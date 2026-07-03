"""Reusable job execution framework for Bonsai services."""

from .dispatcher import ExecutionHooks
from .exceptions import (
    InvalidJobRequestError,
    JobExecutionError,
    TaskNotFoundError,
    TaskValidationError,
    UnauthorizedJobExecutionError,
)
from .logging import LoggerProtocol, StandardLogger
from .models import ExecutionContext, JobRequest, JobResponse, TaskContext, build_execution_context
from .registry import TaskRegistry
from .tracing import SimpleTracer, TracerProtocol
from .worker import SecureWorker, configure_worker
from .queueing import configure_queue, schedule_job
from .entrypoint import execute_task

__all__ = [
    "ExecutionContext",
    "ExecutionHooks",
    "JobRequest",
    "JobResponse",
    "LoggerProtocol",
    "SimpleTracer",
    "StandardLogger",
    "TaskContext",
    "TaskRegistry",
    "TracerProtocol",
    "UnauthorizedJobExecutionError",
    "build_execution_context",
    "configure_queue",
    "configure_worker",
    "InvalidJobRequestError",
    "JobExecutionError",
    "SecureWorker",
    "TaskNotFoundError",
    "TaskValidationError",
    "schedule_job",
    "execute_task",
]
