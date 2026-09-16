"""Test quast result parser."""

import pathlib

import pytest

from bonsai_libs.parse.models.base import ParserOutput, ResultEnvelope
from bonsai_libs.parse.models.enums import AnalysisType, ResultStatus
from bonsai_libs.parse.models.qc import QuastQcResult
from bonsai_libs.parse.parsers.quast import QuastParser


@pytest.mark.parametrize(
    "fixture_name",
    [
        ("saureus_quast_path"),
        ("mtuberculosis_quast_path"),
        ("kp_quast_path"),
        ("ecoli_quast_path"),
    ],
)
def test_quast_parser(fixture_name: str, request):
    """Test quast parser."""
    filename = request.getfixturevalue(fixture_name)

    # test parsing the output of an ecoli.
    parser = QuastParser()
    result = parser.parse(filename)

    # test that result is method index
    assert isinstance(result, ParserOutput)

    # verify that parser produces what it say it should
    assert all(at in parser.produces for at in result.results.keys())

    qc = result.results[AnalysisType.QC]
    assert isinstance(qc, ResultEnvelope)
    assert isinstance(qc.value, QuastQcResult)


def test_quast_parser_without_reference_genome(saureus_quast_path, tmp_path):
    """Species without a reference genome get a quast report with no reference columns."""
    reference_columns = {
        "Reference length", "Reference GC (%)", "Duplication ratio", "NG50",
    }
    rows = [line.split("\t") for line in
            pathlib.Path(saureus_quast_path).read_text().splitlines() if line]
    keep = [i for i, name in enumerate(rows[0]) if name not in reference_columns]
    no_reference = tmp_path / "quast.tsv"
    no_reference.write_text(
        "\n".join("\t".join(row[i] for i in keep) for row in rows) + "\n"
    )

    result = QuastParser().parse(str(no_reference))
    qc = result.results[AnalysisType.QC]

    assert qc.status == ResultStatus.PARSED, qc.reason
    assert isinstance(qc.value, QuastQcResult)
    assert qc.value.total_length > 0
    assert qc.value.reference_length is None
    assert qc.value.reference_gc is None
    assert qc.value.duplication_ratio is None
    assert qc.value.ng50 is None
    # the reference metrics are dropped on the way to the database, not stored as nulls
    assert set(qc.value.model_dump(exclude_none=True)) == {
        "total_length", "largest_contig", "n_contigs", "n50", "assembly_gc",
    }
