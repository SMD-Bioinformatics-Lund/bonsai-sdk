"""Task registry for job execution framework."""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel

from .exceptions import TaskNotFoundError, TaskValidationError


class TaskRegistry:
    """Registry for managing callable task definitions.

    Tasks must be explicitly registered before they can be executed.
    """

    def __init__(self) -> None:
        """Initialize an empty task registry."""

        # tasks are stored as a mapping with task name as key and a tuple as value
        # the tuple contains the callable function and a optionaly Pydantic input schema for payload validation
        self._tasks: dict[str, tuple[Callable[..., Any], type[BaseModel] | None]] = {}

    def register(
        self,
        task_name: str,
        *,
        input_schema: type[BaseModel] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a callable task using a decorator.

        Args:
            task_name: Unique name for the task.
            input_schema: Optional Pydantic schema used to validate payloads.

        Returns:
            Decorator function.

        Raises:
            TaskValidationError: If the task name is invalid or already registered.
        """
        self._validate_task_name(task_name)

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            if task_name in self._tasks:
                raise TaskValidationError(f"Task '{task_name}' is already registered")
            if not callable(func):
                raise TaskValidationError(f"Task '{task_name}' must be callable")
            if input_schema is not None and not (
                isinstance(input_schema, type) and issubclass(input_schema, BaseModel)
            ):
                raise TaskValidationError(
                    f"Task '{task_name}' input schema must be a Pydantic model"
                )

            self._tasks[task_name] = (func, input_schema)
            return func

        return decorator

    def get(self, task_name: str) -> Callable[..., Any]:
        """Retrieve a registered task callable."""
        if task_name not in self._tasks:
            raise TaskNotFoundError(f"Task '{task_name}' not found in registry")
        return self._tasks[task_name][0]

    def get_input_schema(self, task_name: str) -> type[BaseModel] | None:
        """Return the optional input schema associated with a task."""
        if task_name not in self._tasks:
            raise TaskNotFoundError(f"Task '{task_name}' not found in registry")
        return self._tasks[task_name][1]

    def list(self) -> list[str]:
        """List all registered task names in sorted order."""
        return sorted(self._tasks.keys())

    def exists(self, task_name: str) -> bool:
        """Check whether a task name is already registered."""
        return task_name in self._tasks

    @staticmethod
    def _validate_task_name(task_name: str) -> None:
        """Validate task name format."""
        if not isinstance(task_name, str):
            raise TaskValidationError("Task name must be a string")
        if not task_name.strip():
            raise TaskValidationError("Task name cannot be empty")
        if len(task_name) > 255:
            raise TaskValidationError("Task name too long (max 255 chars)")
