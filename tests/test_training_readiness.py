import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from phishing.training.readiness import check_training_inputs, sha256

spec = importlib.util.spec_from_file_location('check_inputs_cli', Path(__file__).resolve().parents[1] / 'scripts/check_training_inputs.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class TrainingReadinessTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.manifest = cli.write_demo_inputs(self.root)

    def change(self, name, mutate):
        path = self.root / f'{name}.json'
        content = json.loads(path.read_text())
        mutate(content)
        path.write_text(json.dumps(content), encoding='utf-8')
        manifest = json.loads(self.manifest.read_text())
        manifest['artifacts'][name]['sha256'] = sha256(path)
        self.manifest.write_text(json.dumps(manifest), encoding='utf-8')

    def test_valid_fixture_never_authorizes_research(self):
        result = check_training_inputs(self.manifest)
        self.assertEqual(result['samples'], [2, 2, 2])
        self.assertFalse(result['research_training_allowed'])
        content = json.loads(self.manifest.read_text())
        content['scope'] = 'research'
        self.manifest.write_text(json.dumps(content))
        with self.assertRaisesRegex(ValueError, 'Research inputs blocked'):
            check_training_inputs(self.manifest)

    def test_hash_and_html_tampering(self):
        (self.root / 'fixture.html').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'HTML checksum'):
            check_training_inputs(self.manifest)
        self.manifest = cli.write_demo_inputs(self.root)
        (self.root / 'labels.json').write_text('[]')
        with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
            check_training_inputs(self.manifest)

    def test_group_leakage_and_reserved_ids(self):
        self.change('groups', lambda rows: rows.update({'fixture-2': 'fixture-group-0'}))
        with self.assertRaisesRegex(ValueError, 'Group overlap'):
            check_training_inputs(self.manifest)
        self.manifest = cli.write_demo_inputs(self.root)
        self.change('exclusion', lambda rows: rows['excluded_ids'].append('fixture-0'))
        with self.assertRaisesRegex(ValueError, 'Pilot/reserved'):
            check_training_inputs(self.manifest)

    def test_unknown_labels_and_duplicate_ids(self):
        self.change('labels', lambda rows: rows[0].update(class_label='unknown'))
        with self.assertRaisesRegex(ValueError, 'Final binary'):
            check_training_inputs(self.manifest)
        self.manifest = cli.write_demo_inputs(self.root)
        self.change('index', lambda rows: rows.append(dict(rows[0])))
        with self.assertRaisesRegex(ValueError, 'unique sample'):
            check_training_inputs(self.manifest)

    def test_partition_classes_and_missing_members(self):
        self.change('labels', lambda rows: rows[0].update(class_label='phishing'))
        with self.assertRaisesRegex(ValueError, 'both classes'):
            check_training_inputs(self.manifest)
        self.manifest = cli.write_demo_inputs(self.root)
        self.change('groups', lambda rows: rows.pop('fixture-0'))
        with self.assertRaisesRegex(ValueError, 'do not match'):
            check_training_inputs(self.manifest)

    def test_excluded_cohort_and_path_escape(self):
        self.change('index', lambda rows: rows[0].update(exclusion_reason='pilot'))
        with self.assertRaisesRegex(ValueError, 'Excluded sample'):
            check_training_inputs(self.manifest)
        self.manifest = cli.write_demo_inputs(self.root)
        self.change('index', lambda rows: rows[0].update(html_path='../outside.html'))
        with self.assertRaisesRegex(ValueError, 'escapes'):
            check_training_inputs(self.manifest)
