"""Test functions for parsing NanoPlot results."""

from bonsai_libs.parse.models.base import ParserOutput, ResultEnvelope
from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.models.qc import NanoPlotQcResult
from bonsai_libs.parse.parsers.nanoplot import NanoplotParser


def test_parse_nanoplot_results(saureus_nanoplot_path):
    """Test parsing of NanoPlot result file."""

    parser = NanoplotParser()
    result = parser.parse(saureus_nanoplot_path)

    # test that result is method index
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    res = result.results[AnalysisType.QC]
    assert isinstance(res, ResultEnvelope)
    assert res.status == "parsed"

    # test parser result
    assert isinstance(res.value, NanoPlotQcResult)

    # Test parsing the output
    expected_summary = {
        "mean_read_length": 4697.8,
        "mean_read_quality": 13.2,
        "median_read_length": 2814.0,
        "median_read_quality": 15.2,
        "n_reads": 1000.0,
        "read_length_n50": 6893.0,
        "stdev_read_length": 5845.6,
        "total_bases": 4697845.0,
    }

    # Check if data matches
    assert expected_summary == res.value.summary.model_dump()
    assert len(res.value.top_longest) == 5
    assert len(res.value.top_quality) == 5
