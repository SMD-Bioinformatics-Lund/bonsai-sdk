from typing import Any

from .models import build_execution_context, ExecutionContext, JobRequest

def build_queue_config(*, name: str = "default", connection: Any | None = None, serializer: Any | None = None, **kwargs: Any) -> dict[str, Any]:
    """Build a configuration dictionary for creating an RQ queue."""
    config: dict[str, Any] = {"name": name}
    if connection is not None:
        config["connection"] = connection
    if serializer is not None:
        config["serializer"] = serializer
    config.update(kwargs)
    return config


def configure_queue(*, name: str = "default", connection: Any | None = None, serializer: Any | None = None, **kwargs: Any) -> Any:
    """Create an RQ queue using the supplied configuration."""
    try:
        from rq import Queue
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("rq must be installed to configure queues") from exc

    return Queue(**build_queue_config(name=name, connection=connection, serializer=serializer, **kwargs))


def schedule_job(
    queue: Any,
    *,
    entrypoint: str,
    task: str,
    payload: dict[str, Any],
    context: ExecutionContext | dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    **enqueue_kwargs: Any
) -> Any:
    """
    Build a JobRequest and enqueue it to the given worker entrypoint.
    
    Parameters
    ----------
    queue:
        An RQ queue instance.
    entrypoint:
        Import path to the worker entrypoint function, e.g.
        'minhash_service.worker_entrypoint.execute_service_task'.
    task:
        Registered task name inside the microservice registry.
    payload:
        Task payload.
    context:
        Optional execution context. If omitted, a default context is created.
    metadata:
        Optional metadata attached to the request.
    enqueue_kwargs:
        Extra keyword arguments forwarded to `queue.enqueue`, such as
        `job_timeout`, `result_ttl`, `failure_ttl`, `retry`, etc.
    """
    if context is None:
        execution_context = build_execution_context()
    elif isinstance(context, dict):
        execution_context = ExecutionContext.model_validate(context)
    else:
        execution_context = context
    
    request = JobRequest(
        task=task,
        payload=payload,
        context=execution_context,
        metadata=metadata or {},
    )

    return queue.enqueue(entrypoint, request.model_dump(mode="json"), **enqueue_kwargs)