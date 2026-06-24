"""Pydantic models for job execution framework."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class JobRequest(BaseModel):
    """Represents a job execution request.

    Attributes:
        task: The name of the registered task to execute.
        payload: Dictionary of task arguments.
    """

    task: str = Field(..., description="Name of the registered task to execute")
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Task arguments"
    )

    class Config:
        """Pydantic config."""

        extra = "forbid"

    @field_validator("task")
    @classmethod
    def validate_task_name(cls, v: str) -> str:
        """Ensure task name is non-empty."""
        if not v or not v.strip():
            raise ValueError("task name must be non-empty")
        return v.strip()


class JobResponse(BaseModel):
    """Represents a job execution response.

    Attributes:
        status: Execution status (success or error).
        task: Name of the executed task.
        result: Task result if successful, None otherwise.
        error: Error message if failed, None otherwise.
        metadata: Execution metadata (timing, etc).
    """

    status: Literal["success", "error"] = Field(
        ..., description="Execution status"
    )
    task: str = Field(..., description="Name of the executed task")
    result: Any | None = Field(
        default=None, description="Task result (if successful)"
    )
    error: str | None = Field(
        default=None, description="Error message (if failed)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Execution metadata"
    )

    class Config:
        """Pydantic config."""

        extra = "forbid"

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str, info) -> str:
        """Ensure result/error consistency."""
        result = info.data.get("result")
        error = info.data.get("error")

        if v == "success" and error is not None:
            raise ValueError(
                "status is 'success' but error is set"
            )
        if v == "error" and error is None:
            raise ValueError(
                "status is 'error' but error is not set"
            )

        return v

    def to_dict(self) -> dict[str, Any]:
        """Export response as dictionary (JSON-safe)."""
        return self.model_dump()

    def to_json(self) -> str:
        """Export response as JSON string."""
        return self.model_dump_json()
