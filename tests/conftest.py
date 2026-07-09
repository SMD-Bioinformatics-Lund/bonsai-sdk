"""Test fixtures."""

from bonsai_libs.parse.core.registry import _PARSER_REGISTRY, _RESULT_MODEL_REGISTRY

from .fixtures import *


@pytest.fixture()
def data_path() -> Path:
    """Get path of this file"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def clear_registry_before_each_test():
    """Ensure a clean registry for each test."""
    _PARSER_REGISTRY.clear()
    _RESULT_MODEL_REGISTRY.clear()
    yield
    _PARSER_REGISTRY.clear()
    _RESULT_MODEL_REGISTRY.clear()


@pytest.fixture()
def small_distance_matrix() -> tuple[list[float], list[str]]:
    """
    Create a simple 3-sample condensed distance matrix.

    Distances:
        A-B = 1
        A-C = 2
        B-C = 3
    """
    labels = ["A", "B", "C"]
    condensed = [1.0, 2.0, 3.0]
    return condensed, labels


@pytest.fixture
def medium_distance_matrix():
    """
    Create a more complex condensed distance matrix

    Distances:
        A-B = 3
        A-C = 4.5
        A-D = 5.5
        A-E = 13
        B-C = 5.5
        B-D = 6.5
        B-E = 14
        C-D = 7
        C-E = 15.5
        D-E = 16.5

    """

    labels = ["A", "B", "C", "D", "E"]
    condensed = [
        3,
        4,
        5,
        13,
        5,
        6,
        14,
        7,
        15,
        16,
    ]
    return condensed, labels
