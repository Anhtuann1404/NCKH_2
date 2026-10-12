import unittest
from dataclasses import replace

from phishing.training.experiment import fit_fold
from phishing.training.synthetic import make_dataset
from phishing.training.temporal import fold_from_temporal_split


class TemporalHandoffTests(unittest.TestCase):
    def setUp(self):
        self.samples, self.dictionary = make_dataset(20)
        ids = [sample.sample_id for sample in self.samples]
        self.split = {
            'status': 'evaluable',
            'train_indices': ids[:48], 'val_indices': ids[48:64], 'test_indices': ids[64:],
            'purged_val_indices': [], 'purged_test_indices': [],
            'cutoffs': {'train_cutoff_date': '2025-01-12', 'val_cutoff_date': '2025-01-16'},
        }
        self.dates = {sample.sample_id: f'2025-01-{i // 4 + 1:02d}' for i, sample in enumerate(self.samples)}

    def test_fixture_runs_both_models_without_real_data(self):
        fold = fold_from_temporal_split(self.samples, self.split, self.dates)
        for variant in ('M0', 'M3'):
            _, report, rows = fit_fold(self.samples, fold, variant, self.dictionary, candidates=(1.0,))
            self.assertEqual(report['test_samples'], 16)
            self.assertEqual(len(rows), 16)

    def test_unusable_or_leaking_splits_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'not evaluable'):
            fold_from_temporal_split(self.samples, {**self.split, 'status': 'not_evaluable'}, self.dates)
        with self.assertRaisesRegex(ValueError, 'Purged'):
            fold_from_temporal_split(self.samples, {**self.split, 'purged_test_indices': [self.split['test_indices'][0]]}, self.dates)
        with self.assertRaisesRegex(ValueError, 'Pilot/reserved'):
            fold_from_temporal_split(self.samples, self.split, self.dates,
                                     excluded_ids=frozenset([self.split['train_indices'][0]]))
        altered = list(self.samples)
        altered[48] = replace(altered[48], group_id=altered[0].group_id)
        with self.assertRaisesRegex(ValueError, 'Group overlap'):
            fold_from_temporal_split(altered, self.split, self.dates)

    def test_future_dates_and_changed_cutoff_fail_closed(self):
        dates = dict(self.dates)
        dates[self.split['train_indices'][0]] = '2025-03-01'
        with self.assertRaisesRegex(ValueError, 'strictly ordered'):
            fold_from_temporal_split(self.samples, self.split, dates)
        with self.assertRaisesRegex(ValueError, 'cutoffs'):
            fold_from_temporal_split(self.samples, {**self.split, 'cutoffs': {'train_cutoff_date': '2025-01-11', 'val_cutoff_date': '2025-01-16'}}, self.dates)

    def test_cutoff_can_follow_last_unpurged_validation_day(self):
        split = {**self.split, 'val_indices': self.split['val_indices'][:-4],
                 'purged_val_indices': self.split['val_indices'][-4:]}
        fold = fold_from_temporal_split(self.samples, split, self.dates)
        self.assertEqual(len(fold.validation), 12)
