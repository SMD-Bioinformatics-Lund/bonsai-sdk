"""Test functions for parsing ShigaTyper results."""

from io import StringIO

import pytest

from bonsai_libs.parse import hydrate_result, run_parser
from bonsai_libs.parse.models.base import ParserOutput, ResultEnvelope
from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.models.typing import TypingResultShigatyper
from bonsai_libs.parse.parsers.shigatyper import ShigatyperParser


def test_parse_shigatyper_results_with_hits(ecoli_shigatyper_path, ecoli_shigatyper_hits_path):
    """Test parsing of shigatyper result file together with its hits companion file."""

    parser = ShigatyperParser()
    result = parser.parse(ecoli_shigatyper_path, hits_path=ecoli_shigatyper_hits_path)

    assert isinstance(result, ParserOutput)

    res = result.results[AnalysisType.SHIGATYPE]
    assert isinstance(res, ResultEnvelope)
    assert res.status == "parsed"
    assert isinstance(res.value, TypingResultShigatyper)

    expected = {
        "prediction": "Not Shigella or EIEC",
        "ipaB": "-",
        "notes": "cmdtest2_260226_nb000000_0000_test is ipaH-.",
        "hits": [
            {"name": "EclacY", "n_reads": 1259},
            {"name": "cadA", "n_reads": 2571},
        ],
    }
    assert expected == res.value.model_dump()


def test_parse_shigatyper_results_without_hits(ecoli_shigatyper_path):
    """The hits companion file is optional; parsing should still succeed."""

    parser = ShigatyperParser()
    result = parser.parse(ecoli_shigatyper_path)

    res = result.results[AnalysisType.SHIGATYPE]
    assert res.value.prediction == "Not Shigella or EIEC"
    assert res.value.hits == []


@pytest.mark.parametrize("marker, expected", [("+", "+"), ("-", "-"), ("", None), ("NA", None)])
def test_shigatyper_preserves_marker_calls_through_hydration(marker, expected):
    source = StringIO(
        "sample\tprediction\tipaB\tnotes\n" f"s1\tShigella dysenteriae serotype 3\t{marker}\t\n"
    )
    output = run_parser("shigatyper", version="2.0.5", data=source)
    envelope = output.results[AnalysisType.SHIGATYPE]
    assert envelope.status == "parsed"
    restored = hydrate_result(
        software=output.software,
        analysis_type="shigatype",
        result=envelope.value.model_dump(mode="json"),
    )
    assert restored.ipaB == expected
    assert restored.notes is None


def test_invalid_shigatyper_marker_is_an_error():
    source = StringIO("sample\tprediction\tipaB\tnotes\ns1\tEIEC\tinvalid\t\n")
    envelope = ShigatyperParser().parse(source).results[AnalysisType.SHIGATYPE]
    assert envelope.status == "error"
