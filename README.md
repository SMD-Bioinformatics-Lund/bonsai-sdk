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
  "bonsai-libs @ git+https://github.com/SMD-Bioinformatics-Lund/bonsai-sdk.git@v0.2.1",
]
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```
