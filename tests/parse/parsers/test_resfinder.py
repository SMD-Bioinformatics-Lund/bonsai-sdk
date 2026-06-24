"""Test functions for the resfinder parser."""

from bonsai_libs.parse.models.base import ParserOutput, ResultEnvelope
from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.parsers.resfinder import ResFinderParser, get_nt_change


def test_get_nt_changes_from_condons():
    """Test extraction of changed nucleotides from codons."""

    ref_codon = "tcg"
    alt_codon = "ttg"

    ref_nt, alt_nt = get_nt_change(ref_codon, alt_codon)

    assert ref_nt == "C" and alt_nt == "T"


def test_resfinder_parser(ecoli_resfinder_path):
    """Test the resfinder parser."""

    parser = ResFinderParser()
    result = parser.parse(ecoli_resfinder_path, strict=True)

    # assert correct ouptut data model
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    # test that all genes and varaints are identified
    amr_res = result.results[AnalysisType.AMR]
    assert isinstance(amr_res, ResultEnvelope)
    assert amr_res.status == "parsed"

    assert len(amr_res.value.genes) == 17
    assert len(amr_res.value.variants) == 4
