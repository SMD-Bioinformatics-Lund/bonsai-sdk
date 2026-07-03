"""Tests for TaskContext and task context passing."""

from typing import Any

from bonsai_libs.jobs import (
    ExecutionContext,
    ExecutionHooks,
    JobResponse,
    StandardLogger,
    TaskContext,
    TaskRegistry,
    SimpleTracer,
    build_execution_context,
    dispatch_job,
)


def test_task_context_creation() -> None:
    """TaskContext can be created with execution data and tools."""
    execution = build_execution_context(request_id="req-1", trace_id="trace-1")
    logger = StandardLogger("test")
    tracer = SimpleTracer(logger=logger)

    context = TaskContext(execution=execution, logger=logger, tracer=tracer)

    assert context.execution.request_id == "req-1"
    assert context.logger is logger
    assert context.tracer is tracer


def test_task_receives_task_context() -> None:
    """Task functions receive TaskContext parameter."""
    registry = TaskRegistry()
    received_contexts: list[TaskContext] = []

    @registry.register("capture_context")
    def capture_context(context: TaskContext) -> dict[str, Any]:
        received_contexts.append(context)
        return {
            "request_id": context.execution.request_id,
            "trace_id": context.execution.trace_id,
            "has_logger": context.logger is not None,
            "has_tracer": context.tracer is not None,
        }

    logger = StandardLogger("test")
    response = dispatch_job(
        registry,
        {"task": "capture_context", "payload": {}},
        logger=logger,
    )

    assert response.status == "success"
    assert len(received_contexts) == 1
    assert received_contexts[0].logger is logger
    assert received_contexts[0].tracer is not None  # SimpleTracer was created


def test_task_can_use_logger_from_context() -> None:
    """Tasks can log using the logger from TaskContext."""
    registry = TaskRegistry()
    logger = StandardLogger("test")
    log_messages: list[tuple[str, dict[str, Any]]] = []

    # Monkey-patch logger to capture calls
    original_debug = logger.debug

    def capture_debug(message: str, **kwargs: Any) -> None:
        log_messages.append(("debug", {"message": message, **kwargs}))
        return original_debug(message, **kwargs)

    logger.debug = capture_debug  # type: ignore

    @registry.register("log_from_task")
    def log_from_task(context: TaskContext) -> dict[str, str]:
        if context.logger:
            context.logger.debug("task_event", task_id="123")
        return {"logged": True}

    response = dispatch_job(
        registry,
        {"task": "log_from_task", "payload": {}},
        logger=logger,
    )

    assert response.status == "success"
    # Should have task.start, task_event, and task.success messages
    assert any(msg[0] == "debug" for msg in log_messages)
    assert any("task_event" in str(msg) for msg in log_messages)


def test_task_can_use_tracer_from_context() -> None:
    """Tasks can create spans using the tracer from TaskContext."""
    registry = TaskRegistry()
    logger = StandardLogger("test")
    traced_spans: list[str] = []

    # Monkey-patch to capture span operations
    original_debug = logger.debug

    def capture_span(message: str, **kwargs: Any) -> None:
        if message.startswith("span."):
            traced_spans.append(message)
        return original_debug(message, **kwargs)

    logger.debug = capture_span  # type: ignore

    @registry.register("use_tracer")
    def use_tracer(context: TaskContext) -> dict[str, int]:
        if context.tracer:
            with context.tracer.start_span("process"):
                count = 5
        return {"count": count}

    response = dispatch_job(
        registry,
        {"task": "use_tracer", "payload": {}},
        logger=logger,
    )

    assert response.status == "success"
    assert "span.start" in traced_spans
    assert "span.end" in traced_spans


def test_dispatch_creates_tracer_if_logger_provided() -> None:
    """Dispatcher automatically creates SimpleTracer if logger is provided."""
    registry = TaskRegistry()

    @registry.register("check_tracer")
    def check_tracer(context: TaskContext) -> dict[str, Any]:
        return {
            "has_tracer": context.tracer is not None,
            "tracer_type": type(context.tracer).__name__ if context.tracer else None,
        }

    logger = StandardLogger("test")
    response = dispatch_job(
        registry,
        {"task": "check_tracer", "payload": {}},
        logger=logger,
    )

    assert response.status == "success"
    assert response.result["has_tracer"] is True
    assert response.result["tracer_type"] == "SimpleTracer"


def test_task_context_in_lifecycle_hooks() -> None:
    """Lifecycle hooks receive TaskContext instead of ExecutionContext."""
    registry = TaskRegistry()
    hook_calls: list[str] = []

    @registry.register("hooked")
    def hooked(context: TaskContext) -> dict[str, str]:
        return {"ok": True}

    def before_task(context: TaskContext, payload: dict[str, Any]) -> None:
        hook_calls.append("before")
        assert isinstance(context, TaskContext)
        assert context.execution is not None

    def after_task(context: TaskContext, payload: dict[str, Any]) -> None:
        hook_calls.append("after")
        assert isinstance(context, TaskContext)

    def on_error(context: TaskContext, exc: Exception) -> None:
        hook_calls.append("error")

    hooks = ExecutionHooks(
        before_task=before_task,
        after_task=after_task,
        on_error=on_error,
    )
    response = dispatch_job(
        registry,
        {"task": "hooked", "payload": {}},
        hooks=hooks,
    )

    assert response.status == "success"
    assert hook_calls == ["before", "after"]


def test_task_context_in_error_handling() -> None:
    """Error hook receives TaskContext on failure."""
    registry = TaskRegistry()
    error_contexts: list[TaskContext] = []

    @registry.register("failing")
    def failing(context: TaskContext) -> None:
        raise ValueError("Intentional failure")

    def on_error(context: TaskContext, exc: Exception) -> None:
        error_contexts.append(context)

    hooks = ExecutionHooks(on_error=on_error)
    logger = StandardLogger("test")
    response = dispatch_job(
        registry,
        {"task": "failing", "payload": {}},
        hooks=hooks,
        logger=logger,
    )

    assert response.status == "error"
    assert len(error_contexts) == 1
    assert error_contexts[0].logger is logger


def test_task_context_attributes() -> None:
    """TaskContext provides access to execution data and tools."""
    registry = TaskRegistry()

    @registry.register("inspect_context")
    def inspect_context(context: TaskContext) -> dict[str, Any]:
        return {
            "request_id": context.execution.request_id,
            "trace_id": context.execution.trace_id,
            "service": context.execution.service,
            "attempt": context.execution.attempt,
            "logger_type": type(context.logger).__name__ if context.logger else None,
            "tracer_type": type(context.tracer).__name__ if context.tracer else None,
        }

    logger = StandardLogger("test")
    exec_ctx = build_execution_context(
        request_id="req-123",
        trace_id="trace-456",
        service="my-service",
        attempt=2,
    )
    response = dispatch_job(
        registry,
        {
            "task": "inspect_context",
            "payload": {},
            "context": exec_ctx.model_dump(),
        },
        logger=logger,
    )

    assert response.status == "success"
    assert response.result["request_id"] == "req-123"
    assert response.result["trace_id"] == "trace-456"
    assert response.result["service"] == "my-service"
    assert response.result["attempt"] == 2
    assert response.result["logger_type"] == "StandardLogger"
    assert response.result["tracer_type"] == "SimpleTracer"
