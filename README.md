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

## VirulenceFinder STX typing

VirulenceFinder v2 and v3 return `TypingResultStx` for a nonempty STX result.
The existing `gene_symbol`, `accession`, `identity`, and `coverage` fields remain
a best-match summary. Read **`hits`** for the complete typing evidence:

```python
from bonsai_libs.parse import run_parser

output = run_parser(software="virulencefinder", version="3.2.0", data="result.json")
stx = output.results["stx"]
if stx.status == "parsed":
    for hit in stx.value.hits:
        print(hit.gene_symbol, hit.accession, hit.identity, hit.coverage)
```

All matches from the dedicated STX assay are retained, including alternatives
for the same toxin type. They are evidence reported by VirulenceFinder, rather
than independently confirmed toxin copies. In v3, a region shared by multiple
phenotypes is listed once. Matches are ordered by gene symbol and coverage.
Ordinary virulence database findings stay in the virulence result.

Summary ranking retains coverage then identity for v2; v3 selects by coverage
then identity within each typing phenotype, then identity and coverage across
phenotypes. Exact ties retain the first input hit. No typing findings still
produce `status="empty"` and `value=None`. `hydrate_result` accepts both the new
payload and historical single-gene payloads, exposing the latter as one hit.

Existing consumers that use only the summary fields will still show one hit.
Consumers must iterate `hits` to display or export the full profile. This is an
additive payload change; the VirulenceFinder parser version is now 2.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```
