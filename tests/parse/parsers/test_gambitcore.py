"""Test gambitcore parsing."""

import csv
from io import StringIO

import pytest

from bonsai_libs.parse.models.base import ParserOutput, ResultEnvelope
from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.models.qc import GambitcoreQcResult
from bonsai_libs.parse.parsers.gambitcore import GambitcoreParser


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


@pytest.mark.parametrize("assembly_qc", ["", "NA"])
def test_gambitcore_parser_accepts_missing_assembly_qc(ecoli_gambitcore_path, assembly_qc):
    with ecoli_gambitcore_path.open(newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        row = next(reader)

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(row), delimiter="\t")
    writer.writeheader()
    writer.writerow({**row, "Assembly QC": assembly_qc})
    output.seek(0)

    qc = GambitcoreParser().parse(output).results[AnalysisType.QC]

    assert qc.status == "parsed"
    assert isinstance(qc.value, GambitcoreQcResult)
    assert qc.value.assembly_qc is None
