"""Secure worker implementation for registered job execution."""

from __future__ import annotations

from typing import Any

from .exceptions import UnauthorizedJobExecutionError
from .registry import TaskRegistry

try:
    from rq.worker import SimpleWorker
except ImportError:  # pragma: no cover - optional dependency
    SimpleWorker = object  # type: ignore[misc,assignment]


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


def build_worker_config(*, queues: list[Any] | None = None, connection: Any | None = None, name: str | None = None, **kwargs: Any) -> dict[str, Any]:
    """Build a configuration dictionary for creating an RQ worker."""
    config: dict[str, Any] = {}
    if queues is not None:
        config["queues"] = queues
    if connection is not None:
        config["connection"] = connection
    if name is not None:
        config["name"] = name
    config.update(kwargs)
    return config


def configure_worker(*, queues: list[Any] | None = None, connection: Any | None = None, name: str | None = None, registry: TaskRegistry | None = None, allowed_entrypoints: list[str] | None = None, **kwargs: Any) -> Any:
    """Create a worker using the supplied configuration."""
    try:
        from rq import Worker
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("rq must be installed to configure workers") from exc

    config = build_worker_config(queues=queues, connection=connection, name=name, **kwargs)
    if registry is not None or allowed_entrypoints is not None:
        worker = SecureWorker(registry=registry, **config)
        if allowed_entrypoints is not None:
            for entrypoint in allowed_entrypoints:
                worker.allow_entrypoint(entrypoint)
        return worker
    return Worker(**config)


class SecureWorker(SimpleWorker):
    """Restrict execution to explicitly allowed task entrypoints."""

    def __init__(self, *args: Any, registry: TaskRegistry | None = None, **kwargs: Any) -> None:
        self._registry = registry
        self._allowed_entrypoints: set[str] = set()
        if SimpleWorker is object:
            raise RuntimeError("rq must be installed to create a SecureWorker")
        super().__init__(*args, **kwargs)

    def allow_entrypoint(self, task_name: str) -> None:
        """Allow a task name to be executed by this worker."""
        if self._registry is not None and not self._registry.exists(task_name):
            raise UnauthorizedJobExecutionError(
                f"Task '{task_name}' is not registered and cannot be whitelisted"
            )
        self._allowed_entrypoints.add(task_name)

    def _is_entrypoint_allowed(self, func_name: str | None) -> bool:
        """Return whether the named entrypoint is explicitly whitelisted."""
        if func_name is None:
            return False
        return func_name in self._allowed_entrypoints

    def execute_job(self, job: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute a job only if its entrypoint is explicitly allowed."""
        func_name = getattr(job, "func_name", None)
        if not self._is_entrypoint_allowed(func_name):
            raise UnauthorizedJobExecutionError(
                f"Job execution is not permitted for entrypoint '{func_name}'"
            )
        return super().execute_job(job, *args, **kwargs)
