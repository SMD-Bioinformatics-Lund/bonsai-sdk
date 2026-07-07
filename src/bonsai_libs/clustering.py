"""Shared clustering methods for Bonsai microservices."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Sequence

import networkx as nx
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


def minimum_spanning_tree(
    condensed_distance_matrix: Sequence[float],
    labels: Sequence[str],
) -> nx.Graph:
    """Generate a minimum spanning tree for the given distance matrix."""
    # Create a graph from the distance matrix
    G = nx.from_edgelist(
        [(i, j, d) for i in range(len(labels)) for j in range(i + 1, len(labels))],
        create_using=nx.Graph,
    )

    # Add edge weights to the graph
    for (i, j), d in zip(G.edges(), condensed_distance_matrix):
        G[i][j]['weight'] = d

    # Find the minimum spanning tree
    mst = nx.minimum_spanning_tree(G)

    return mst


def mst_to_newick(mst: nx.Graph, labels: Sequence[str]) -> str:
    """Convert a minimum spanning tree to Newick format."""
    newick = _mst_to_newick_recursive(mst, "", 0, labels)
    if not newick.endswith(";"):
        newick += ";"
    return newick


def _mst_to_newick_recursive(
    mst: nx.Graph, newick: str, parent_dist: float, labels: Sequence[str]
) -> str:
    """Recursively convert a minimum spanning tree to Newick format."""

    if len(mst.nodes()) == 1:
        return f"{labels[list(mst.nodes())[0]}:{parent_dist}{newick}"

    for node in mst.nodes():
        neighbors = list(mst.neighbors(node))
        if len(neighbors) == 1:
            child_node = neighbors[0]
            edge_weight = mst[node][child_node]['weight']
            newick = f"{labels[child_node]}:{parent_dist + edge_weight}{newick}"
            return _mst_to_newick_recursive(mst.subgraph([node, child_node]), newick, parent_dist + edge_weight, labels)

    raise ValueError("Invalid minimum spanning tree")
