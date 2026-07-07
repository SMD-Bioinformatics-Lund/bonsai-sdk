"""Shared clustering methods for Bonsai microservices."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Sequence

from scipy.cluster import hierarchy

TreeNode = Any


class LinkageMethod(StrEnum):
    """Linkage methods for hierarchical clustering."""

    SINGLE = "single"
    COMPLETE = "complete"
    AVERAGE = "average"
    WEIGHTED = "weighted"
    CENTROID = "centroid"


@dataclass(frozen=True)
class ClusterResult:
    """Result of a clustering operation."""

    tree: TreeNode
    labels: Sequence[str]

    def to_newick(self) -> str:
        """Convert the clustering result to Newick format."""
        return tree_to_newick(self.tree, self.labels)


def heirarchical_clustering(
    condensed_distance_matrix: Sequence[float],
    labels: Sequence[str],
    *,
    method: LinkageMethod = LinkageMethod.SINGLE,
) -> ClusterResult:
    """Perform hierarchial clustering on a condensed distance matrix."""
    tree = hierarchy.linkage(condensed_distance_matrix, method=method.value)
    return ClusterResult(tree=tree, labels=labels)


def tree_to_newick(tree: TreeNode, labels: Sequence[str]) -> str:
    """Convert a hierarchical clustering tree to Newick format."""
    newick = _to_newick_recursive(tree, "", tree.dist, labels)
    if not newick.endswith(";"):
        newick += ";"
    return newick


def _to_newick_recursive(
    node: TreeNode, newick: str, parent_dist: float, labels: Sequence[str]
) -> str:
    """Recursively convert a hierarchical clustering tree to Newick format."""

    if node.is_leaf():
        return f"{labels[node.id]}:{parent_dist - node.dist}{newick}"

    if newick:
        newick = f"):{parent_dist - node.dist}{newick}"
    else:
        newick = ");"

    newick = _to_newick_recursive(node.get_right(), newick, node.dist, labels)
    newick = _to_newick_recursive(node.get_left(), f",{newick}", node.dist, labels)

    return f"({newick}"
