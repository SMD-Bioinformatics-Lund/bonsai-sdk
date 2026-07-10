"""Keep track of Klebsiella pneumoniae fixtures."""

from pathlib import Path

import pytest


@pytest.fixture()
def kp_kleborate_path(data_path: Path) -> Path:
    """Get path for kleborate result file"""
    return data_path.joinpath("kpneumoniae", "kleborate_v3_kpsc_output.txt")


@pytest.fixture()
def kp_kleborate_hamronization_path(data_path: Path) -> Path:
    """Get path for kleborate result file"""
    return data_path.joinpath(
        "kpneumoniae", "kleborate_v3_kpsc_hamronization_output.txt"
    )


@pytest.fixture()
def kp_sample_conf_path(data_path: Path) -> Path:
    """Get path for klebsiella sample config file"""
    return data_path.joinpath("kpneumoniae", "sample_1.cnf.yml")


@pytest.fixture()
def kp_analysis_meta_path(data_path: Path) -> Path:
    """Get path for ecoli meta file"""
    return data_path.joinpath("kpneumoniae", "analysis_meta.json")


@pytest.fixture()
def kp_quast_path(data_path: Path) -> Path:
    """Get path for ecoli meta file"""
    return data_path.joinpath("kpneumoniae", "quast.tsv")
