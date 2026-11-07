"""Generic input/selection regressions; no analysis tools are executed."""

from io import StringIO
import pytest
from bonsai_libs.parse import run_parser
from bonsai_libs.parse.models.enums import AnalysisType


@pytest.mark.parametrize('kind',[AnalysisType.SPECIES,AnalysisType.LINEAGE])
def test_mykrobe_selected_result_does_not_require_another_result(kind):
    text=('sample,mykrobe_version,drug,susceptibility,genotype_model,variants,species,species_per_covg,phylo_group,phylo_group_per_covg,lineage\n'
          'generic,0.12.2,,,,,Generic_label,99,Generic_group,99,label.1\n')
    result=run_parser('mykrobe',version='0.12.2',data=StringIO(text),want={kind})
    assert str(result.results[kind].status)=='parsed'
    assert all(str(envelope.status)=='skipped' for other,envelope in result.results.items() if other!=kind)
    assert result.results[kind].meta['step']==kind


def test_header_only_bracken_report_is_empty_with_list_shape():
    text='name\ttaxonomy_id\ttaxonomy_lvl\tkraken_assigned_reads\tadded_reads\tnew_est_reads\tfraction_total_reads\n'
    result=run_parser('bracken',version='2.8.0',data=StringIO(text)).results[AnalysisType.SPECIES]
    assert str(result.status)=='empty'
    assert result.value==[]


def test_samtools_coverage_retains_all_rows_from_stream_and_path(tmp_path):
    text=('#rname\tstartpos\tendpos\tnumreads\tcovbases\tcoverage\tmeandepth\tmeanbaseq\tmeanmapq\n'
          'Generic one\t1\t100\t0\t0\t0\t0\t0\t0\nGeneric two\t1\t100\t10\t50\t50\t5\t30\t60\n')
    path=tmp_path/'coverage.tsv';path.write_text(text)
    values=[]
    for source in [path,StringIO(text)]:
        envelope=run_parser('samtools',subcommand='coverage',version='1.0.0',data=source).results[AnalysisType.QC]
        assert str(envelope.status)=='parsed'
        assert len(envelope.value.contigs)==2
        assert envelope.value.contigs[0].n_reads==0
        values.append(envelope.value.model_dump())
    assert values[0]==values[1]
