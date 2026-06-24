"""Task registry for job execution framework."""

from typing import Any, Callable

from .exceptions import TaskNotFoundError, TaskValidationError


class TaskRegistry:
    """Registry for managing task definitions.

    A lightweight registry that stores and manages callable task definitions.
    Tasks must be explicitly registered before they can be executed.

    Example:
        registry = TaskRegistry()

        @registry.register("my_task")
        def my_task(x: int) -> int:
            return x * 2

        task_fn = registry.get("my_task")
        result = task_fn(x=5)
    """

    def __init__(self) -> None:
        """Initialize empty task registry."""
        self._tasks: dict[str, Callable[..., Any]] = {}

    def register(self, task_name: str) -> Callable:
        """Decorator to register a task.

        Args:
            task_name: Unique name for the task.

        Returns:
            Decorator function.

        Raises:
            TaskValidationError: If task name is invalid or already registered.
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._validate_task_name(task_name)
            if task_name in self._tasks:
                raise TaskValidationError(
                    f"Task '{task_name}' is already registered"
                )
            if not callable(func):
                raise TaskValidationError(
                    f"Task '{task_name}' must be callable"
                )

            self._tasks[task_name] = func
            return func

        return decorator

    def get(self, task_name: str) -> Callable[..., Any]:
        """Retrieve a registered task.

        Args:
            task_name: Name of the task.

        Returns:
            The callable task function.

        Raises:
            TaskNotFoundError: If task is not registered.
        """
        if task_name not in self._tasks:
            raise TaskNotFoundError(
                f"Task '{task_name}' not found in registry"
            )
        return self._tasks[task_name]

    def list(self) -> list[str]:
        """List all registered task names.

        Returns:
            Sorted list of registered task names.
        """
        return sorted(self._tasks.keys())

    def exists(self, task_name: str) -> bool:
        """Check if a task is registered.

        Args:
            task_name: Name of the task.

        Returns:
            True if registered, False otherwise.
        """
        return task_name in self._tasks

    @staticmethod
    def _validate_task_name(task_name: str) -> None:
        """Validate task name format.

        Args:
            task_name: Name to validate.

        Raises:
            TaskValidationError: If name is invalid.
        """
        if not task_name:
            raise TaskValidationError("Task name cannot be empty")
        if not isinstance(task_name, str):
            raise TaskValidationError("Task name must be a string")
        if not task_name.strip():
            raise TaskValidationError("Task name cannot be whitespace-only")
        if len(task_name) > 255:
            raise TaskValidationError("Task name too long (max 255 chars)")
