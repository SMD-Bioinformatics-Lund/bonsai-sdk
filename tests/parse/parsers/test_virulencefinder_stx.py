"""Preserve complete STX typing evidence alongside the legacy summary hit."""

import json
from copy import deepcopy
from io import StringIO
from types import SimpleNamespace

import pytest

from bonsai_libs.parse import hydrate_result
from bonsai_libs.parse.models.base import GeneWithReference
from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.parsers.virulencefinder import (
    VirulenceFinderParser,
    VirulenceFinderV2Parser,
)


@pytest.fixture(params=[2, 3], ids=["v2", "v3"])
def stx_case(request, data_path):
    """Replace STX candidates to isolate multi-hit retention and ranking."""
    version = request.param
    filename = "virulencefinder.v2.stx.json" if version == 2 else "virulencefinder.stx_pred.stx.json"
    pred = json.loads((data_path / "ecoli" / filename).read_text())
    if version == 2:
        hits = next(iter(pred["virulencefinder"]["results"].values()))["stx"]
        template = deepcopy(next(iter(hits.values())))
        hits.clear()
        parser = VirulenceFinderV2Parser()
    else:
        phenotype = deepcopy(pred["phenotypes"].pop("stx2"))
        template = pred["seq_regions"].pop(phenotype["seq_regions"][0])
        pred["phenotypes"].pop("stx2c-O157-FLY16")
        parser = VirulenceFinderParser()

    def add(symbol, accession, coverage=100.0, identity=100.0):
        record = deepcopy(template)
        record.update(coverage=coverage, identity=identity)
        if version == 2:
            record.update(virulence_gene=symbol, accession=accession, hit_id=accession)
            hits[accession] = record
        else:
            record.update(name=symbol, ref_acc=accession, key=accession, phenotypes=[symbol])
            pred["seq_regions"][accession] = record
            if symbol not in pred["phenotypes"]:
                pred["phenotypes"][symbol] = {
                    **deepcopy(phenotype), "key": symbol, "seq_regions": [],
                }
            pred["phenotypes"][symbol]["seq_regions"].append(accession)

    return SimpleNamespace(
        version=version, pred=pred, add=add,
        parse=lambda: parser.parse(StringIO(json.dumps(pred)), strict=True),
    )


@pytest.mark.parametrize("identity", [99.0, 100.0])
def test_distinct_stx_types_survive_parsing_and_json(stx_case, identity):
    stx_case.add("stx2", "stx2-reference")
    stx_case.add("stx1", "stx1-reference", identity=identity)
    result = stx_case.parse()
    stx = result.results[AnalysisType.STX]

    assert stx.status == "parsed"
    assert isinstance(stx.value, GeneWithReference)
    assert stx.value.gene_symbol == "stx2"
    assert {hit.gene_symbol for hit in stx.value.hits} == {"stx1", "stx2"}
    assert len(stx.value.hits) == 2
    virulence = result.results[AnalysisType.VIRULENCE].value.genes
    if stx_case.version == 2:
        assert "stx2c-O157-FLY16" in [gene.gene_symbol for gene in virulence]
    assert not {"stx1", "stx2"} & {gene.gene_symbol for gene in virulence}

    wire = json.loads(result.model_dump_json())["results"]["stx"]["value"]
    hydrated = hydrate_result(software="virulencefinder", analysis_type="stx", result=wire)
    assert [hit.accession for hit in hydrated.hits] == ["stx1-reference", "stx2-reference"]
    assert all(isinstance(hit, GeneWithReference) for hit in hydrated.hits)


def test_multiple_candidates_for_one_type_are_retained(stx_case):
    stx_case.add("stx2", "first-allele", coverage=90, identity=100)
    stx_case.add("stx2", "second-allele", coverage=100, identity=98)
    result = stx_case.parse().results[AnalysisType.STX]

    assert result.value.accession == "second-allele"
    assert {hit.accession for hit in result.value.hits} == {"first-allele", "second-allele"}


