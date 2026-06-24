"""Test functions for parsing SCCmec results."""

from bonsai_libs.parse.models.base import ParserOutput, ResultEnvelope
from bonsai_libs.parse.models.typing import TypingResultSccmec
from bonsai_libs.parse.parsers.sccmec import SccMecParser


def test_parse_sccmec_results(saureus_sccmec_path):
    """Test parsing of spatyper result file."""

    # test parsing the output of saureus.
    parser = SccMecParser()
    result = parser.parse(saureus_sccmec_path)

    # assert correct ouptut data model
    assert isinstance(result, ParserOutput)

    res = result.results["sccmec"]
    assert isinstance(res, ResultEnvelope)
    assert isinstance(res.value[0], TypingResultSccmec)

    expected_sccmec = {
        "camlhmp_version": "1.1.0",
        "type": "IV",
        "subtype": "multiple",
        "mecA": "+",
        "target_schema": "sccmec_targets",
        "target_schema_version": "1.2.0",
        "targets": [
            "ccrA2",
            "ccrB2",
            "IS431",
            "IS431_1",
            "IS431_2",
            "IS1272",
            "mecA",
            "mecR1",
        ],
        "regions": ["IVa", "IVn"],
        "coverage": [96.31, 83.93],
        "hits": [27, 25],
        "target_comment": None,
        "region_schema": "sccmec_regions",
        "region_schema_version": "1.2.0",
        "region_comment": "Found matches for multiple types including: IVa, IVn",
        "comment": "The type was determined based on matches to multiple subtypes of the same type",
    }

    # check if data matches
    assert expected_sccmec == res.value[0].model_dump()
