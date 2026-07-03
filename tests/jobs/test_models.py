"""Tests for models and execution context."""

from bonsai_libs.jobs import ExecutionContext, JobRequest, JobResponse, build_execution_context


def test_build_execution_context_defaults() -> None:
    """build_execution_context creates context with defaults."""
    context = build_execution_context()

    assert context.request_id is None
    assert context.trace_id is None
    assert context.span_id is None
    assert context.service is None
    assert context.attempt == 1
    assert isinstance(context.timestamp, str)
    assert context.metadata == {}


def test_build_execution_context_with_values() -> None:
    """build_execution_context accepts custom values."""
    context = build_execution_context(
        request_id="req-1",
        trace_id="trace-1",
        span_id="span-1",
        service="my-service",
        attempt=2,
        metadata={"user": "alice"},
    )

    assert context.request_id == "req-1"
    assert context.trace_id == "trace-1"
    assert context.span_id == "span-1"
    assert context.service == "my-service"
    assert context.attempt == 2
    assert context.metadata["user"] == "alice"


def test_job_request_normalizes_context() -> None:
    """JobRequest normalizes context from dict or instance."""
    context_dict = {
        "request_id": "req-1",
        "trace_id": "trace-1",
        "service": "test",
    }
    request = JobRequest(
        task="echo", payload={"value": "test"}, context=context_dict
    )

    assert isinstance(request.context, ExecutionContext)
    assert request.context.request_id == "req-1"


def test_job_response_consistency_validation() -> None:
    """JobResponse validates status/error consistency."""
    # Valid success response
    success = JobResponse(
        status="success", task="test", result={"ok": True}, error=None
    )
    assert success.status == "success"

    # Valid error response
    error = JobResponse(
        status="error", task="test", result=None, error="Failed"
    )
    assert error.status == "error"

    # Invalid: success with error message should fail
    try:
        JobResponse(
            status="success", task="test", result={"ok": True}, error="error!"
        )
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    # Invalid: error without error message should fail
    try:
        JobResponse(
            status="error", task="test", result=None, error=None
        )
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_job_response_serialization() -> None:
    """JobResponse can be serialized to dict and JSON."""
    response = JobResponse(
        status="success",
        task="echo",
        result={"value": "ok"},
        metadata={"execution_time_seconds": 0.123},
    )

    response_dict = response.to_dict()
    assert response_dict["status"] == "success"
    assert response_dict["result"] == {"value": "ok"}

    response_json = response.to_json()
    assert '"status":"success"' in response_json or '"status": "success"' in response_json
