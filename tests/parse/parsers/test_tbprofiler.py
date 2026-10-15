"""Test parsing of TbProfiler results."""

import copy
import io
import json

import pytest

from bonsai_libs.parse.models.base import ElementTypeResult, ParserOutput, ResultEnvelope
from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.models.typing import LineageInformation
from bonsai_libs.parse.parsers.tbprofiler import TbProfilerParser


def test_tbprofier_parser_results(mtuberculosis_tbprofiler_path):
    """Test that the TbProfilerParser produces the expected result and data types."""

    parser = TbProfilerParser()
    result = parser.parse(mtuberculosis_tbprofiler_path)

    # test that result is method index
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    res = result.results[AnalysisType.AMR]
    assert isinstance(res, ResultEnvelope)
    assert res.status == "parsed"

    # test parser results
    assert isinstance(res.value, ElementTypeResult)

    res = result.results[AnalysisType.LINEAGE]
    assert isinstance(res, ResultEnvelope)
    assert res.status == "parsed"

    assert isinstance(res.value, list)
    assert isinstance(res.value[0], LineageInformation)


@pytest.mark.parametrize(
    "annotated_drugs,gene_drugs,expected_resistant",
    [
        (["amikacin"], ["amikacin", "capreomycin", "kanamycin"], ["amikacin"]),
        ([], ["amikacin", "capreomycin", "kanamycin"], []),
        (["kanamycin", "amikacin", "amikacin"], [], ["amikacin", "kanamycin"]),
        (["amikacin"], None, ["amikacin"]),
    ],
)
def test_resistance_summary_uses_variant_annotations(
    mtuberculosis_tbprofiler_path, annotated_drugs, gene_drugs, expected_resistant
):
    """Gene associations must not introduce or suppress variant resistance calls."""
    source = json.loads(mtuberculosis_tbprofiler_path.read_text())
    hit = copy.deepcopy(source["dr_variants"][0])
    hit["annotation"] = [
        {"type": "drug_resistance", "drug": drug} for drug in annotated_drugs
    ]
    if gene_drugs is None:
        hit.pop("gene_associated_drugs", None)
    else:
        hit["gene_associated_drugs"] = gene_drugs
    source["dr_variants"] = [hit]
    # These categories retain variant annotations but must not affect the summary.
    for category, drug in [("other_variants", "rifampicin"), ("qc_fail_variants", "isoniazid")]:
        excluded_hit = copy.deepcopy(hit)
        excluded_hit["annotation"] = [{"type": "drug_resistance", "drug": drug}]
        excluded_hit["gene_associated_drugs"] = [drug]
        source[category] = [excluded_hit]

    output = TbProfilerParser().parse(io.StringIO(json.dumps(source)))
    envelope = output.results[AnalysisType.AMR]

    assert envelope.status == "parsed"
    result = envelope.value
    assert result.phenotypes["resistant"] == expected_resistant
    assert {"capreomycin", "rifampicin", "isoniazid"} <= set(result.phenotypes["susceptible"])
    assert set(expected_resistant).isdisjoint(result.phenotypes["susceptible"])
    assert len(result.variants) == 3
    # Both the summary and drug-specific annotations survive API/storage serialization.
    stored = ElementTypeResult.model_validate_json(result.model_dump_json())
    assert stored.phenotypes == result.phenotypes
    assert [phe["name"] for phe in stored.variants[0]["phenotypes"]] == annotated_drugs
