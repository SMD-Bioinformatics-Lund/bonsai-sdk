"""Tests for job dispatcher execution and context passing."""

import pytest
from pydantic import BaseModel

from bonsai_libs.jobs import (
    TaskContext,
    JobRequest,
    JobResponse,
    TaskRegistry,
    build_execution_context,
    dispatch_job,
)
from bonsai_libs.jobs.exceptions import TaskNotFoundError


class ExamplePayload(BaseModel):
    value: str


def test_dispatch_job_returns_structured_success_response() -> None:
    """Dispatcher executes task and returns structured response."""
    registry = TaskRegistry()

    @registry.register("echo")
    def echo(value: str, context: TaskContext) -> dict[str, str]:
        return {"value": value, "request_id": context.execution.request_id or "none"}

    response = dispatch_job(
        registry, {"task": "echo", "payload": {"value": "ok"}}
    )

    assert isinstance(response, JobResponse)
    assert response.status == "success"
    assert response.result["value"] == "ok"
    assert response.error is None
    assert response.metadata["execution_time_seconds"] >= 0
    assert response.metadata["context"] is not None


def test_dispatch_job_passes_context_to_task() -> None:
    """Dispatcher passes task context to task."""
    registry = TaskRegistry()

    @registry.register("echo_context")
    def echo_context(context: TaskContext) -> dict[str, object]:
        return {
            "request_id": context.execution.request_id,
            "trace_id": context.execution.trace_id,
            "service": context.execution.service,
        }

    context = build_execution_context(
        request_id="req-1", trace_id="trace-1", service="test"
    )
    response = dispatch_job(
        registry,
        {"task": "echo_context", "payload": {}, "context": context.model_dump()},
    )

    assert response.status == "success"
    assert response.result["request_id"] == "req-1"
    assert response.result["trace_id"] == "trace-1"
    assert response.result["service"] == "test"


def test_dispatch_job_handles_missing_tasks() -> None:
    """Dispatcher returns error for missing tasks."""
    registry = TaskRegistry()

    response = dispatch_job(registry, {"task": "missing", "payload": {}})

    assert response.status == "error"
    assert response.result is None
    assert "not found" in response.error.lower()
    assert response.metadata["error_type"] == "TaskNotFoundError"


def test_dispatch_job_handles_non_serializable_results() -> None:
    """Dispatcher converts non-serializable objects to strings."""
    registry = TaskRegistry()

    @registry.register("custom_object")
    def custom_object(context: TaskContext) -> object:
        return type("Thing", (), {"value": "test"})()

    response = dispatch_job(registry, {"task": "custom_object", "payload": {}})

    assert response.status == "success"
    assert isinstance(response.result, str)
    assert "Thing" in response.result


def test_dispatch_job_validates_input_schema() -> None:
    """Dispatcher validates payloads against input schema."""
    registry = TaskRegistry()

    @registry.register("validate", input_schema=ExamplePayload)
    def validate(value: str, context: TaskContext) -> dict[str, str]:
        return {"value": value}

    # Invalid payload (missing required field)
    response = dispatch_job(
        registry, {"task": "validate", "payload": {"wrong_field": "test"}}
    )
    assert response.status == "error"
    assert "Invalid request" in response.error
    assert response.metadata["error_type"] == "InvalidJobRequestError"


def test_dispatch_job_handles_task_exceptions() -> None:
    """Dispatcher catches task exceptions and returns error response."""
    registry = TaskRegistry()

    @registry.register("failing")
    def failing(context: TaskContext) -> None:
        raise ValueError("Task failed intentionally")
    response = dispatch_job(registry, {"task": "failing", "payload": {}})

    assert response.status == "error"
    assert response.result is None
    assert "ValueError" in response.error or "Task failed" in response.error
    assert response.metadata["error_type"] == "ValueError"
