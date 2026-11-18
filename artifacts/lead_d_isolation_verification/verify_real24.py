"""Local restricted-file audit; emits aggregate checks only and never fits a model."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import zipfile

from phishing.training.plan import RunPlan
from phishing.training.readiness import check_run_plan_isolation, check_training_inputs, load_isolated_ids, sha256

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / 'scripts/check_training_inputs.py').is_file())
spec = importlib.util.spec_from_file_location('fixture_cli', ROOT / 'scripts/check_training_inputs.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pack', required=True, type=Path)
pack = parser.parse_args().pack
assert sha256(pack) == 'e0bb55e8be1e0d9bad996bcdfbc2b1401bcbfcdcf207fec78b9219cc3961bd12'
checks = {'real_runplan_rejections': 0, 'real_readiness_rejections': 0, 'positive_controls': 0}
with tempfile.TemporaryDirectory(prefix='nckh-real24-restricted-') as temp:
    root = Path(temp)
    with zipfile.ZipFile(pack) as archive:
        for line in archive.read('SHA256SUMS.txt').decode().splitlines():
            expected, name = line.split(maxsplit=1)
            assert hashlib.sha256(archive.read(name)).hexdigest() == expected
        files = []
        for suffix in ('json', 'csv'):
            name = 'clean_calibration_runway_a_labels_final.' + suffix
            path = root / name
            path.write_bytes(archive.read(name))
            files.append((path, sha256(path)))
    rows = json.loads(files[0][0].read_text())['records']
    assert len(rows) == 24
    binary_eligible = sum(row.get('binary_model_eligible') is True for row in rows)
    for path, digest in files:
        ids = load_isolated_ids(path, digest)
        assert len(ids) == 24
        groups = {'control-train': 'g1', 'control-val': 'g2', 'control-test': 'g3'}
        groups.update({sid: 'reserved-' + str(i) for i, sid in enumerate(ids)})
        control = [('control-train',), ('control-val',), ('control-test',)]
        assert check_run_plan_isolation(RunPlan('M0', 17, *control), groups,
                                       label_artifacts=[(path, digest)])['samples'] == [1, 1, 1]
        checks['positive_controls'] += 1
        for sid in ids:
            for partition in range(3):
                parts = control.copy()
                parts[partition] = (sid,)
                try:
                    check_run_plan_isolation(RunPlan('M0', 17, *parts), groups,
                                             label_artifacts=[(path, digest)])
                except ValueError as exc:
                    assert str(exc) == 'Pilot/reserved samples entered the run plan'
                    checks['real_runplan_rejections'] += 1
                else:
                    raise AssertionError('Reserved record was accepted')
    fixture_root = root / 'fixture'
    fixture_root.mkdir()
    for row in rows:
        for position in (0, 2, 4):
            manifest_path = cli.write_demo_inputs(fixture_root)
            manifest = json.loads(manifest_path.read_text())
            for artifact in ('labels', 'index'):
                path = fixture_root / (artifact + '.json')
                data = json.loads(path.read_text())
                # Carry the real isolation metadata into a valid input contract;
                # preserve fixture identity so other validation cannot mask the guard.
                for key in ('dataset_split', 'excluded_from_model_training',
                            'excluded_from_model_validation', 'excluded_from_official_test'):
                    data[position][key] = row[key]
                path.write_text(json.dumps(data))
                manifest['artifacts'][artifact]['sha256'] = sha256(path)
            manifest_path.write_text(json.dumps(manifest))
            try:
                check_training_inputs(manifest_path)
            except ValueError as exc:
                assert str(exc) == 'Isolated sample entered input cohort'
                checks['real_readiness_rejections'] += 1
            else:
                raise AssertionError('Loader accepted a reserved record')
    manifest_path = cli.write_demo_inputs(fixture_root)
    assert check_training_inputs(manifest_path)['research_training_allowed'] is False
    checks['positive_controls'] += 1
    manifest = json.loads(manifest_path.read_text())
    manifest['scope'] = 'research'
    manifest_path.write_text(json.dumps(manifest))
    try:
        check_training_inputs(manifest_path)
    except ValueError as exc:
        assert str(exc).startswith('Research inputs blocked')
        checks['research_scope_blocked'] = True
    else:
        raise AssertionError('Research was authorized')
    checks.update({'records': 24, 'binary_eligible_but_blocked': binary_eligible,
                   'label_hashes': {path.suffix: digest for path, digest in files},
                   'models_fitted': 0, 'training_blocked': True})
assert checks['real_runplan_rejections'] == 144
assert checks['real_readiness_rejections'] == 72
print(json.dumps(checks, indent=2))
