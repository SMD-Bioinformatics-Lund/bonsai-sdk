"""Fixtures for Streptococcus."""

from pathlib import Path

import pytest


@pytest.fixture()
def streptococcus_emmtyper_path(data_path: Path) -> Path:
    """Get path for Emmtyper results for streptococcus."""
    return data_path.joinpath("streptococcus", "emmtyper.tsv")


@pytest.fixture()
def streptococcus_kraken_path(data_path: Path) -> Path:
    """Get path for a Kraken report for streptococcus."""
    return data_path.joinpath("streptococcus", "kraken.report")
