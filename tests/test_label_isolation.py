"""Exercise file-to-ID exclusion through the real RunPlan, without fitting models."""
import csv
import json
from dataclasses import replace

import pytest

from phishing.training.plan import RunPlan
from phishing.training.readiness import check_run_plan_isolation, load_isolated_ids, sha256


@pytest.fixture(params=['json', 'csv'])
def labels(tmp_path, request):
    path = tmp_path / ('labels.' + request.param)
    rows = [{'sample_id': 'reserved-case', 'dataset_split': 'calibration_offline_excluded',
             'excluded_from_model_training': True, 'excluded_from_model_validation': True,
             'excluded_from_official_test': True}]
    if request.param == 'json':
        path.write_text(json.dumps({'records': rows}))
    else:
        with path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return path


def test_real_runplan_rejects_every_partition_and_accepts_control(labels):
    groups = {'train': 'g1', 'val': 'g2', 'test': 'g3', 'reserved-case': 'g4'}
    plan = RunPlan('M0', 17, ('train',), ('val',), ('test',))
    artifacts = [(labels, sha256(labels))]
    assert load_isolated_ids(*artifacts[0]) == frozenset({'reserved-case'})
    assert check_run_plan_isolation(plan, groups, label_artifacts=artifacts)['samples'] == [1, 1, 1]
    for field in ('train_ids', 'validation_ids', 'test_ids'):
        with pytest.raises(ValueError, match='Pilot/reserved'):
            check_run_plan_isolation(replace(plan, **{field: ('reserved-case',)}), groups,
                                     label_artifacts=artifacts)


def test_tampered_label_file_is_rejected_before_runplan(labels):
    expected = sha256(labels)
    with labels.open('a') as stream:
        stream.write('\n')
    with pytest.raises(ValueError, match='checksum mismatch'):
        load_isolated_ids(labels, expected)


@pytest.mark.parametrize('change', [
    lambda r: r.pop('excluded_from_model_training'),
    lambda r: r.update(excluded_from_model_training='false'),
    lambda r: r.update(excluded_from_official_test=0),
    lambda r: r.update(sample_id=''),
])
def test_invalid_isolation_metadata_cannot_silently_drop_exclusions(tmp_path, change):
    row = {'sample_id': 'reserved', 'dataset_split': 'calibration_isolated',
           'excluded_from_model_training': True, 'excluded_from_model_validation': True,
           'excluded_from_official_test': True}
    change(row)
    path = tmp_path / 'labels.json'
    path.write_text(json.dumps([row]))
    with pytest.raises(ValueError):
        load_isolated_ids(path, sha256(path))
