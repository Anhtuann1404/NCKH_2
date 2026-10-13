import hashlib
import json
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from phishing.training.experiment import fit_fold
from phishing.training.handoff import fold_from_c_grouped_split, inspect_c_split_artifacts
from phishing.training.synthetic import make_dataset
from phishing.preprocessing import prepare_snapshot


class CHandoffTests(unittest.TestCase):
    def setUp(self):
        self.samples, self.dictionary = make_dataset(20)
        ids = [sample.sample_id for sample in self.samples]
        provenance = {'input_sha256': 'a' * 64, 'group_rules_version': 'fixture-v1',
                      'psl_snapshot_sha256': 'b' * 64}
        self.groups = {'metadata': dict(provenance),
                       'sample_groups': {sample.sample_id: sample.group_id for sample in self.samples}}
        self.grouped = {'metadata': {**provenance, 'anti_leakage_verified': True, 'seeds': [17]},
                        'splits_by_seed': {'17': [{
                            'fold': 0, 'seed': 17, 'is_usable': True,
                            'class_sufficiency': {'status': 'sufficient'},
                            'train_indices': ids[:64], 'inner_train_indices': ids[:48],
                            'inner_val_indices': ids[48:64], 'test_indices': ids[64:],
                        }]}}

    def test_c_shape_runs_fixture_m0_m3_without_authorizing_real_training(self):
        fold = fold_from_c_grouped_split(self.samples, self.groups, self.grouped, seed=17, number=0)
        for variant in ('M0', 'M3'):
            _, report, predictions = fit_fold(self.samples, fold, variant, self.dictionary, candidates=(1.0,))
            self.assertEqual(report['test_samples'], 16)
            self.assertEqual(len(predictions), 16)

    def test_leaks_and_bad_inner_partition_are_rejected(self):
        altered = list(self.samples)
        altered[0] = replace(altered[0], snapshot=prepare_snapshot('https://example.org/', '<p>fixture</p>'))
        with self.assertRaisesRegex(ValueError, 'invented fixture'):
            fold_from_c_grouped_split(altered, self.groups, self.grouped, seed=17, number=0)
        with self.assertRaisesRegex(ValueError, 'Pilot/reserved'):
            fold_from_c_grouped_split(self.samples, self.groups, self.grouped, seed=17, number=0,
                                      excluded_ids=frozenset([self.samples[0].sample_id]))
        self.grouped['splits_by_seed']['17'][0]['inner_val_indices'] = [self.samples[0].sample_id]
        with self.assertRaisesRegex(ValueError, 'Inner partitions'):
            fold_from_c_grouped_split(self.samples, self.groups, self.grouped, seed=17, number=0)

    def test_artifact_hash_and_input_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            entries = {}
            for key, name, value in (('groups_json', 'groups.json', self.groups),
                                     ('grouped_5fold_splits_json', 'grouped_5fold_splits.json', self.grouped)):
                path = root / name
                path.write_text(json.dumps(value), encoding='utf-8')
                entries[key] = {'path': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'manifest_type': 'DATA-03_SPLIT_MANIFEST',
                                            'input_sha256': 'a' * 64, 'artifacts': entries}), encoding='utf-8')
            self.assertEqual(inspect_c_split_artifacts(manifest)[0]['sample_groups'], self.groups['sample_groups'])
            (root / 'groups.json').write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                inspect_c_split_artifacts(manifest)
            entries['groups_json']['path'] = '../outside.json'
            manifest.write_text(json.dumps({'manifest_type': 'DATA-03_SPLIT_MANIFEST',
                                            'input_sha256': 'a' * 64, 'artifacts': entries}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'escapes'):
                inspect_c_split_artifacts(manifest)
