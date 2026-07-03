"""Reusable job execution framework for Bonsai services."""

from .dispatcher import ExecutionHooks, dispatch_job
from .exceptions import (
    InvalidJobRequestError,
    JobExecutionError,
    TaskNotFoundError,
    TaskValidationError,
    UnauthorizedJobExecutionError,
)
from .logging import LoggerProtocol, StandardLogger
from .models import ExecutionContext, JobRequest, JobResponse, build_execution_context
from .registry import TaskRegistry
from .worker import SecureWorker, build_queue_config, build_worker_config, configure_queue, configure_worker

__all__ = [
    "ExecutionContext",
    "ExecutionHooks",
    "LoggerProtocol",
    "StandardLogger",
    "build_execution_context",
    "build_queue_config",
    "build_worker_config",
    "configure_queue",
    "configure_worker",
    "dispatch_job",
    "InvalidJobRequestError",
    "JobExecutionError",
    "JobRequest",
    "JobResponse",
    "SecureWorker",
    "TaskRegistry",
    "TaskNotFoundError",
    "TaskValidationError",
    "UnauthorizedJobExecutionError",
]
