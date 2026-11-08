"""Read stored Kaptive columns from the nested Kleborate report block."""
import csv

import pytest

from bonsai_libs.parse.models.enums import AnalysisType
from bonsai_libs.parse.parsers.kleborate import KleborateParser


@pytest.mark.parametrize('analysis_type,prefix', [(AnalysisType.K_TYPE, 'K'), (AnalysisType.O_TYPE, 'O')])
def test_saved_kaptive_columns(kp_kleborate_path, analysis_type, prefix):
    with kp_kleborate_path.open() as handle:
        row = next(csv.DictReader(handle, delimiter='\t'))
    columns = 'klebsiella_pneumo_complex__kaptive__' + prefix
    output = KleborateParser().parse(kp_kleborate_path, want={analysis_type})
    envelope = output.results[analysis_type]
    assert envelope.status == 'parsed', envelope.reason
    assert envelope.value.model_dump() == {
        'locus': row[columns + '_locus'], 'type': row[columns + '_type'],
        'identity': float(row[columns + '_locus_identity'].rstrip('%')) / 100,
        'confidence': row[columns + '_locus_confidence'].lower(),
        'problems': None if row[columns + '_locus_problems'] == '-' else row[columns + '_locus_problems'],
        'missing_genes': None if row[columns + '_Missing_expected_genes'] == '-' else row[columns + '_Missing_expected_genes'],
    }


def test_missing_kaptive_block_is_absent(kp_kleborate_path, tmp_path):
    with kp_kleborate_path.open() as handle:
        reader = csv.DictReader(handle, delimiter='\t')
        columns = [c for c in reader.fieldnames if '__kaptive__' not in c]
        rows = list(reader)
    target = tmp_path / 'without-kaptive.tsv'
    with target.open('w') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter='\t', extrasaction='ignore')
        writer.writeheader(); writer.writerows(rows)
    output = KleborateParser().parse(target, want={AnalysisType.K_TYPE, AnalysisType.O_TYPE})
    assert output.results[AnalysisType.K_TYPE].status == 'absent'
    assert output.results[AnalysisType.O_TYPE].status == 'absent'


def test_fractional_identity_is_preserved(kp_kleborate_path, tmp_path):
    with kp_kleborate_path.open() as handle:
        reader = csv.DictReader(handle, delimiter='\t'); columns = reader.fieldnames; rows = list(reader)
    for prefix in ['K', 'O']:
        rows[0]['klebsiella_pneumo_complex__kaptive__' + prefix + '_locus_identity'] = '0.875'
    target = tmp_path / 'fractional-identity.tsv'
    with target.open('w') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter='\t'); writer.writeheader(); writer.writerows(rows)
    output = KleborateParser().parse(target, want={AnalysisType.K_TYPE, AnalysisType.O_TYPE})
    for kind in [AnalysisType.K_TYPE, AnalysisType.O_TYPE]:
        assert output.results[kind].status == 'parsed'
        assert output.results[kind].value.identity == 0.875
