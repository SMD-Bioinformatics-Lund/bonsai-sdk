"""mtuberculosis input data fixutres."""

from pathlib import Path

import pytest


@pytest.fixture()
def mtuberculosis_sample_conf_path(data_path: Path) -> Path:
    """Get path for mtuberculosis sample config file"""
    return data_path.joinpath("mtuberculosis", "sample_1.cnf.yml")


@pytest.fixture()
def mtuberculosis_analysis_meta_path(data_path: Path) -> Path:
    """Get path for mtuberculosis meta file"""
    return data_path.joinpath("mtuberculosis", "analysis_meta.json")


@pytest.fixture()
def mtuberculosis_bracken_path(data_path: Path) -> Path:
    """Get path for mtuberculosis bracken file"""
    return data_path.joinpath("mtuberculosis", "bracken.out")


@pytest.fixture()
def mtuberculosis_bwa_path(data_path: Path) -> Path:
    """Get path for mtuberculosis bwa qc file"""
    return data_path.joinpath("mtuberculosis", "bwa.qc")


@pytest.fixture()
def mtuberculosis_mykrobe_path(data_path: Path) -> Path:
    """Get path for mtuberculosis mykrobe file"""
    return data_path.joinpath("mtuberculosis", "mykrobe.csv")


@pytest.fixture()
def mtuberculosis_quast_path(data_path: Path) -> Path:
    """Get path for mtuberculosis quast file"""
    return data_path.joinpath("mtuberculosis", "quast.tsv")


@pytest.fixture()
def mtuberculosis_tbprofiler_path(data_path: Path) -> Path:
    """Get path for mtuberculosis tbprofiler file"""
    return data_path.joinpath("mtuberculosis", "tbprofiler.json")


@pytest.fixture()
def mtuberculosis_snv_vcf_path(data_path: Path) -> Path:
    """Get path for mtuberculosis meta file"""
    return data_path.joinpath("mtuberculosis", "snv.vcf")


@pytest.fixture()
def mtuberculosis_sv_vcf_path(data_path: Path) -> Path:
    """Get path for mtuberculosis meta file"""
    return data_path.joinpath("mtuberculosis", "sv.vcf")


@pytest.fixture()
def mtuberculosis_delly_bcf_path(data_path: Path) -> Path:
    """Get path for mtuberculosis meta file"""
    return data_path.joinpath("mtuberculosis", "delly.bcf")


@pytest.fixture()
def converged_bed_path(data_path: Path) -> Path:
    """Get path for mtuberculosis converged who fohm tbdb bgzipped bed file"""
    return data_path.joinpath("mtuberculosis", "converged_who_fohm_tbdb.bed.gz")


@pytest.fixture()
def annotated_delly_path(data_path: Path) -> Path:
    """Get path for annotated delly vcf file"""
    return data_path.joinpath("mtuberculosis", "annotated_delly.vcf")
