"""Ecoli input data fixutres."""

import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture()
def ecoli_sample_conf_path(data_path: Path) -> Path:
    """Get path for ecoli sample config file"""
    return data_path.joinpath("ecoli", "sample_1.cnf.yml")


@pytest.fixture()
def ecoli_analysis_meta_path(data_path: Path) -> Path:
    """Get path for ecoli meta file"""
    return data_path.joinpath("ecoli", "analysis_meta.json")


@pytest.fixture()
def ecoli_bwa_path(data_path: Path) -> Path:
    """Get path for ecoli bwa qc file"""
    return data_path.joinpath("ecoli", "bwa.qc")


@pytest.fixture()
def ecoli_quast_path(data_path: Path) -> Path:
    """Get path for ecoli quast file"""
    return data_path.joinpath("ecoli", "quast.tsv")


@pytest.fixture()
def ecoli_gambitcore_path(data_path: Path) -> Path:
    """Get path for ecoli gambit file"""
    return data_path.joinpath("ecoli", "gambitcore.tsv")


@pytest.fixture()
def ecoli_amrfinder_path(data_path: Path) -> Path:
    """Get path for ecoli amrfinder file"""
    return data_path.joinpath("ecoli", "amrfinder.out")


@pytest.fixture()
def ecoli_resfinder_path(data_path: Path) -> Path:
    """Get path for ecoli resfinder file"""
    return data_path.joinpath("ecoli", "resfinder.json")


@pytest.fixture()
def ecoli_resfinder_meta_path(data_path: Path) -> Path:
    """Get path for ecoli resfinder meta file"""
    return data_path.joinpath("ecoli", "resfinder_meta.json")


@pytest.fixture()
def ecoli_virulencefinder_wo_stx_path(data_path: Path) -> Path:
    """Get path for ecoli virulencefinder without stx file"""
    return data_path.joinpath("ecoli", "virulencefinder.json")


@pytest.fixture()
def ecoli_virulencefinder_stx_pred_stx_path(data_path: Path) -> Path:
    """Get path for ecoli stx prediction file"""
    return data_path.joinpath("ecoli", "virulencefinder.stx_pred.stx.json")


@pytest.fixture()
def ecoli_virulencefinder_stx_pred_no_stx_path(data_path: Path) -> Path:
    """Get path for ecoli stx prediction no stx file"""
    return data_path.joinpath("ecoli", "virulencefinder.stx_pred.no_stx.json")


@pytest.fixture()
def ecoli_virulencefinder_meta_path(data_path: Path) -> Path:
    """Get path for ecoli virulencefinder meta file"""
    return data_path.joinpath("ecoli", "virulencefinder_meta.json")


@pytest.fixture()
def ecoli_serotypefinder_path(data_path: Path) -> Path:
    """Get path for ecoli stx prediction file"""
    return data_path.joinpath("ecoli", "serotypefinder.json")


@pytest.fixture()
def ecoli_serotypefinder_meta_path(data_path: Path) -> Path:
    """Get path for ecoli serotypefinder meta file"""
    return data_path.joinpath("ecoli", "serotypefinder_meta.json")


@pytest.fixture()
def ecoli_shigapass_path(data_path: Path) -> Path:
    """Get path for Shigapass results for ecoli."""
    return data_path.joinpath("ecoli", "shigapass.csv")


@pytest.fixture()
def ecoli_mlst_path(data_path: Path) -> Path:
    """Get path for ecoli mlst file"""
    return data_path.joinpath("ecoli", "mlst.json")


@pytest.fixture()
def ecoli_chewbbaca_path(data_path: Path) -> Path:
    """Get path for ecoli chewbbaca file"""
    return data_path.joinpath("ecoli", "chewbbaca.out")


@pytest.fixture()
def ecoli_bracken_path(data_path: Path) -> Path:
    """Get path for ecoli bracken file"""
    return data_path.joinpath("ecoli", "bracken.out")


@pytest.fixture()
def ecoli_cdm_input(data_path: Path) -> list[dict[str, Any]]:
    """Get path for ecoli cdm file"""
    path = data_path.joinpath("ecoli", "cdm_input.json")
    with open(path, "rb") as inpt:
        return json.load(inpt)


@pytest.fixture()
def ecoli_kleborate_path(data_path: Path) -> Path:
    """Get path for kleborate result file"""
    return data_path.joinpath("ecoli", "kleborate_v3_escherichia_output.txt")
