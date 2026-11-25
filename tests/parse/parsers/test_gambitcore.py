"""Test gambitcore parsing."""

import csv
from io import StringIO

import pytest

from bonsai_libs.parse.models.base import ParserOutput, ResultEnvelope
from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.models.qc import GambitcoreQcResult
from bonsai_libs.parse.parsers.gambitcore import COLUMN_MAP, GambitcoreParser


def test_gambitcore_parser(ecoli_gambitcore_path):
    """Test gambitcore parser."""
    parser = GambitcoreParser()
    result = parser.parse(ecoli_gambitcore_path)

    # test that result is method index
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    qc = result.results[AnalysisType.QC]
    assert isinstance(qc, ResultEnvelope)
    assert qc.status == "parsed"

    assert isinstance(qc.value, GambitcoreQcResult)

    assert qc.value.assembly_core == 2852
    assert qc.value.species_core == 2864


def _parse_with_overrides(path, overrides):
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        row = next(reader)

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(row), delimiter="\t")
    writer.writeheader()
    writer.writerow({**row, **overrides})
    output.seek(0)
    return GambitcoreParser().parse(output).results[AnalysisType.QC]


@pytest.mark.parametrize("assembly_qc", ["", "NA"])
def test_gambitcore_parser_accepts_missing_assembly_qc(ecoli_gambitcore_path, assembly_qc):
    qc = _parse_with_overrides(ecoli_gambitcore_path, {"Assembly QC": assembly_qc})

    assert qc.status == "parsed"
    assert isinstance(qc.value, GambitcoreQcResult)
    assert qc.value.assembly_qc is None


def test_gambitcore_parser_preserves_skipped_assessment(ecoli_gambitcore_path):
    reason = "Species could not be identified, skipping core genome assessment"
    row = dict.fromkeys(COLUMN_MAP, "NA")
    row["Species"] = reason
    qc = _parse_with_overrides(ecoli_gambitcore_path, row)

    assert qc.status == "parsed"
    assert isinstance(qc.value, GambitcoreQcResult)
    assert qc.value.model_dump(exclude_none=True) == {"scientific_name": reason}
    assert GambitcoreQcResult.model_validate({"scientific_name": reason}) == qc.value


@pytest.mark.parametrize("column", ["Completeness (%)", "Assembly Core/species Core"])
def test_gambitcore_parser_rejects_malformed_assessment(ecoli_gambitcore_path, column):
    qc = _parse_with_overrides(ecoli_gambitcore_path, {column: "invalid"})

    assert qc.status == "error"
