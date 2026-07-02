import pytest
from pydantic import BaseModel

from bonsai_libs.jobs import JobRequest, JobResponse, TaskRegistry, dispatch_job
from bonsai_libs.jobs.exceptions import TaskNotFoundError, TaskValidationError


class ExamplePayload(BaseModel):
    value: str


def test_registry_registers_and_lists_tasks() -> None:
    registry = TaskRegistry()

    @registry.register("echo")
    def echo(value: str) -> dict[str, str]:
        return {"value": value}

    assert registry.get("echo") is echo
    assert registry.list() == ["echo"]


def test_registry_rejects_duplicate_or_invalid_tasks() -> None:
    registry = TaskRegistry()

    @registry.register("sample")
    def sample() -> str:
        return "ok"

    with pytest.raises(TaskValidationError):

        @registry.register("sample")
        def duplicate() -> str:
            return "no"

    with pytest.raises(TaskValidationError):
        registry.register("")


def test_dispatch_job_returns_structured_success_response() -> None:
    registry = TaskRegistry()

    @registry.register("echo")
    def echo(value: str) -> dict[str, str]:
        return {"value": value}

    response = dispatch_job(registry, {"task": "echo", "payload": {"value": "ok"}})

    assert isinstance(response, JobResponse)
    assert response.status == "success"
    assert response.result == {"value": "ok"}
    assert response.error is None
    assert response.metadata["execution_time_seconds"] >= 0


def test_dispatch_job_handles_missing_tasks_and_non_serializable_results() -> None:
    registry = TaskRegistry()

    @registry.register("custom", input_schema=ExamplePayload)
    def custom(value: str) -> object:
        return type("Thing", (), {"value": value})()

    missing = dispatch_job(registry, {"task": "missing", "payload": {}})
    assert missing.status == "error"
    assert missing.result is None
    assert "not found" in missing.error.lower()
    assert missing.metadata["error_type"] == "TaskNotFoundError"

    success = dispatch_job(registry, {"task": "custom", "payload": {"value": "ok"}})
    assert success.status == "success"
    assert isinstance(success.result, str)
    assert "Thing" in success.result
