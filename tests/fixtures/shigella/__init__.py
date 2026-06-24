"""Fixtures for Shigella."""

from pathlib import Path

import pytest


@pytest.fixture()
def shigella_shigapass_path(data_path: Path) -> Path:
    """Get path for Shigapass results for shigella."""
    return data_path.joinpath("shigella", "shigapass.csv")
