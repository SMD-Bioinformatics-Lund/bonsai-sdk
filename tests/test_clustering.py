"""Test clustering module."""

from bonsai_libs.clustering import tree_to_newick


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


def test_single_leaf():
    """Test Newick conversion for a single leaf node."""
    node = FakeNode(id=0, dist=0.0)
    labels = ["A"]

    newick = tree_to_newick(node, labels)

    assert newick == "A:0.0;"


def test_two_leaf_tree():
    left = FakeNode(id=0, dist=0.0)
    right = FakeNode(id=1, dist=0.0)

    root = FakeNode(
        id=None,
        dist=1.0,
        left=left,
        right=right,
    )

    labels = ["A", "B"]

    result = tree_to_newick(root, labels)

    assert result == "(A:1.0,B:1.0);"
