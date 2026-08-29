from __future__ import annotations

from typing import Any

from .dispatcher import ExecutionHooks, dispatch_job
from .logging import LoggerProtocol
from .models import ExecutionContext, JobRequest, JobResponse
from .registry import TaskRegistry
from .tracing import TracerProtocol


def execute_task(
    registry: TaskRegistry,
    request: dict[str, Any] | JobRequest,
    *,
    hooks: ExecutionHooks | None = None,
    logger: LoggerProtocol | None = None,
    tracer: TracerProtocol | None = None,
    context: ExecutionContext | dict[str, Any] | None = None,
) -> JobResponse:
    """
    Generic shared entr*point for executing a raw job requ*st against a task registry.

    T*is is intended for worker-side use* where the worker receives a raw r*quest
    payload and*forwards it to the correct registe*ed task.
    """
    return dispatch_job(
        registry=registry,
        request=request,
        hooks=hooks,
        logger=logger,
        tracer=tracer,
        context=context
    )