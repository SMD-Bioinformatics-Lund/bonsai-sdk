"""Secure worker implementation for registered job execution."""

from __future__ import annotations

from typing import Any

from .exceptions import UnauthorizedJobExecutionError
from .registry import TaskRegistry

try:
    from rq.worker import SimpleWorker
except ImportError:  # pragma: no cover - optional dependency
    SimpleWorker = object  # type: ignore[misc,assignment]


class SecureWorker(SimpleWorker):
    """Restrict execution to explicitly allowed task entrypoints."""

    def __init__(self, *args: Any, registry: TaskRegistry | None = None, **kwargs: Any) -> None:
        self._registry = registry
        self._allowed_entrypoints: set[str] = set()
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
