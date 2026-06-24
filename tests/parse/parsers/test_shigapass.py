"""Test functions for parsing Shigapass results."""

from typing import Any

import pytest

from bonsai_libs.parse.models.base import ParserOutput, ResultEnvelope
from bonsai_libs.parse.parsers.shigapass import ShigapassParser, extract_percentage

EXPECTED_SHIGA_OUTPUT = [
    (
        "ecoli_shigapass_path",
        {
            "rfb": None,
            "rfb_hits": 0.0,
            "mlst": None,
            "flic": None,
            "crispr": None,
            "ipah": "ipaH-",
            "predicted_serotype": "Not Shigella/EIEC",
            "predicted_flex_serotype": None,
            "comments": None,
        },
    ),
    (
        "shigella_shigapass_path",
        {
            "rfb": "C2",
            "rfb_hits": 48.2,
            "mlst": "ST145",
            "flic": "ShH57(ShH3cplx)",
            "crispr": "A-var2",
            "ipah": "ipaH+",
            "predicted_serotype": "SB2",
            "predicted_flex_serotype": None,
            "comments": None,
        },
    ),
]


@pytest.mark.parametrize(
    "input,expected",
    [
        ("79,(48.2%)", 48.2),
        ("79,(48.0%)", 48.0),
        ("79,(48%)", 48.0),
        ("NA,(0.0%)", 0.0),
        ("NA,(0%)", 0.0),
    ],
)
def test_extract_percentage(input: str, expected: float):
    """Test extracting percentages from a string."""

    assert extract_percentage(input) == expected


@pytest.mark.parametrize("fixture_name,expected_result", EXPECTED_SHIGA_OUTPUT)
def test_parse_shigapass_results(fixture_name: str, expected_result: dict[str, Any], request):
    """Test parsing of shigapass result files."""
    filename = request.getfixturevalue(fixture_name)
    # test parsing the output of an ecoli.
    parser = ShigapassParser()
    result = parser.parse(filename)

    # test that result is method index
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    # check if data matches
    pred = result.results["shigatype"]
    assert isinstance(pred, ResultEnvelope)
    assert pred.status == "parsed"

    assert expected_result == pred.value.model_dump()
