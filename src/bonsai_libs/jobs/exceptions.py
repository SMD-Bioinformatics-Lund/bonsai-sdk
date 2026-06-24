"""Custom exceptions for the job execution framework."""


class JobExecutionError(Exception):
    """Base exception for job execution errors."""


class TaskNotFoundError(JobExecutionError):
    """Raised when a requested task is not registered."""


class TaskValidationError(JobExecutionError):
    """Raised when task validation fails."""


class InvalidJobRequestError(JobExecutionError):
    """Raised when JobRequest validation fails."""


class UnauthorizedJobExecutionError(JobExecutionError):
    """Raised when a job tries to execute an unauthorized entrypoint."""
