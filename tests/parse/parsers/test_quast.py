"""Test quast result parser."""

import pytest

from bonsai_libs.parse.models.base import ParserOutput, ResultEnvelope
from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.models.qc import QuastQcResult
from bonsai_libs.parse.parsers.quast import QuastParser


@pytest.mark.parametrize(
    "fixture_name",
    [
        ("saureus_quast_path"),
        ("mtuberculosis_quast_path"),
        ("kp_quast_path"),
        ("ecoli_quast_path"),
    ],
)
def test_quast_parser(fixture_name: str, request):
    """Test quast parser."""
    filename = request.getfixturevalue(fixture_name)

    # test parsing the output of an ecoli.
    parser = QuastParser()
    result = parser.parse(filename)

    # test that result is method index
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    qc = result.results[AnalysisType.QC]
    assert isinstance(qc, ResultEnvelope)
    assert isinstance(qc.value, QuastQcResult)
