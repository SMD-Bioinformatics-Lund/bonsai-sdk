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