def test_primary_summary_keeps_version_specific_ranking(stx_case):
    stx_case.add("stx1", "stx1-reference", coverage=99, identity=100)
    stx_case.add("stx2", "stx2-reference", coverage=100, identity=99)
    result = stx_case.parse().results[AnalysisType.STX]

    assert result.value.gene_symbol == ("stx2" if stx_case.version == 2 else "stx1")
    assert len(result.value.hits) == 2


def test_string_scores_are_ranked_numerically(stx_case):
    stx_case.add("stx1", "partial-match", coverage="9", identity="100")
    stx_case.add("stx1", "complete-match", coverage="100", identity="99")
    result = stx_case.parse().results[AnalysisType.STX]

    assert result.value.accession == "complete-match"
    assert len(result.value.hits) == 2


def test_zero_score_hit_is_not_silently_discarded(stx_case):
    stx_case.add("stx1", "zero-score-reference", coverage=0, identity=0)
    result = stx_case.parse().results[AnalysisType.STX]

    assert result.status == "parsed"
    assert result.value.hits[0].accession == "zero-score-reference"


def test_no_stx_candidates_is_empty(stx_case):
    result = stx_case.parse().results[AnalysisType.STX]

    assert result.status == "empty"
    assert result.value is None


def test_legacy_single_hit_can_be_hydrated(stx_case):
    stx_case.add("stx1", "legacy-reference")
    legacy = stx_case.parse().results[AnalysisType.STX].value.model_dump(exclude={"hits"})
    result = hydrate_result(software="virulencefinder", analysis_type="stx", result=legacy)

    assert isinstance(result, GeneWithReference)
    assert result.gene_symbol == "stx1"
    assert [hit.accession for hit in result.hits] == ["legacy-reference"]


def test_shared_v3_region_is_reported_once(ecoli_virulencefinder_stx_pred_stx_path):
    pred = json.loads(ecoli_virulencefinder_stx_pred_stx_path.read_text())
    pred["phenotypes"]["stx2-alias"] = deepcopy(pred["phenotypes"]["stx2"])
    result = VirulenceFinderParser().parse(StringIO(json.dumps(pred)))

    hits = result.results[AnalysisType.STX].value.hits
    assert [hit.gene_symbol for hit in hits] == ["stx2", "stx2c-O157-FLY16"]


def test_missing_v3_region_does_not_discard_available_hits(ecoli_virulencefinder_stx_pred_stx_path):
    pred = json.loads(ecoli_virulencefinder_stx_pred_stx_path.read_text())
    pred["phenotypes"]["stx1"] = {
        **deepcopy(pred["phenotypes"]["stx2"]), "seq_regions": ["missing-region"],
    }
    result = VirulenceFinderParser().parse(StringIO(json.dumps(pred)))
    stx = result.results[AnalysisType.STX]

    assert stx.status == "parsed"
    assert [hit.gene_symbol for hit in stx.value.hits] == ["stx2", "stx2c-O157-FLY16"]


def test_v3_keeps_name_based_stx_selection(ecoli_virulencefinder_stx_pred_stx_path):
    """General-database STX findings remain eligible without dedicated hits."""
    pred = json.loads(ecoli_virulencefinder_stx_pred_stx_path.read_text())
    pred["phenotypes"].pop("stx2")
    result = VirulenceFinderParser().parse(StringIO(json.dumps(pred)), strict=True)
    stx = result.results[AnalysisType.STX]

    assert stx.status == "parsed"
    assert stx.value.gene_symbol == "stx2c-O157-FLY16"
    assert [hit.gene_symbol for hit in stx.value.hits] == ["stx2c-O157-FLY16"]
    virulence = result.results[AnalysisType.VIRULENCE].value.genes
    assert "stx2c-O157-FLY16" in [gene.gene_symbol for gene in virulence]
