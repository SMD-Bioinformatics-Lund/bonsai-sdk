"""Test parsing of MSLT results."""

from bonsai_libs.parse.models.base import ParserOutput, ResultEnvelope
from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.models.typing import TypingResultMlst
from bonsai_libs.parse.parsers.mlst import MlstParser


def test_parse_mlst_result(ecoli_mlst_path):
    """Test parsing of MLST result file."""

    parser = MlstParser()
    result = parser.parse(ecoli_mlst_path)

    # assert correct ouptut data model
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    res = result.results[AnalysisType.MLST]
    assert isinstance(res, ResultEnvelope)
    assert res.status == "parsed"

    assert isinstance(res.value, TypingResultMlst)

    # THEN verify sequence type and allele assignment
    assert res.value.sequence_type == 58
    assert len(res.value.alleles) == 8


def test_parse_mlst_result_w_no_call(mlst_result_path_no_call):
    """Test parsing of MLST results file where the alleles was not called."""
    parser = MlstParser()
    result = parser.parse(mlst_result_path_no_call)

    # THEN verify that sequence type is None
    res = result.results[AnalysisType.MLST]
    assert isinstance(res, ResultEnvelope)
    assert res.status == "absent"
