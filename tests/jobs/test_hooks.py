"""Tests for execution hooks and logging protocol."""

from typing import Any

from bonsai_libs.jobs import (
    ExecutionContext,
    ExecutionHooks,
    TaskContext,
    TaskRegistry,
    StandardLogger,
    build_execution_context,
    dispatch_job,
)


class MockLogger:
    """Mock logger for testing."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, dict[str, Any]]] = []

    def debug(self, message: str, **kwargs: Any) -> None:
        self.messages.append(("debug", {"message": message, **kwargs}))

    def info(self, message: str, **kwargs: Any) -> None:
        self.messages.append(("info", {"message": message, **kwargs}))

    def warning(self, message: str, **kwargs: Any) -> None:
        self.messages.append(("warning", {"message": message, **kwargs}))

    def error(self, message: str, **kwargs: Any) -> None:
        self.messages.append(("error", {"message": message, **kwargs}))

def test_execution_hooks_with_logging() -> None:
    """Dispatcher invokes before/after hooks with logger available."""
    registry = TaskRegistry()
    logger = StandardLogger("test")
    hook_calls: list[str] = []

    @registry.register("echo")
    def echo(value: str, context: TaskContext) -> dict[str, str]:
        return {"value": value}

    def before_task(context: TaskContext, payload: dict[str, Any]) -> None:
        hook_calls.append("before")
        # Logger is available in context
        assert context.logger is not None

    def after_task(context: TaskContext, payload: dict[str, Any]) -> None:
        hook_calls.append("after")

    hooks = ExecutionHooks(before_task=before_task, after_task=after_task)
    response = dispatch_job(
        registry,
        {"task": "echo", "payload": {"value": "ok"}},
        hooks=hooks,
        logger=logger,
    )

    assert response.status == "success"
    assert hook_calls == ["before", "after"]

def test_execution_hooks_before_and_after_task() -> None:
    """Dispatcher invokes before_task and after_task hooks."""
    registry = TaskRegistry()
    hook_calls: list[str] = []

    @registry.register("echo")
    def echo(value: str, context: TaskContext) -> dict[str, str]:
        hook_calls.append("task_executed")
        return {"value": value}

    def before_task(context: TaskContext, payload: dict[str, Any]) -> None:
        hook_calls.append("before")

    def after_task(context: TaskContext, payload: dict[str, Any]) -> None:
        hook_calls.append("after")

    hooks = ExecutionHooks(before_task=before_task, after_task=after_task)
    response = dispatch_job(
        registry,
        {"task": "echo", "payload": {"value": "ok"}},
        hooks=hooks,
    )

    assert response.status == "success"
    assert hook_calls == ["before", "task_executed", "after"]


def test_execution_hooks_on_error() -> None:
    """Dispatcher invokes on_error hook on task failure."""
    registry = TaskRegistry()
    errors_caught: list[Exception] = []

    @registry.register("failing")
    def failing(context: TaskContext) -> None:
        raise ValueError("Intentional failure")

    def on_error(context: TaskContext, exc: Exception) -> None:
        errors_caught.append(exc)

    hooks = ExecutionHooks(on_error=on_error)
    response = dispatch_job(
        registry,
        {"task": "failing", "payload": {}},
        hooks=hooks,
    )

    assert response.status == "error"
    assert len(errors_caught) == 1
    assert isinstance(errors_caught[0], ValueError)


def test_execution_context_in_hooks() -> None:
    """Execution context is available in before/after hooks."""
    registry = TaskRegistry()
    captured_contexts: list[TaskContext] = []

    @registry.register("echo")
    def echo(context: TaskContext) -> dict[str, object]:
        return {"ok": True}

    def before_task(context: TaskContext, payload: dict[str, Any]) -> None:
        captured_contexts.append(context)

    context = build_execution_context(
        request_id="req-123", trace_id="trace-456", service="test-service"
    )
    hooks = ExecutionHooks(before_task=before_task)
    dispatch_job(
        registry,
        {"task": "echo", "payload": {}, "context": context.model_dump()},
        hooks=hooks,
    )

    assert len(captured_contexts) == 1
    assert captured_contexts[0].execution.request_id == "req-123"
    assert captured_contexts[0].execution.trace_id == "trace-456"
    assert captured_contexts[0].execution.service == "test-service"
