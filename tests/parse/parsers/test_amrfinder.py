"""Virulencefinder parser test suite."""

import pytest

from bonsai_libs.parse.models.base import (
    ElementTypeResult,
    ParserOutput,
    ResultEnvelope,
)
from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.parsers.amrfinder import AmrFinderParser

EXPECTED_RESULT = [
    (
        "saureus_amrfinder_path",
        (
            8,
            3,
            (
                "beta-lactam",
                "fosfomycin",
                "methicillin",
                "quinolone",
                "tetracycline",
                "tigecycline",
            ),
        ),
    ),
    ("saureus_amrfinder_no_amr_path", (0, 0, tuple())),
]


EXPECTED_AMRFINDER_RESULT = [
    (
        "saureus_amrfinder_path",
        (
            14,  # virulence genes
            8,  # amr genes
            3,  # amr variants
            (
                "beta-lactam",
                "fosfomycin",
                "methicillin",
                "quinolone",
                "tetracycline",
                "tigecycline",
            ),
        ),
    ),
    ("saureus_amrfinder_no_amr_path", (0, 0, 0, tuple())),
]


@pytest.mark.parametrize("fixture_name,expected", EXPECTED_AMRFINDER_RESULT)
def test_amrfinder_parser_results(fixture_name, expected, request):
    """Test parsing amrfinder resistance."""
    exp_vir_genes, exp_genes, exp_variants, exp_phenotypes = expected
    filename = request.getfixturevalue(fixture_name)

    # parse result
    parser = AmrFinderParser()
    result = parser.parse(source=filename)

    # test that result is method index
    assert isinstance(result, ParserOutput)

    # test that result contain the expected types
    result_types = list(result.results.keys())
    assert all(method in result_types for method in parser.produces)

    # test that all virulence genes were parsed
    vir = result.results["virulence"]
    assert isinstance(vir, ResultEnvelope)
    assert isinstance(vir.value, ElementTypeResult)
    assert len(vir.value.genes) == exp_vir_genes

    # test that all genes, variants, and phenotypes are identified
    res = result.results["amr"]
    assert isinstance(res, ResultEnvelope)
    assert isinstance(res.value, ElementTypeResult)

    assert len(res.value.genes) == exp_genes
    assert len(res.value.variants) == exp_variants
    assert set(res.value.phenotypes["resistant"]) == set(exp_phenotypes)


def test_amrfinder_parser_filter(saureus_amrfinder_path):
    """Test that filtering of AMRfinder results works."""
    selected_result = AnalysisType.AMR
    parser = AmrFinderParser()
    result = parser.parse(saureus_amrfinder_path, want=selected_result)

    res = result.results[selected_result]
    assert res.status == "parsed"
