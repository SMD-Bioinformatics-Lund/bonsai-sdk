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


@pytest.mark.parametrize("organism", ["ecoli", "saureus"])
def test_database_references_survive_serialization(data_path, organism):
    """Keep each gene and variant's source database through storage serialization."""
    path = data_path / organism / "resfinder.json"
    source = json.loads(path.read_text())
    output = ResFinderParser().parse(path, strict=True)
    result = output.results[AnalysisType.AMR].value
    stored = ElementTypeResult.model_validate_json(result.model_dump_json())

    expected_genes = Counter(
        (hit["name"], hit["ref_acc"], hit["ref_database"][0])
        for hit in source["seq_regions"].values()
        if hit["ref_database"][0].startswith("Res") and hit.get("phenotypes")
    )
    assert Counter(
        (gene["gene_symbol"], gene["accession"], gene.get("ref_database"))
        for gene in stored.genes
    ) == expected_genes

    expected_variants = Counter(
        (hit["seq_regions"][0].split(";;")[0], hit["ref_start_pos"], hit["ref_database"])
        for hit in source["seq_variations"].values()
    )
    assert Counter(
        (variant["reference_sequence"], variant["start"], variant.get("ref_database"))
        for variant in stored.variants
    ) == expected_variants


@pytest.mark.parametrize("as_list", [False, True])
def test_database_reference_string_and_list_formats(ecoli_resfinder_path, as_list):
    """Normalize both reference formats without reducing strings to one character."""
    source = json.loads(ecoli_resfinder_path.read_text())
    for hit in source["seq_regions"].values():
        reference = hit["ref_database"][0]
        hit["ref_database"] = [reference] if as_list else reference
    for hit in source["seq_variations"].values():
        reference = hit["ref_database"]
        hit["ref_database"] = [reference] if as_list else reference

    output = ResFinderParser().parse(StringIO(json.dumps(source)), strict=True)
    result = output.results[AnalysisType.AMR].value

    assert len(result.genes) == 17
    assert len(result.variants) == 4
    assert {gene.ref_database for gene in result.genes} == {"ResFinder-2.1.1"}
    assert {variant.ref_database for variant in result.variants} == {"PointFinder-4.0.0"}


@pytest.mark.parametrize("reference", [None, "", []])
def test_missing_variant_database_reference_remains_optional(ecoli_resfinder_path, reference):
    """Older outputs without database metadata still retain their variant findings."""
    source = json.loads(ecoli_resfinder_path.read_text())
    for hit in source["seq_variations"].values():
        hit.pop("ref_database")
        if reference is not None:
            hit["ref_database"] = reference

    output = ResFinderParser().parse(StringIO(json.dumps(source)), strict=True)
    result = output.results[AnalysisType.AMR].value

    assert len(result.variants) == 4
    assert all(variant.ref_database is None for variant in result.variants)
