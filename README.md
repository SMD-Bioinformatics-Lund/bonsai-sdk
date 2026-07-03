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

All registered tasks **must** accept an `ExecutionContext` parameter. This ensures every task has access to request tracing, service identity, and retry metadata.

```python
from bonsai_libs.jobs import TaskRegistry, ExecutionContext, dispatch_job

registry = TaskRegistry()

@registry.register("add_signature")
def add_signature(sample_id: str, context: ExecutionContext) -> dict[str, str]:
    # context contains request_id, trace_id, service, attempt, timestamp, etc.
    print(f"Request: {context.request_id}")
    return {"status": "added", "id": sample_id}

response = dispatch_job(registry, {
    "task": "add_signature",
    "payload": {"sample_id": "123"},
})
```

### Execution context and tracing

Every task receives an `ExecutionContext` that enables end-to-end request tracing:

```python
from bonsai_libs.jobs import build_execution_context

context = build_execution_context(
    request_id="req-123",
    trace_id="trace-456",
    service="my-service",
    attempt=1,
)

response = dispatch_job(
    registry,
    {"task": "add_signature", "payload": {"sample_id": "123"}},
    context=context,
)
```

### Structured logging

The framework uses a `LoggerProtocol` for structured logging, decoupled from implementation:

```python
from bonsai_libs.jobs import ExecutionHooks, StandardLogger

logger = StandardLogger(name="my-service")
hooks = ExecutionHooks(logger=logger)

dispatch_job(registry, request, hooks=hooks)
# Logs: task.start, task.success, or task.error with structured fields
```

### Lifecycle hooks

Optional hooks allow services to integrate observability and business logic:

```python
def before_task(context: ExecutionContext, payload: dict) -> None:
    # Prepare execution context or validate preconditions
    pass

def after_task(context: ExecutionContext, payload: dict) -> None:
    # Record success, update cache, etc.
    pass

def on_error(context: ExecutionContext, exc: Exception) -> None:
    # Record failure, create alert, etc.
    pass

hooks = ExecutionHooks(
    logger=logger,
    before_task=before_task,
    after_task=after_task,
    on_error=on_error,
)

dispatch_job(registry, request, hooks=hooks)
```

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

New tasks are added by registering them with required `ExecutionContext` parameter. Payload schemas can evolve using Pydantic models, while the dispatcher enforces the shared contract. Custom loggers can be injected via the hook system.
