"""Test gambitcore parsing."""

import csv
from io import StringIO

import pytest

from bonsai_libs.parse.core.registry import hydrate_result
from bonsai_libs.parse.models.base import ParserOutput, ResultEnvelope
from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.models.qc import GambitcoreQcResult
from bonsai_libs.parse.parsers.gambitcore import COLUMN_MAP, GambitcoreParser


def test_gambitcore_parser(tmp_path):
    """Test gambitcore parser."""
    path = tmp_path / "gambitcore.tsv"
    path.write_text(_assessment_tsv({}).getvalue(), encoding="utf-8")
    parser = GambitcoreParser()
    result = parser.parse(path)

    # test that result is method index
    assert isinstance(result, ParserOutput)
    assert result.parser_version == 2

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    qc = result.results[AnalysisType.QC]
    assert isinstance(qc, ResultEnvelope)
    assert qc.status == "parsed"

    assert isinstance(qc.value, GambitcoreQcResult)

    assert qc.value.scientific_name == "Escherichia coli"
    assert qc.value.assembly_core == 2852
    assert qc.value.species_core == 2864


def _assessment_tsv(overrides):
    row = dict.fromkeys(COLUMN_MAP, "NA")
    row.update(
        {
            "Species": "Escherichia coli",
            "Completeness (%)": "99.6%",
            "Assembly Core/species Core": "(2852/2864)",
            "Assembly QC": "green",
        }
    )
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(row), delimiter="\t")
    writer.writeheader()
    writer.writerow({**row, **overrides})
    output.seek(0)
    return output


def _parse_with_overrides(overrides):
    return GambitcoreParser().parse(_assessment_tsv(overrides)).results[AnalysisType.QC]


@pytest.mark.parametrize("assembly_qc", ["", "NA"])
def test_gambitcore_parser_accepts_missing_assembly_qc(assembly_qc):
    qc = _parse_with_overrides({"Assembly QC": assembly_qc})

    assert qc.status == "parsed"
    assert isinstance(qc.value, GambitcoreQcResult)
    assert qc.value.assembly_qc is None


def test_gambitcore_parser_preserves_skipped_assessment():
    reason = "Species could not be identified, skipping core genome assessment"
    row = dict.fromkeys(COLUMN_MAP, "NA")
    row["Species"] = reason
    qc = _parse_with_overrides(row)

    assert qc.status == "parsed"
    assert isinstance(qc.value, GambitcoreQcResult)
    assert qc.value.scientific_name is None
    stored = qc.value.model_dump(mode="json", exclude_none=True)
    assert stored == {}
    hydrated = hydrate_result(software="gambitcore", analysis_type=AnalysisType.QC, result=stored)
    assert hydrated == qc.value


@pytest.mark.parametrize("species", ["", "NA"])
def test_gambitcore_parser_accepts_missing_scientific_name(species):
    qc = _parse_with_overrides({"Species": species})

    assert qc.status == "parsed"
    assert qc.value.scientific_name is None


@pytest.mark.parametrize("column", ["Completeness (%)", "Assembly Core/species Core"])
def test_gambitcore_parser_rejects_malformed_assessment(column):
    qc = _parse_with_overrides({column: "invalid"})

    assert qc.status == "error"
    if column == "Assembly Core/species Core":
        assert qc.reason == "Invalid Gambitcore core counts 'invalid'. Expected '(assembly/species)'."
