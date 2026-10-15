"""Test parsing of Kleborate results."""

import logging
from io import StringIO
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
    """Test converting kleborate hAMRonization a bonsai_libs resistance record."""

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
            ParsedVariant(ref="Lys", start=28, residue="protein", type=VariantSubType.FRAME_SHIFT),
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
def test_parse_variant_str(variant: str, expected: ParsedVariant, warn_msg: str | None, caplog):
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
    (
        "kp_kleborate_path",
        {"k_type": "parsed", "o_type": "parsed", "amr": "error"},
    ),
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
    result = parser.parse(kp_kleborate_path, hamronization_source=kp_kleborate_hamronization_path)

    # test that result is method index
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    # AMR should be present
    res = result.results[AnalysisType.AMR]
    assert isinstance(res, ResultEnvelope)
    assert res.status == "parsed"
    assert isinstance(res.value, ElementTypeResult)
    assert len(res.value.genes) == 14
    assert len(res.value.variants) == 7
    assert res.value.genes[0].identity == 100.0
    assert all(gene.identity is not None for gene in res.value.genes)
    assert all(env.status == "parsed" for env in result.results.values())


def test_kaptive_loci_and_percentage_identity(kp_kleborate_path):
    """Read both loci from the nested Kaptive block and store fractional identity."""
    result = KleborateParser().parse(kp_kleborate_path)
    k_type = result.results[AnalysisType.K_TYPE]
    o_type = result.results[AnalysisType.O_TYPE]

    assert k_type.status == o_type.status == "parsed"
    assert k_type.value.locus == "KL107"
    assert k_type.value.type == "unknown (KL107)"
    assert k_type.value.identity == pytest.approx(0.9997)
    assert o_type.value.locus == "OL2α.2"
    assert o_type.value.type == "O2β"
    assert o_type.value.identity == pytest.approx(0.9917)


@pytest.mark.parametrize("identity,expected", [("100%", 1.0), ("0%", 0.0), ("99.97", 0.9997)])
def test_kaptive_identity_formats(kp_kleborate_path, identity, expected):
    source = StringIO(kp_kleborate_path.read_text().replace("99.97%", identity))
    result = KleborateParser().parse(source, want=AnalysisType.K_TYPE)

    assert result.results[AnalysisType.K_TYPE].status == "parsed"
    assert result.results[AnalysisType.K_TYPE].value.identity == pytest.approx(expected)


@pytest.mark.parametrize("identity", ["101%", "-1%", "invalid", "-"])
def test_bad_k_identity_preserves_o_typing(kp_kleborate_path, identity):
    source = StringIO(kp_kleborate_path.read_text().replace("99.97%", identity))
    result = KleborateParser().parse(source)

    assert result.results[AnalysisType.K_TYPE].status == "error"
    assert result.results[AnalysisType.O_TYPE].status == "parsed"
    assert result.results[AnalysisType.O_TYPE].value.type == "O2β"


def test_missing_kaptive_block_is_absent():
    source = StringIO(
        "strain\tklebsiella_pneumo_complex__virulence_score__virulence_score\nsample\t3\n"
    )
    result = KleborateParser().parse(source, want={AnalysisType.K_TYPE, AnalysisType.O_TYPE})

    assert all(env.status == "absent" for env in result.results.values() if env.status != "skipped")


def test_empty_amr_companion_has_no_findings(kp_kleborate_path, kp_kleborate_hamronization_path):
    header = kp_kleborate_hamronization_path.read_text().splitlines()[0]
    result = KleborateParser().parse(
        kp_kleborate_path, want=AnalysisType.AMR, hamronization_source=StringIO(header + "\n")
    )

    amr = result.results[AnalysisType.AMR]
    assert amr.status == "empty"
    assert amr.value.genes == []
    assert amr.value.variants == []


def test_invalid_amr_companion_preserves_error(kp_kleborate_path):
    result = KleborateParser().parse(
        kp_kleborate_path,
        want=AnalysisType.AMR,
        hamronization_source=StringIO("wrong\tcolumns\nbad\tdata\n"),
    )

    assert result.results[AnalysisType.AMR].status == "error"
