"""Test clustering module."""

from bonsai_libs.clustering import (
    ExportNode,
    heirarchical_clustering,
    minimum_spanning_tree_clustering,
    to_newick,
)


class FakeNode:
    def __init__(self, id=None, dist=0.0, left=None, right=None):
        self.id = id
        self.dist = dist
        self._left = left
        self._right = right

    def is_leaf(self):
        return self.id is not None

    def get_left(self):
        return self._left

    def get_right(self):
        return self._right


# Helpers


def assert_valid_newick(newick: str, labels: list[str]):
    """Basic structural checks for Newick output."""
    assert newick.endswith(";")
    for label in labels:
        assert label in newick


# Heiarchical Clustering Tests


def test_hierarchical_cluster_returns_result(small_distance_matrix):
    condensed, labels = small_distance_matrix

    result = heirarchical_clustering(condensed, labels)

    assert result.root is not None
    assert result.labels == labels


def test_hierarchical_to_newick_valid(small_distance_matrix):
    condensed, labels = small_distance_matrix

    result = heirarchical_clustering(condensed, labels)
    newick = result.to_newick()

    assert_valid_newick(newick, labels)


def test_hierarchical_two_points():
    """Minimal case: two samples."""
    condensed = [1.0]
    labels = ["A", "B"]

    result = heirarchical_clustering(condensed, labels)
    newick = result.to_newick()

    assert_valid_newick(newick, labels)


# MST Clustering Tests


def test_mst_cluster_returns_result(small_distance_matrix):
    condensed, labels = small_distance_matrix

    result = minimum_spanning_tree_clustering(condensed, labels)

    assert result.root is not None
    assert result.labels == labels


def test_mst_cluster_to_newick_valid(small_distance_matrix):
    condensed, labels = small_distance_matrix

    result = minimum_spanning_tree_clustering(condensed, labels)
    newick = result.to_newick()

    assert_valid_newick(newick, labels)

    assert newick == "(A:0.000000,B:1.000000,C:2.000000);"


def test_mst_cluster_to_newick_valid_medium(medium_distance_matrix):
    condensed, labels = medium_distance_matrix

    result = minimum_spanning_tree_clustering(condensed, labels)
    newick = result.to_newick()

    assert_valid_newick(newick, labels)

    assert newick == "(A:0.000000,B:3.000000,C:4.000000,D:5.000000,E:13.000000);"


def test_mst_two_points():
    """Minimal MST case."""
    condensed = [1.0]
    labels = ["A", "B"]

    result = minimum_spanning_tree_clustering(condensed, labels)
    newick = result.to_newick()

    assert_valid_newick(newick, labels)


# Newick Tests


def test_single_leaf():
    node = ExportNode(name="A", branch_length=0.0)

    newick = to_newick(node) + ";"

    assert newick == "A:0.000000;"


def test_two_leaf_tree():
    node = ExportNode(
        name=None,
        children=[
            ExportNode(name="A", branch_length=1.0),
            ExportNode(name="B", branch_length=1.0),
        ],
    )

    newick = to_newick(node) + ";"

    assert_valid_newick(newick, ["A", "B"])
