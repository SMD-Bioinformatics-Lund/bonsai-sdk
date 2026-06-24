"""Test functions for parsing spaTyper results."""

from bonsai_libs.parse.models.base import ParserOutput, ResultEnvelope
from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.models.typing import TypingResultSpatyper
from bonsai_libs.parse.parsers.spatyper import SpatyperParser


def test_parse_spatyper_results(saureus_spatyper_path):
    """Test parsing of spatyper result file."""

    parser = SpatyperParser()
    result = parser.parse(saureus_spatyper_path)

    # assert correct ouptut data model
    assert isinstance(result, ParserOutput)

    # check if data matches
    res = result.results[AnalysisType.SPATYPE]
    assert isinstance(res, ResultEnvelope)
    assert res.status == "parsed"

    assert isinstance(res.value, TypingResultSpatyper)

    expected_spatyper = {
        "sequence_name": "contig_1",
        "repeats": "15-12-16-02-16-02-25-17-24",
        "type": "t021",
    }
    assert expected_spatyper == res.value.model_dump()
