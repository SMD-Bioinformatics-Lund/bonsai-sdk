"""Job dispatcher for executing registered tasks."""

import json
import time
from typing import Any

from .exceptions import InvalidJobRequestError, TaskNotFoundError
from .models import JobRequest, JobResponse
from .registry import TaskRegistry


def make_json_serializable(obj: Any) -> Any:
    """Convert object to JSON-serializable form.

    Recursively processes objects to ensure JSON compatibility:
    - dict, list, str, int, float, bool, None → unchanged
    - Other objects → converted to string

    Args:
        obj: Object to convert.

    Returns:
        JSON-serializable equivalent.
    """
    # Handle primitive types
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj

    # Handle dict
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}

    # Handle list/tuple
    if isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]

    # Handle Pydantic models
    if hasattr(obj, "model_dump"):
        return make_json_serializable(obj.model_dump())

    # Handle dataclasses
    if hasattr(obj, "__dataclass_fields__"):
        return make_json_serializable(obj.__dict__)

    # Fallback: convert to string
    return str(obj)


def dispatch_job(
    registry: TaskRegistry,
    request: dict[str, Any] | JobRequest,
) -> JobResponse:
    """Execute a job and return structured response.

    This is the main entry point for job execution. It:
    1. Validates the request
    2. Resolves the task from the registry
    3. Executes the task safely
    4. Captures all exceptions
    5. Ensures JSON-serializable output
    6. Returns structured response

    Args:
        registry: TaskRegistry instance containing registered tasks.
        request: JobRequest dict or instance with 'task' and 'payload'.

    Returns:
        JobResponse with execution result or error.

    Example:
        registry = TaskRegistry()

        @registry.register("greet")
        def greet(name: str) -> dict:
            return {"message": f"Hello, {name}!"}

        response = dispatch_job(registry, {
            "task": "greet",
            "payload": {"name": "Alice"}
        })

        assert response.status == "success"
        assert response.result["message"] == "Hello, Alice!"
    """
    start_time = time.time()
    task_name = None

    try:
        # Step 1: Validate request
        if isinstance(request, dict):
            job_request = JobRequest(**request)
        else:
            job_request = request

        task_name = job_request.task

        # Step 2: Resolve task
        if not registry.exists(task_name):
            raise TaskNotFoundError(
                f"Task '{task_name}' not found in registry"
            )

        task_func = registry.get(task_name)

        # Step 3: Execute task
        result = task_func(**job_request.payload)

        # Step 4: Ensure JSON serializable
        result = make_json_serializable(result)

        # Step 5: Validate JSON serializability
        try:
            json.dumps(result)
        except (TypeError, ValueError) as e:
            # Fallback if JSON serialization still fails
            result = str(result)

        execution_time = time.time() - start_time

        return JobResponse(
            status="success",
            task=task_name,
            result=result,
            error=None,
            metadata={
                "execution_time_seconds": execution_time,
            },
        )

    except InvalidJobRequestError as e:
        execution_time = time.time() - start_time
        return JobResponse(
            status="error",
            task=task_name or "unknown",
            result=None,
            error=f"Invalid request: {str(e)}",
            metadata={
                "execution_time_seconds": execution_time,
                "error_type": "InvalidJobRequestError",
            },
        )

    except TaskNotFoundError as e:
        execution_time = time.time() - start_time
        return JobResponse(
            status="error",
            task=task_name or "unknown",
            result=None,
            error=str(e),
            metadata={
                "execution_time_seconds": execution_time,
                "error_type": "TaskNotFoundError",
            },
        )

    except Exception as e:
        # Catch all other exceptions safely
        execution_time = time.time() - start_time
        error_msg = f"{type(e).__name__}: {str(e)}"

        return JobResponse(
            status="error",
            task=task_name or "unknown",
            result=None,
            error=error_msg,
            metadata={
                "execution_time_seconds": execution_time,
                "error_type": type(e).__name__,
            },
        )
