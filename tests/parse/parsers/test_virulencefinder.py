"""Virulencefinder parser test suite."""

import importlib

import pytest

from bonsai_libs.parse.core.registry import get_parser
from bonsai_libs.parse.models.base import (
    ElementTypeResult,
    GeneWithReference,
    ParserOutput,
    ResultEnvelope,
)
from bonsai_libs.parse.models.enums import AnalysisType, ElementVirulenceSubtype
from bonsai_libs.parse.parsers import virulencefinder
from bonsai_libs.parse.parsers.virulencefinder import (
    VirulenceFinderParser,
    VirulenceFinderV2Parser,
)


@pytest.fixture()
def registered_parsers():
    """Re-register the parsers, which the autouse registry fixture clears."""
    return importlib.reload(virulencefinder)


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


def test_virulencefinder_v2_parser(ecoli_virulencefinder_v2_stx_path):
    """VirulenceFinder v2 output is parsed correctly."""

    parser = VirulenceFinderV2Parser()
    result = parser.parse(ecoli_virulencefinder_v2_stx_path, strict=True)

    assert isinstance(result, ParserOutput)
    assert all(at in parser.produces for at in result.results.keys())

    vir_res = result.results[AnalysisType.VIRULENCE]
    assert isinstance(vir_res, ResultEnvelope)
    assert vir_res.status == "parsed"

    assert isinstance(vir_res.value, ElementTypeResult)
    assert len(vir_res.value.genes) == 26

    # the dedicated stx assay is reported as a typing result, not as a virulence
    # gene; the stx entry of the virulence database itself is still listed
    symbols = [gene.gene_symbol for gene in vir_res.value.genes]
    assert "stx2" not in symbols
    assert "stx2c-O157-FLY16" in symbols

    stx_res = result.results[AnalysisType.STX]
    assert isinstance(stx_res, ResultEnvelope)
    assert stx_res.status == "parsed"

    assert isinstance(stx_res.value, GeneWithReference)
    assert stx_res.value.gene_symbol == "stx2"
    assert stx_res.value.accession == "AB015057"


def test_virulencefinder_v2_parser_no_stx(ecoli_virulencefinder_v2_no_stx_path):
    """A v2 stx assay without hits yields an empty stx result."""

    parser = VirulenceFinderV2Parser()
    result = parser.parse(ecoli_virulencefinder_v2_no_stx_path, strict=True)

    vir_res = result.results[AnalysisType.VIRULENCE]
    assert vir_res.status == "parsed"
    assert len(vir_res.value.genes) == 25

    stx_res = result.results[AnalysisType.STX]
    assert stx_res.status == "empty"
    assert stx_res.value is None


def test_virulencefinder_v2_parser_gene_fields(ecoli_virulencefinder_v2_stx_path):
    """v2 gene records are mapped onto the shared gene model."""

    parser = VirulenceFinderV2Parser()
    result = parser.parse(ecoli_virulencefinder_v2_stx_path, strict=True)

    genes = {gene.gene_symbol: gene for gene in result.results[AnalysisType.VIRULENCE].value.genes}

    # position_in_ref is split into start and end positions
    afa_a = genes["afaA"]
    assert afa_a.accession == "X76688"
    assert afa_a.sequence_name == "Transcriptional regulator"
    assert afa_a.ref_start_pos == 1
    assert afa_a.ref_end_pos == 307
    assert afa_a.ref_gene_length == 306
    assert afa_a.identity == 100.0
    assert afa_a.coverage == 100.0

    # genes without an accession report "NA", which is stored as null
    assert genes["fimH"].accession is None


def test_virulencefinder_v2_parser_subtypes(saureus_virulencefinder_v2_path):
    """Genes from a v2 toxin database are assigned the toxin subtype."""

    parser = VirulenceFinderV2Parser()
    result = parser.parse(saureus_virulencefinder_v2_path, strict=True)

    genes = result.results[AnalysisType.VIRULENCE].value.genes
    # s.aureus_hostimm reports "No hit found" and contributes no genes
    assert len(genes) == 14

    subtypes = [gene.element_subtype for gene in genes]
    assert subtypes.count(ElementVirulenceSubtype.TOXIN) == 11
    assert subtypes.count(ElementVirulenceSubtype.VIR) == 3


@pytest.mark.parametrize(
    "version,expected",
    [
        ("2.0.1", "VirulenceFinderV2Parser"),
        ("2.0.4", "VirulenceFinderV2Parser"),
        ("2.99.99", "VirulenceFinderV2Parser"),
        ("3.0.0", "VirulenceFinderParser"),
        ("3.2.0", "VirulenceFinderParser"),
    ],
)
def test_virulencefinder_version_dispatch(version, expected, registered_parsers):
    """The registry selects the parser matching the software version."""

    assert get_parser("virulencefinder", version=version).__name__ == expected


def test_virulencefinder_parser_rejects_v2_format(ecoli_virulencefinder_v2_stx_path):
    """A v2 file given to the v3 parser is reported as absent, not raised."""

    parser = VirulenceFinderParser()
    result = parser.parse(ecoli_virulencefinder_v2_stx_path)

    assert result.results[AnalysisType.VIRULENCE].status == "absent"
    assert result.results[AnalysisType.STX].status == "absent"
