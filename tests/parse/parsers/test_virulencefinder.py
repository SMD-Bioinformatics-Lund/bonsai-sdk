"""Virulencefinder parser test suite."""

from bonsai_libs.parse.models.base import (
    ElementTypeResult,
    GeneWithReference,
    ParserOutput,
    ResultEnvelope,
)
from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.parsers.virulencefinder import VirulenceFinderParser


def test_virulencefinder_parser(ecoli_virulencefinder_stx_pred_stx_path):
    """Test parsing of virulencefinder stx typing prediction."""

    parser = VirulenceFinderParser()
    result = parser.parse(ecoli_virulencefinder_stx_pred_stx_path, strict=True)

    # assert correct ouptut data model
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    # test that all genes are identified
    vir_res = result.results[AnalysisType.VIRULENCE]
    assert isinstance(vir_res, ResultEnvelope)
    assert vir_res.status == "parsed"

    assert isinstance(vir_res.value, ElementTypeResult)
    assert len(vir_res.value.genes) == 29

    # test STX prediction returns the expected results
    stx_res = result.results[AnalysisType.STX]
    assert isinstance(stx_res, ResultEnvelope)
    assert stx_res.status == "parsed"

    assert isinstance(stx_res.value, GeneWithReference)
    assert stx_res.value.gene_symbol == "stx2"
