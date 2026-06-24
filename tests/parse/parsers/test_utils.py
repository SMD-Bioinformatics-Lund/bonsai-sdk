"""Test various utility functions."""

import pytest

from bonsai_libs.parse.parsers.utils import safe_percent


@pytest.mark.parametrize(
    "input,expected",
    [
        ("48.2%", 48.2),
        ("48.0%", 48.0),
        ("48%", 48.0),
        ("0.0%", 0.0),
        ("0%", 0.0),
    ],
)
def test_safe_percentage_conversion(input: str, expected: float):
    """Test that the percentage can be converted

    "12%" -> 12%
    """
    result = safe_percent(input)
    assert result == expected


@pytest.mark.parametrize(
    "input,expected",
    [
        ("48.2", 48.2),
        ("48.0", 48.0),
        ("48", 48.0),
        ("0.0", 0.0),
        ("0", 0.0),
    ],
)
def test_safe_float_conversion(input: str, expected: float):
    """Test conversion of stringed floats."""
    result = safe_percent(input)
    assert result == expected
