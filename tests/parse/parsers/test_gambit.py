"""Test gambit parsing."""

from bonsai_libs.parse.models.base import ParserOutput, ResultEnvelope
from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.models.qc import GambitcoreQcResult
from bonsai_libs.parse.parsers.gambit import GambitCoreParser


def test_gambit_parser(ecoli_gambitcore_path):
    """Test gambit parser."""
    parser = GambitCoreParser()
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
