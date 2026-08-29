"""Tests for tracing and span lifecycle events."""

from typing import Any

from bonsai_libs.jobs import SimpleTracer, StandardLogger
from bonsai_libs.jobs.exceptions import JobExecutionError


class CaptureLogger:
    """Logger that captures all messages for testing."""

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


def test_simple_tracer_emits_span_start_event() -> None:
    """SimpleTracer logs span.start event when entering context."""
    logger = CaptureLogger()
    tracer = SimpleTracer(logger=logger)

    with tracer.start_span("process_item", item_id="123"):
        pass

    debug_messages = [m for m in logger.messages if m[0] == "debug"]
    assert any(m[1]["message"] == "span.start" for m in debug_messages)
    assert any(m[1].get("span") == "process_item" for m in debug_messages)
    assert any(m[1].get("item_id") == "123" for m in debug_messages)


def test_simple_tracer_emits_span_end_event() -> None:
    """SimpleTracer logs span.end event when exiting context."""
    logger = CaptureLogger()
    tracer = SimpleTracer(logger=logger)

    with tracer.start_span("query_db"):
        pass

    debug_messages = [m for m in logger.messages if m[0] == "debug"]
    end_messages = [m for m in debug_messages if m[1]["message"] == "span.end"]
    assert len(end_messages) == 1
    assert end_messages[0][1]["span"] == "query_db"
    assert "duration_seconds" in end_messages[0][1]


def test_simple_tracer_duration_is_accurate() -> None:
    """SimpleTracer measures span duration accurately."""
    import time

    logger = CaptureLogger()
    tracer = SimpleTracer(logger=logger)

    with tracer.start_span("sleep_span"):
        time.sleep(0.05)

    debug_messages = [m for m in logger.messages if m[0] == "debug"]
    end_messages = [m for m in debug_messages if m[1]["message"] == "span.end"]
    assert len(end_messages) == 1

    duration = end_messages[0][1]["duration_seconds"]
    # Should be approximately 0.05, allowing for some variance
    assert 0.04 < duration < 0.1


def test_simple_tracer_emits_span_error_event() -> None:
    """SimpleTracer logs span.error event when exception occurs."""
    logger = CaptureLogger()
    tracer = SimpleTracer(logger=logger)

    try:
        with tracer.start_span("failing_operation"):
            raise ValueError("Operation failed")
    except ValueError:
        pass

    error_messages = [m for m in logger.messages if m[0] == "error"]
    assert len(error_messages) == 1
    assert error_messages[0][1]["message"] == "span.error"
    assert error_messages[0][1]["span"] == "failing_operation"
    assert error_messages[0][1]["error_type"] == "ValueError"
    assert error_messages[0][1]["error_message"] == "Operation failed"


def test_simple_tracer_error_event_has_duration() -> None:
    """SimpleTracer includes duration in error event."""
    import time

    logger = CaptureLogger()
    tracer = SimpleTracer(logger=logger)

    try:
        with tracer.start_span("timing_error"):
            time.sleep(0.02)
            raise RuntimeError("Timed out")
    except RuntimeError:
        pass

    error_messages = [m for m in logger.messages if m[0] == "error"]
    assert len(error_messages) == 1
    assert "duration_seconds" in error_messages[0][1]
    duration = error_messages[0][1]["duration_seconds"]
    assert 0.01 < duration < 0.1


def test_simple_tracer_with_no_logger() -> None:
    """SimpleTracer works without logger (no-op)."""
    tracer = SimpleTracer(logger=None)

    # Should not raise
    with tracer.start_span("no_log_span"):
        pass


def test_simple_tracer_exception_propagates() -> None:
    """SimpleTracer re-raises exceptions after logging."""
    logger = CaptureLogger()
    tracer = SimpleTracer(logger=logger)

    raised_exception = None
    try:
        with tracer.start_span("failing"):
            raise KeyError("Not found")
    except KeyError as exc:
        raised_exception = exc

    assert raised_exception is not None
    assert str(raised_exception) == "'Not found'"


def test_simple_tracer_metadata_passed_through() -> None:
    """SimpleTracer includes metadata in span events."""
    logger = CaptureLogger()
    tracer = SimpleTracer(logger=logger)

    with tracer.start_span(
        "operation",
        user_id="user-456",
        region="us-west-2",
        retry_count=3,
    ):
        pass

    debug_messages = [m for m in logger.messages if m[0] == "debug"]

    # Metadata should be in both start and end events
    start_events = [m for m in debug_messages if m[1]["message"] == "span.start"]
    end_events = [m for m in debug_messages if m[1]["message"] == "span.end"]

    for event in start_events + end_events:
        assert event[1].get("user_id") == "user-456"
        assert event[1].get("region") == "us-west-2"
        assert event[1].get("retry_count") == 3


def test_simple_tracer_nested_spans() -> None:
    """SimpleTracer can create nested spans."""
    logger = CaptureLogger()
    tracer = SimpleTracer(logger=logger)

    with tracer.start_span("outer"):
        with tracer.start_span("inner"):
            pass

    debug_messages = [m for m in logger.messages if m[0] == "debug"]
    spans = [m[1]["span"] for m in debug_messages if "span" in m[1]]

    # Should see outer start, inner start, inner end, outer end
    assert spans.count("outer") >= 1
    assert spans.count("inner") >= 1


def test_standard_logger_with_simple_tracer() -> None:
    """StandardLogger works with SimpleTracer."""
    logger = StandardLogger("test")
    tracer = SimpleTracer(logger=logger)

    # Should not raise
    with tracer.start_span("integration_test"):
        pass
