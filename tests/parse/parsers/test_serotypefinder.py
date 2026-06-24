"""Test Serotypefinder parser."""

import pytest

from bonsai_libs.parse.models.base import GeneBase, ParserOutput, ResultEnvelope
from bonsai_libs.parse.parsers.serotypefinder import SerotypeFinderParser, _is_no_hit


def test_serotypefinder_parser(ecoli_serotypefinder_path):
    """Test parsing of serotypefinder result file."""

    # test parsing the output of saureus.
    parser = SerotypeFinderParser()
    result = parser.parse(ecoli_serotypefinder_path)

    # assert correct ouptut data model
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    # verify that h_type hit was parsed.
    hres = result.results["h_type"]
    assert isinstance(hres, ResultEnvelope)
    assert hres.status == "parsed"
    assert isinstance(hres.value, GeneBase)

    # verify that the expected no o_type hit was correctly handled.
    ores = result.results["o_type"]
    assert isinstance(ores, ResultEnvelope)
    assert ores.status == "absent"


@pytest.mark.parametrize(
    "value,expected",
    [("No hit!", True), ("", True), (None, True), ({}, True), ({"GENE": {}}, False)],
)
def test_is_no_hit(value, expected):
    """Test function that checks wether it was a serotypefinder hit."""
    assert _is_no_hit(value) == expected
