"""Job dispatcher for executing registered tasks."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from .exceptions import InvalidJobRequestError, TaskNotFoundError
from .models import JobRequest, JobResponse
from .registry import TaskRegistry


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
) -> JobResponse:
    """Execute a registered task and return a structured JobResponse."""
    start_time = time.perf_counter()
    task_name: str | None = None

    try:
        if isinstance(request, JobRequest):
            job_request = request
        elif isinstance(request, dict):
            job_request = JobRequest.model_validate(request)
        else:
            raise InvalidJobRequestError("request must be a mapping or JobRequest")

        task_name = job_request.task

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

        result = task_func(**payload)
        result = make_json_serializable(result)
        json.dumps(result)

        execution_time = time.perf_counter() - start_time
        return JobResponse(
            status="success",
            task=task_name,
            result=result,
            error=None,
            metadata={"execution_time_seconds": round(execution_time, 6)},
        )

    except InvalidJobRequestError as exc:
        execution_time = time.perf_counter() - start_time
        return JobResponse(
            status="error",
            task=task_name or "unknown",
            result=None,
            error=f"Invalid request: {_safe_error_message(exc)}",
            metadata={
                "execution_time_seconds": round(execution_time, 6),
                "error_type": "InvalidJobRequestError",
            },
        )

    except TaskNotFoundError as exc:
        execution_time = time.perf_counter() - start_time
        return JobResponse(
            status="error",
            task=task_name or "unknown",
            result=None,
            error=_safe_error_message(exc),
            metadata={
                "execution_time_seconds": round(execution_time, 6),
                "error_type": "TaskNotFoundError",
            },
        )

    except Exception as exc:  # pragma: no cover - defensive path
        execution_time = time.perf_counter() - start_time
        return JobResponse(
            status="error",
            task=task_name or "unknown",
            result=None,
            error=_safe_error_message(exc),
            metadata={
                "execution_time_seconds": round(execution_time, 6),
                "error_type": type(exc).__name__,
            },
        )
