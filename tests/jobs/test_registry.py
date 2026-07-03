"""Tests for task registry validation and inspection."""

import pytest
from pydantic import BaseModel

from bonsai_libs.jobs import TaskContext, TaskRegistry
from bonsai_libs.jobs.exceptions import TaskValidationError


class SamplePayload(BaseModel):
    value: str


def test_registry_registers_and_lists_tasks() -> None:
    """Registry can register tasks that accept TaskContext."""
    registry = TaskRegistry()

    @registry.register("echo")
    def echo(value: str, context: TaskContext) -> dict[str, str]:
        return {"value": value}

    assert registry.get("echo") is echo
    assert registry.list() == ["echo"]


def test_registry_rejects_tasks_without_context() -> None:
    """Registry rejects tasks that don't accept context parameter."""
    registry = TaskRegistry()

    with pytest.raises(TaskValidationError, match="context"):

        @registry.register("no_context")
        def no_context(value: str) -> str:
            return value


def test_registry_rejects_duplicate_or_invalid_tasks() -> None:
    """Registry rejects duplicate names and invalid inputs."""
    registry = TaskRegistry()

    @registry.register("sample")
    def sample(context: TaskContext) -> str:
        return "ok"

    with pytest.raises(TaskValidationError, match="already registered"):

        @registry.register("sample")
        def duplicate(context: TaskContext) -> str:
            return "no"

    with pytest.raises(TaskValidationError, match="empty"):
        registry.register("")

    with pytest.raises(TaskValidationError, match="string"):
        registry.register(123)  # type: ignore


def test_registry_accepts_input_schema() -> None:
    """Registry accepts optional input schemas for payload validation."""
    registry = TaskRegistry()

    @registry.register("validate", input_schema=SamplePayload)
    def validate(value: str, context: TaskContext) -> dict[str, str]:
        return {"value": value}

    assert registry.get_input_schema("validate") is SamplePayload


def test_registry_rejects_invalid_schema() -> None:
    """Registry rejects non-Pydantic schemas."""
    registry = TaskRegistry()

    with pytest.raises(TaskValidationError, match="Pydantic model"):

        @registry.register("bad_schema", input_schema=dict)  # type: ignore
        def bad_schema(context: TaskContext) -> None:
            pass


def test_registry_exists_check() -> None:
    """Registry can check whether a task exists."""
    registry = TaskRegistry()

    @registry.register("exists")
    def exists(context: TaskContext) -> None:
        pass

    assert registry.exists("exists")
    assert not registry.exists("missing")
