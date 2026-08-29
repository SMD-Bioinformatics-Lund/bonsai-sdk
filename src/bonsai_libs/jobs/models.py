"""Task execution context and related models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

if TYPE_CHECKING:
    from .logging import LoggerProtocol
    from .tracing import TracerProtocol


class ExecutionContext(BaseModel):
    """Standardized execution context attached to job requests and responses."""

    model_config = ConfigDict(extra="forbid")

    request_id: str | None = Field(default=None, description="Unique request identifier")
    trace_id: str | None = Field(default=None, description="Distributed tracing identifier")
    span_id: str | None = Field(default=None, description="Current span identifier")
    service: str | None = Field(default=None, description="Name of the emitting service")
    attempt: int = Field(default=1, ge=1, description="Current execution attempt")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Execution context timestamp",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context data")


@dataclass
class TaskContext:
    """Context passed to task functions with execution data and tools."""

    execution: ExecutionContext
    logger: LoggerProtocol | None = None
    tracer: TracerProtocol | None = None


def build_execution_context(
    *,
    request_id: str | None = None,
    trace_id: str | None = None,
    span_id: str | None = None,
    service: str | None = None,
    attempt: int = 1,
    metadata: dict[str, Any] | None = None,
) -> ExecutionContext:
    """Create a standardized execution context payload."""
    return ExecutionContext(
        request_id=request_id,
        trace_id=trace_id,
        span_id=span_id,
        service=service,
        attempt=attempt,
        metadata=metadata or {},
    )


class JobRequest(BaseModel):
    """Represents a job execution request."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(..., description="Name of the registered task to execute")
    payload: dict[str, Any] = Field(default_factory=dict, description="Task arguments")
    context: ExecutionContext | None = Field(default=None, description="Execution context")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional request metadata")

    @field_validator("task")
    @classmethod
    def validate_task_name(cls, value: str) -> str:
        """Ensure task names are not empty or whitespace-only."""
        if not value or not value.strip():
            raise ValueError("task name must be non-empty")
        return value.strip()

    @field_validator("context", mode="before")
    @classmethod
    def normalize_context(cls, value: Any) -> Any:
        """Normalize a mapping-like context into an ExecutionContext instance."""
        if value is None or isinstance(value, ExecutionContext):
            return value
        if isinstance(value, dict):
            return ExecutionContext(**value)
        raise TypeError("context must be an ExecutionContext or mapping")


class JobResponse(BaseModel):
    """Represents a job execution response."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "error"] = Field(..., description="Execution status")
    task: str = Field(..., description="Name of the executed task")
    result: Any | None = Field(default=None, description="Task result (if successful)")
    error: str | None = Field(default=None, description="Error message (if failed)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Execution metadata")

    @model_validator(mode="after")
    def validate_status_consistency(self) -> "JobResponse":
        """Ensure success and error fields remain consistent."""
        if self.status == "success" and self.error is not None:
            raise ValueError("status is 'success' but error is set")
        if self.status == "error" and self.error is None:
            raise ValueError("status is 'error' but error is not set")
        return self

    def to_dict(self) -> dict[str, Any]:
        """Export response as a dictionary."""
        return self.model_dump(mode="json")

    def to_json(self) -> str:
        """Export response as a JSON string."""
        return self.model_dump_json()
