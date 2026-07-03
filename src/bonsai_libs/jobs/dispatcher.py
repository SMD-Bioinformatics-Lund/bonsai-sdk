"""Job dispatcher for executing registered tasks."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from .exceptions import InvalidJobRequestError, TaskNotFoundError
from .models import ExecutionContext, JobRequest, JobResponse, build_execution_context
from .registry import TaskRegistry
from .logging import LoggerProtocol


@dataclass
class ExecutionHooks:
    """Optional hooks invoked around task execution."""

    logger: LoggerProtocol | None = None
    tracer: Callable[[str, dict[str, Any]], None] | None = None

    before_task: Callable[[ExecutionContext, dict[str, Any]], None] | None = None
    after_task: Callable[[ExecutionContext, dict[str, Any]], None] | None = None
    on_error: Callable[[ExecutionContext, Exception], None] | None = None


def make_json_serializable(obj: Any) -> Any:
    """Convert objects into a JSON-safe structure."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj

    if isinstance(obj, dict):
        return {str(k): make_json_serializable(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        return [make_json_serializable(item) for item in obj]

    if isinstance(obj, BaseModel):
        return make_json_serializable(obj.model_dump(mode="json"))

    if is_dataclass(obj):
        return make_json_serializable(asdict(obj))

    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")

    if isinstance(obj, Mapping):
        return {str(k): make_json_serializable(v) for k, v in obj.items()}

    if hasattr(obj, "__dict__") and not isinstance(obj, type):
        return f"<{obj.__class__.__module__}.{obj.__class__.__name__} object>"

    return str(obj)


def _safe_error_message(exc: Exception) -> str:
    """Return a concise, non-sensitive error message."""
    message = str(exc).strip()
    if not message:
        return exc.__class__.__name__
    if message.startswith("Traceback"):
        return exc.__class__.__name__
    return message


def dispatch_job(
    registry: TaskRegistry,
    request: dict[str, Any] | JobRequest,
    *,
    hooks: ExecutionHooks | None = None,
    context: ExecutionContext | dict[str, Any] | None = None,
) -> JobResponse:
    """Execute a registered task and return a structured JobResponse."""
    start_time = time.perf_counter()
    task_name: str | None = None
    execution_context: ExecutionContext | None = None

    try:
        if isinstance(request, JobRequest):
            job_request = request
        elif isinstance(request, dict):
            job_request = JobRequest.model_validate(request)
        else:
            raise InvalidJobRequestError("request must be a mapping or JobRequest")

        task_name = job_request.task
        execution_context = job_request.context or context
        if execution_context is None:
            execution_context = build_execution_context()
        elif isinstance(execution_context, dict):
            execution_context = ExecutionContext(**execution_context)
        
        # Logging start
        if hooks and hooks.logger:
            hooks.logger.info(
                "task.start",
                task=task_name,
                context=execution_context.model_dump(mode="json"),
            )
        
        # Validate task existence
        if not registry.exists(task_name):
            raise TaskNotFoundError(f"Task '{task_name}' not found in registry")

        task_func = registry.get(task_name)
        input_schema = registry.get_input_schema(task_name)

        payload = job_request.payload
        if input_schema is not None:
            try:
                validated_payload = input_schema.model_validate(payload)
            except ValidationError as exc:
                raise InvalidJobRequestError(
                    f"Invalid payload for task '{task_name}': {exc}"
                ) from exc
            payload = validated_payload.model_dump(mode="json")

        # Execute before_task hook if provided
        if hooks and hooks.before_task:
            hooks.before_task(execution_context, payload)

        # Execute the main task
        result = task_func(**payload, context=execution_context)
        result = make_json_serializable(result)
        json.dumps(result)

        if hooks and hooks.after_task:
            hooks.after_task(execution_context, payload)

        execution_time = time.perf_counter() - start_time
        metadata = {
            "execution_time_seconds": round(execution_time, 6),
            "context": execution_context.model_dump(mode="json"),
        }
        if job_request.metadata:
            metadata["request_metadata"] = job_request.metadata
        
        if hooks and hooks.logger:
            hooks.logger.info(
                "task.success",
                task=task_name,
                duration=metadata["execution_time_seconds"],
            )

        return JobResponse(
            status="success",
            task=task_name,
            result=result,
            error=None,
            metadata=metadata,
        )

    except InvalidJobRequestError as exc:
        execution_time = time.perf_counter() - start_time

        if hooks and hooks.logger:
            hooks.logger.error(
                "task.error",
                task=task_name,
                error_type=type(exc).__name__,
                message=str(exc),
            )


        if hooks is not None and hooks.on_error is not None and execution_context is not None:
            hooks.on_error(execution_context, exc)

        return JobResponse(
            status="error",
            task=task_name or "unknown",
            result=None,
            error=f"Invalid request: {_safe_error_message(exc)}",
            metadata={
                "execution_time_seconds": round(execution_time, 6),
                "error_type": "InvalidJobRequestError",
                "context": execution_context.model_dump(mode="json") if execution_context is not None else None,
            },
        )

    except TaskNotFoundError as exc:
        execution_time = time.perf_counter() - start_time
        if hooks is not None and hooks.on_error is not None and execution_context is not None:
            hooks.on_error(execution_context, exc)
        return JobResponse(
            status="error",
            task=task_name or "unknown",
            result=None,
            error=_safe_error_message(exc),
            metadata={
                "execution_time_seconds": round(execution_time, 6),
                "error_type": "TaskNotFoundError",
                "context": execution_context.model_dump(mode="json") if execution_context is not None else None,
            },
        )

    except Exception as exc:  # pragma: no cover - defensive path
        execution_time = time.perf_counter() - start_time
        if hooks is not None and hooks.on_error is not None and execution_context is not None:
            hooks.on_error(execution_context, exc)
        return JobResponse(
            status="error",
            task=task_name or "unknown",
            result=None,
            error=_safe_error_message(exc),
            metadata={
                "execution_time_seconds": round(execution_time, 6),
                "error_type": type(exc).__name__,
                "context": execution_context.model_dump(mode="json") if execution_context is not None else None,
            },
        )
