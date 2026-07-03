# Bonsai API

Shared API client library for Bonsai services (bonsai, audit log, notification, etc.). It might be expanded in the future to include other shared resources.

## Quick start

Install from a package repository (example):

```bash
pip install bonsai-libs
```

Or use a git dependency in `pyproject.toml`:

```toml
[project]
dependencies = [
  "bonsai-libs @ git+https://github.com/mhkc/bonsai-libs.git@v0.1.0",
]
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

## Reusable job framework

### Overview

The job framework in `bonsai_libs.jobs` provides a lightweight foundation for dispatching Python tasks across microservices. It standardises task registration, request validation, execution context passing, structured logging, and JSON-safe responses so that services can share a predictable contract.

### Architecture

- **Registry**: Stores explicitly registered tasks with optional input schemas. Validates that tasks accept an execution context parameter.
- **Dispatcher**: Validates incoming requests, resolves the task, executes it with context, and returns a structured JobResponse.
- **ExecutionContext**: Standardized metadata passed to every task including request ID, trace ID, service name, and attempt number.
- **Hooks**: Optional callbacks for task lifecycle events (before, after, on_error) and structured logging.
- **Worker**: Provides a secured execution wrapper for environments such as RQ that only permits explicitly whitelisted entrypoints.
- **Models**: Pydantic schemas for requests, responses, and context to ensure the public contract stays JSON-compatible.

### Task registration

All registered tasks **must** accept a `TaskContext` parameter. This ensures every task has access to request tracing, service identity, logging, and retry metadata.

```python
from bonsai_libs.jobs import TaskRegistry, TaskContext, dispatch_job

registry = TaskRegistry()

@registry.register("add_signature")
def add_signature(sample_id: str, context: TaskContext) -> dict[str, str]:
    # context.execution contains request_id, trace_id, service, attempt, timestamp, etc.
    # context.logger provides structured logging
    # context.tracer provides distributed tracing with spans
    if context.logger:
        context.logger.info("processing_sample", sample_id=sample_id)
    return {"status": "added", "id": sample_id}

response = dispatch_job(registry, {
    "task": "add_signature",
    "payload": {"sample_id": "123"},
})
```

### Execution context and tracing

Every task receives a `TaskContext` that combines execution metadata with optional logging and tracing tools:

```python
from bonsai_libs.jobs import build_execution_context, StandardLogger, dispatch_job

context = build_execution_context(
    request_id="req-123",
    trace_id="trace-456",
    service="my-service",
    attempt=1,
)

logger = StandardLogger(name="my-service")

response = dispatch_job(
    registry,
    {"task": "add_signature", "payload": {"sample_id": "123"}},
    context=context,
    logger=logger,  # Optional: logger is passed to task via TaskContext
)
```

### Structured logging and tracing

The framework uses a `LoggerProtocol` for structured logging, and `TracerProtocol` for distributed tracing:

```python
from bonsai_libs.jobs import ExecutionHooks, StandardLogger

logger = StandardLogger(name="my-service")

# Optional: Create explicit tracer
from bonsai_libs.jobs import SimpleTracer
tracer = SimpleTracer(logger=logger)

response = dispatch_job(
    registry,
    request,
    logger=logger,
    tracer=tracer,  # Optional: if provided, passed to task via TaskContext
)
# Logs: task.start, task.success, or task.error with structured fields
```

#### Tracing with spans

Tasks can use the tracer from context to create execution spans:

```python
@registry.register("process_sample")
def process_sample(sample_id: str, context: TaskContext) -> dict[str, object]:
    if context.tracer:
        with context.tracer.start_span("validate_sample", sample_id=sample_id):
            # Validation logic...
            pass
        
        with context.tracer.start_span("run_analysis"):
            # Analysis logic...
            pass
    
    return {"status": "complete"}
```

Span events are logged as structured messages:
- `span.start`: When entering a span (metadata included)
- `span.end`: When exiting a span (duration_seconds included)
- `span.error`: If an exception occurs (error_type, error_message, duration_seconds included)


### Lifecycle hooks

Optional hooks allow services to integrate observability and business logic:

```python
def before_task(context: TaskContext, payload: dict) -> None:
    # Prepare execution context or validate preconditions
    # Can access logger and tracer if provided
    if context.logger:
        context.logger.debug("task_starting", task_id=context.execution.request_id)

def after_task(context: TaskContext, payload: dict) -> None:
    # Record success, update cache, etc.
    if context.logger:
        context.logger.info("task_completed")

def on_error(context: TaskContext, exc: Exception) -> None:
    # Record failure, create alert, etc.
    if context.logger:
        context.logger.error("task_failed", error=str(exc))

hooks = ExecutionHooks(
    before_task=before_task,
    after_task=after_task,
    on_error=on_error,
)

dispatch_job(registry, request, hooks=hooks, logger=logger)
```

Note: ExecutionHooks no longer has `logger` or `tracer` fields. Instead, pass them separately to `dispatch_job()` and they become available to hooks via the `TaskContext.logger` and `TaskContext.tracer` attributes.

### JSON contract

All inputs and outputs are JSON-compatible. Requests and responses use plain dictionaries, strings, numbers, booleans, lists, and null values. Non-serializable Python objects are converted to safe string representations.

### Security model

The framework avoids arbitrary code execution:
- Tasks are executed only if explicitly registered in the registry.
- Task signatures are verified at registration time to ensure they accept context.
- The secure worker only runs whitelisted entrypoints.
- No dynamic imports or eval-style execution.

### Design principles

- **Simplicity**: The framework stays small and explicit.
- **Consistency**: All services share the same request, response, and context models.
- **Safety**: Failures are captured early and returned as structured errors without leaking stack traces.
- **Observability**: Every task execution includes trace ID, request ID, execution time, and structured logging.

### Extension points

New tasks are added by registering them with required `TaskContext` parameter. Payload schemas can evolve using Pydantic models, while the dispatcher enforces the shared contract. Custom loggers and tracers can be injected via `dispatch_job()` parameters.
