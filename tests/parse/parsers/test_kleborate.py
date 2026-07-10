"""Test parsing of Kleborate results."""

import logging
from pathlib import Path

import pytest

from bonsai_libs.parse.models.base import (
    ElementTypeResult,
    ParserOutput,
    PhenotypeInfo,
    ResultEnvelope,
)
from bonsai_libs.parse.models.enums import AnalysisType, ElementType, VariantSubType
from bonsai_libs.parse.models.hamronization import HamronizationEntry
from bonsai_libs.parse.models.kleborate import ParsedVariant
from bonsai_libs.parse.parsers.kleborate import (
    KleborateParser,
    _hamr_phenotype,
    _parse_amr,
    _parse_variant_str,
)


def test_convert_hamronization_to_amr_record(hamronization_entry: HamronizationEntry):
    """Test converting kleborate hAMRonization a PRP resistance record."""

    res = _parse_amr([hamronization_entry], warn=lambda x: x)

    # Test that result in strucutred data
    assert isinstance(res, ElementTypeResult)

    # No variants in test data
    assert len(res.variants) == 0

    # No gene in test data
    gene = res.genes[0]
    assert gene.gene_symbol == hamronization_entry.gene_symbol


def test_get_hamr_phenotype(hamronization_entry: HamronizationEntry):
    """Test building phenotype info."""

    info = _hamr_phenotype(hamronization_entry)

    # Test that result in strucutred data
    assert isinstance(info, PhenotypeInfo)

    # Test that fields were assigned correctly
    assert info.type == ElementType.AMR
    assert info.group == "aminoglycoside antibiotic"
    assert info.name == "aminoglycoside antibiotic"


@pytest.mark.parametrize(
    "variant,expected,warn_msg",
    [
        (
            "p.Leu35Gln",
            ParsedVariant(
                ref="Leu",
                alt="Gln",
                start=35,
                residue="protein",
                type=VariantSubType.SUBSTITUTION,
            ),
            None,
        ),
        (
            "p.134_135insGlyAsp",
            ParsedVariant(
                ref="",
                alt="GlyAsp",
                start=134,
                end=135,
                residue="protein",
                type=VariantSubType.INSERTION,
            ),
            None,
        ),
        (
            "p.Lys28fs",
            ParsedVariant(
                ref="Lys", start=28, residue="protein", type=VariantSubType.FRAME_SHIFT
            ),
            None,
        ),
        (
            "c.T68del",
            ParsedVariant(
                ref="T",
                alt="",
                start=68,
                residue="nucleotide",
                type=VariantSubType.DELETION,
            ),
            None,
        ),
        ("c.T68foo", None, None),
        (None, None, None),
    ],
)
def test_parse_variant_str(
    variant: str, expected: ParsedVariant, warn_msg: str | None, caplog
):
    """Test parsing of HGVS-like string."""

    with caplog.at_level(logging.WARNING):
        result = _parse_variant_str(variant)
        assert result == expected

        if warn_msg:
            assert any(warn_msg in message for message in caplog.messages)


TEST_ASSAYS_WO_HAMRONIZATION = [
    (
        "ecoli_kleborate_path",
        {
            "k_type": "absent",
            "abst": "absent",
            "amr": "error",
            "cbst": "absent",
            "o_type": "absent",
            "qc": "parsed",
            "rmst": "absent",
            "smst": "absent",
            "species_prediction": "parsed",
            "virulence": "absent",
            "ybst": "absent",
        },
    ),
    ("kp_kleborate_path", {}),
]


@pytest.mark.parametrize("fixture_name,expected", TEST_ASSAYS_WO_HAMRONIZATION)
def test_parse_kleborate_output_wo_hamronization(
    fixture_name: str, expected: dict[str, str], request
):
    """Test parsing of kleborate output without hAMRonization."""

    filename = request.getfixturevalue(fixture_name)

    parser = KleborateParser()
    result = parser.parse(filename)

    # test that result is method index
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    for atype, exp_status in expected.items():
        res = result.results.get(atype)
        assert isinstance(res, ResultEnvelope)
        assert res.status == exp_status


def test_kleborate_parser_results_w_hamronization(
    kp_kleborate_path: Path, kp_kleborate_hamronization_path: Path
):
    """Test that the KleborateParser produces the expected result and data types."""

    parser = KleborateParser()
    result = parser.parse(
        kp_kleborate_path, hamronization_source=kp_kleborate_hamronization_path
    )

    # test that result is method index
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    # AMR should be present
    res = result.results[AnalysisType.AMR]
    assert isinstance(res, ResultEnvelope)
    assert res.status == "parsed"
    assert isinstance(res.value, ElementTypeResult)
