"""Shared clustering methods for Bonsai microservices."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Sequence

from scipy.cluster import hierarchy
from scipy.sparse import csr_array
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.spatial.distance import squareform

# Data structures

@dataclass(frozen=True)
class Edge:
    """A graph edge connecting nodes."""

    target: int
    weight: float


Graph = dict[int, list[Edge]]


@dataclass
class ExportNode:
    """
    Unified rooted tree node for all clustering outputs.

    This is the only structure used for downstream consumption
    """

    name: str | None = None
    branch_length: float = 0.0
    children: list["ExportNode"] = field(default_factory=list)

    def is_leaf(self) -> bool:
        """Return true if node is a leaf node."""
        return not self.children


# Public API types


class LinkageMethod(StrEnum):
    """Linkage methods for hierarchical clustering."""

    SINGLE = "single"
    COMPLETE = "complete"
    AVERAGE = "average"
    WEIGHTED = "weighted"
    CENTROID = "centroid"


class ClusteringAlgorithm(StrEnum):
    """Supported clustering strategies."""

    HIERARCHICAL = "hierarchical"
    MST = "mst"


@dataclass(frozen=True)
class ClusterResult:
    """Result of a clustering operation."""

    root: ExportNode
    labels: Sequence[str]

    def to_newick(self) -> str:
        """Convert the clustering result to Newick format."""
        return to_newick(self.root) + ";"


# Hierarchical clustering


def hierarchical_clustering(
    condensed_distance_matrix: Sequence[float],
    labels: Sequence[str],
    *,
    method: LinkageMethod = LinkageMethod.SINGLE,
) -> ClusterResult:
    """Perform hierarchial clustering on a condensed distance matrix.

    Output is converted into ExportNode for consistency with MST results.
    """
    linkage = hierarchy.linkage(condensed_distance_matrix, method=method.value)
    scipy_tree = hierarchy.to_tree(linkage, False)
    root = _convert_scipy_tree(
        scipy_tree,
        labels=labels,
        parent_dist=float(scipy_tree.dist),
    )

    return ClusterResult(root=root, labels=labels)


def _convert_scipy_tree(
    node,
    *,
    labels: Sequence[str],
    parent_dist: float,
) -> ExportNode:
    """Convert SciPy cluster tree into ExportNode."""
    branch_length = float(parent_dist - node.dist)

    if node.is_leaf():
        return ExportNode(
            name=labels[node.id],
            branch_length=branch_length,
        )

    left = _convert_scipy_tree(node.get_left(), labels=labels, parent_dist=node.dist)
    right = _convert_scipy_tree(node.get_right(), labels=labels, parent_dist=node.dist)

    return ExportNode(
        name=None,
        branch_length=branch_length,
        children=[left, right],
    )


# MST clustering


def minimum_spanning_tree_clustering(
    condensed_distance_matrix: Sequence[float],
    labels: Sequence[str],
    *,
    root_index: int = 0,
) -> ClusterResult:
    """
    Perform MST clustering and convert to rooted export tree.

    Suitable for GrapeTree-like visualisation.
    """
    if not labels:
        raise ValueError("labels must not be empty")

    if not (0 <= root_index < len(labels)):
        raise ValueError("root_index out of range")

    graph = _build_mst_graph(condensed_distance_matrix, size=len(labels))
    root = _root_graph(graph, labels, root_index=root_index)

    return ClusterResult(root=root, labels=labels)


def _build_mst_graph(
    condensed_distance_matrix: Sequence[float],
    *,
    size: int,
) -> Graph:
    """Build undirected MST graph."""
    matrix = csr_array(squareform(condensed_distance_matrix))
    mst = minimum_spanning_tree(matrix)

    # Make undirected
    mst = mst + mst.T

    graph: defaultdict[int, list[Edge]] = defaultdict(list)
    coo = mst.tocoo()

    for i, j, weight in zip(coo.row, coo.col, coo.data):
        graph[i].append(Edge(target=j, weight=float(weight)))

    # Ensure all nodes exist (defensive)
    for i in range(size):
        graph.setdefault(i, [])

    return dict(graph)


def _root_graph(
    graph: Graph,
    labels: Sequence[str],
    root_index: int | None = None,
    parent: int | None = None,
    branch_length: float = 0.0,
) -> ExportNode:
    """Convert graph into rooted tree."""

    if not root_index:
        # Use synthetic root
        root_index = 0
        root = ExportNode(name=None, branch_length=0.0)
        root.children.append(
            ExportNode(
                name=labels[root_index],
                branch_length=0.0,
            )
        )
    else:
        root = ExportNode(name=labels[root_index], branch_length=branch_length)

    # Build graph
    for edge in graph.get(root_index, []):
        # Prevent traversing back to parent
        if edge.target == parent:
            continue

        child = _root_graph(
            graph,
            labels,
            root_index=edge.target,
            parent=root_index,
            branch_length=edge.weight,
        )
        root.children.append(child)

    return root


# Newick export


def to_newick(node: ExportNode) -> str:
    """Convert ExportNode tree to Newick format."""

    if node.is_leaf():
        if node.name is None:
            raise ValueError("Leaf node missing name")
        return f"{node.name}:{node.branch_length:.6f}"

    children_str = ",".join(to_newick(child) for child in node.children)

    # Internal node naming is optional
    if node.name:
        if node.branch_length > 0:
            return f"({children_str}){node.name}:{node.branch_length:.6f}"
        return f"({children_str}){node.name}"

    if node.branch_length > 0:
        return f"({children_str}):{node.branch_length:.6f}"
    
    return f"({children_str})"
