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

The job framework in bonsai_libs.jobs provides a small, foundation for dispatching Python tasks across services. It standardises task registration, request validation, execution boundaries, and JSON-safe responses so that services can share a predictable output.

### Architecture

- Registry: stores explicitly registered tasks and optional input schemas.
- Dispatcher: validates incoming requests, resolves the task, executes it, and returns a structured JobResponse.
- Worker: provides a secured execution wrapper for environments such as RQ that only permits explicitly whitelisted entrypoints.
- Models: define strict request/response schemas using Pydantic to ensure that the public contract stays JSON-compatible.

### Usage example

```python
from bonsai_libs.jobs import TaskRegistry, dispatch_job

registry = TaskRegistry()

@registry.register("add_signature")
def add_signature(sample_id: str) -> dict[str, str]:
    return {"status": "added", "id": sample_id}

response = dispatch_job(registry, {
    "task": "add_signature",
    "payload": {"sample_id": "123"},
})
```

### JSON contract

All inputs and outputs are intentionally JSON-compatible. Requests and responses use plain dictionaries, strings, numbers, booleans, lists, and null values. Non-serialisable Python objects are converted to a safe string representation before being returned.

### Security model

The framework avoids arbitrary code execution. Tasks are executed only if they are explicitly registered in the registry, and the secure worker only runs whitelisted entrypoints.

### Design principles

- Simplicity: the framework stays small and explicit.
- Consistency: all services share the same request and response model.
- Safety: failures are captured early and returned as structured errors without leaking stack traces.

### Extension points

New tasks can be added by registering them with the registry. Schemas can evolve over time by using Pydantic models for task-specific payload validation, while the dispatcher continues to enforce the shared contract.
