"""Test functions for the resfinder parser."""

import json
from collections import Counter
from io import StringIO

import pytest

from bonsai_libs.parse.models.base import ElementTypeResult, ParserOutput, ResultEnvelope
from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.parsers.resfinder import ResFinderParser, get_nt_change


@pytest.mark.parametrize("source", ['{"phenotypes":', '{}', '[]'])
def test_invalid_resfinder_is_error(source):
    """Read and schema failures must mark both outputs as errors."""
    output = ResFinderParser().parse(StringIO(source))
    assert set(output.results) == {AnalysisType.AMR, AnalysisType.STRESS}
    for envelope in output.results.values():
        assert envelope.status == "error"
        assert envelope.reason
        assert envelope.value is None


def test_resfinder_without_findings_is_valid():
    output = ResFinderParser().parse(StringIO('{"phenotypes": {}}'))
    assert all(envelope.ok for envelope in output.results.values())


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


@pytest.mark.parametrize("organism", ["ecoli", "saureus"])
def test_gene_antibiotics_survive_serialization(data_path, organism):
    """Keep every hit's antibiotic associations through storage serialization."""
    path = data_path / organism / "resfinder.json"
    source = json.loads(path.read_text())
    output = ResFinderParser().parse(path, strict=True)
    result = output.results[AnalysisType.AMR].value
    stored = ElementTypeResult.model_validate_json(result.model_dump_json())

    expected = Counter(
        (hit["name"], hit["ref_acc"], tuple(sorted(hit["phenotypes"])))
        for hit in source["seq_regions"].values()
        if hit["ref_database"][0].startswith("Res") and hit.get("phenotypes")
    )
    actual = Counter(
        (gene["gene_symbol"], gene["accession"],
         tuple(sorted(phe["name"] for phe in gene["phenotypes"])))
        for gene in stored.genes
    )
    assert actual == expected
    assert stored.phenotypes == result.phenotypes
    assert len(stored.variants) == len(result.variants)
