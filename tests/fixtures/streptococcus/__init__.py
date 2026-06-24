"""Fixtures for Streptococcus."""

from pathlib import Path

import pytest


@pytest.fixture()
def streptococcus_emmtyper_path(data_path: Path) -> Path:
    """Get path for Emmtyper results for streptococcus."""
    return data_path.joinpath("streptococcus", "emmtyper.tsv")
