"""Pydantic models for job execution framework."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class JobRequest(BaseModel):
    """Represents a job execution request."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(..., description="Name of the registered task to execute")
    payload: dict[str, Any] = Field(default_factory=dict, description="Task arguments")

    @field_validator("task")
    @classmethod
    def validate_task_name(cls, value: str) -> str:
        """Ensure task names are not empty or whitespace-only."""
        if not value or not value.strip():
            raise ValueError("task name must be non-empty")
        return value.strip()


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
