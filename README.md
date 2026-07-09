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

## Clustering module

The library includes a clustering module that provides utilities for grouping samples based on pairwise distances.

It supports two complementary approaches:
 - **Hierarchical clustering**, implemented using SciPy linkage methods
 - **Minimum spanning tree (MST)–based clustering**, suitable for graph-based visualisation tools such as GrapeTree

Both methods return a unified result type, allowing them to be used interchangeably within services. The results are represented internally as a normalised tree structure, which enables consistent downstream processing.

Clustering outputs can be serialised to Newick format using a shared exporter. For MST-based clustering, an unrooted tree is represented via a synthetic root to ensure compatibility with visualisation tools while preserving the underlying topology.

The module is designed to be reusable across microservices and provides a consistent interface for clustering logic and output formatting.

Example usage

```python
from bonsai_libs.clustering import (
    hierarchical_clustering,
)

# Condensed distance matrix and labels
labels = ["A", "B", "C"]
condensed_dm = [1.0, 2.0, 3.0]

result = hierarchical_clustering(condensed_dm, labels)
newick = result.to_newick()
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```
