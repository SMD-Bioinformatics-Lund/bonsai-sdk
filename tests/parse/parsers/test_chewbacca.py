"""Test typing method parsing."""

import pytest

from bonsai_libs.parse.models.base import ParserOutput, ResultEnvelope
from bonsai_libs.parse.models.enums import AnalysisType, ChewbbacaErrors
from bonsai_libs.parse.models.typing import TypingResultCgMlst
from bonsai_libs.parse.parsers.chewbacca import ChewbbacaParser, replace_cgmlst_errors

# build test cases for handeling chewbacca allele caller errors and annotations
# reference, https://chewbbaca.readthedocs.io/en/latest/user/modules/AlleleCall.html
cgmlst_test_base = [("1", 1), ("99", 99)]  # normal alllale calls
cgmlst_test_include_novel = [
    ("INF-1", 1),
    ("INF-99", 99),
    ("*1", 1),
    ("*99", 99),
]  # inferred alleles
cgmlst_test_not_include_novel = [
    ("INF-1", "INF-1"),
    ("INF-99", "INF-99"),
]  # inferred alleles
cgmlst_test_replace_errors = [(err.value, None) for err in ChewbbacaErrors]  # errors to strip
cgmlst_test_not_replace_errors = [
    (err.value, err.value) for err in ChewbbacaErrors
]  # errors to strip


@pytest.mark.parametrize(
    "called_allele,expected",
    [
        *cgmlst_test_base,
        *cgmlst_test_not_include_novel,
        *cgmlst_test_not_replace_errors,
    ],
)
def test_replace_cgmlst_errors_not_include_novel(called_allele, expected):
    """Test function that process Chewbbaca allele calling."""

    res = replace_cgmlst_errors(called_allele, include_novel_alleles=False, correct_alleles=False)
    assert res == expected


@pytest.mark.parametrize(
    "called_allele,expected",
    [*cgmlst_test_base, *cgmlst_test_include_novel, *cgmlst_test_not_replace_errors],
)
def test_replace_cgmlst_errors_include_novel(called_allele, expected):
    """Test function that process Chewbbaca allele calling."""

    res = replace_cgmlst_errors(called_allele, include_novel_alleles=True, correct_alleles=False)
    assert res == expected


@pytest.mark.parametrize(
    "called_allele,expected",
    [*cgmlst_test_base, *cgmlst_test_include_novel, *cgmlst_test_replace_errors],
)
def test_replace_cgmlst_errors_include_novel_and_correct_allels(called_allele, expected):
    """Test function that process Chewbbaca allele calling."""

    res = replace_cgmlst_errors(called_allele, include_novel_alleles=True, correct_alleles=True)
    assert res == expected


def test_chewbbaca_parser(saureus_chewbbaca_path):
    """Test ChewbbacaParser."""

    parser = ChewbbacaParser()
    result = parser.parse(saureus_chewbbaca_path)

    # assert correct ouptut data model
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    res = result.results[AnalysisType.CGMLST]
    assert isinstance(res, ResultEnvelope)
    assert res.status == "parsed"

    assert isinstance(res.value, TypingResultCgMlst)
