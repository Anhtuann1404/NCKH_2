import unittest
from dataclasses import replace
from sklearn.base import clone
from phishing.preprocessing import prepare_snapshot
from phishing.training.synthetic import make_dataset
from phishing.training.pipeline import make_pipeline, SnapshotNumeric, rule_scores
from phishing.training.experiment import fit_fold
from phishing.evaluation.grouped import make_folds
from phishing.evaluation.bootstrap import paired_bootstrap, resample_group_indices
import numpy as np


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.samples, self.dictionary = make_dataset(20)
        self.fold = make_folds(self.samples, seeds=(17,))[0]

    def test_fixed_group_folds_coverage_and_reproducibility(self):
        folds = make_folds(self.samples, seeds=(17, 42))
        self.assertEqual(folds, make_folds(self.samples, seeds=(17, 42)))
        for seed in (17, 42):
            self.assertEqual(sorted(i for f in folds if f.seed == seed for i in f.test), list(range(len(self.samples))))
        for f in folds:
            groups = [{self.samples[i].group_id for i in part} for part in (f.train, f.validation, f.test)]
            self.assertFalse(groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2])

    def test_reserved_and_duplicate_samples_rejected(self):
        with self.assertRaises(ValueError):
            make_folds(self.samples, excluded_ids=frozenset([self.samples[0].sample_id]))
        with self.assertRaises(ValueError):
            make_folds(self.samples + [self.samples[0]])

    def test_fit_rejects_overlapping_supplied_fold(self):
        bad = replace(self.fold, validation=self.fold.train)
        with self.assertRaises(ValueError):
            fit_fold(self.samples, bad, 'M2', self.dictionary)

    def test_m0_cannot_use_a_different_missing_html_cohort(self):
        changed = list(self.samples)
        i = self.fold.test[0]
        changed[i] = replace(changed[i], snapshot=prepare_snapshot(changed[i].snapshot.url))
        with self.assertRaises(ValueError):
            fit_fold(changed, self.fold, 'M0', self.dictionary)

    def test_train_only_vocabulary_and_scaler(self):
        X = [self.samples[i].snapshot for i in self.fold.train]
        y = [self.samples[i].label for i in self.fold.train]
        model = clone(make_pipeline('M2', self.dictionary)).fit(X, y)
        probe = prepare_snapshot('https://new.fixture.test/', '<p>validationcanarytoken</p>')
        model.predict_proba([probe])
        branches = dict(model.named_steps['features'].transformer_list)
        self.assertNotIn('validationcanarytoken', branches['word'].named_steps['tfidf'].vocabulary_)
        self.assertEqual(branches['numeric'].named_steps['scale'].n_samples_seen_, len(X))

    def test_test_labels_cannot_change_fit_or_threshold(self):
        altered = [replace(s, label=1-s.label) if i in self.fold.test else s for i, s in enumerate(self.samples)]
        _, a, pa = fit_fold(self.samples, self.fold, 'M2', self.dictionary)
        _, b, pb = fit_fold(altered, self.fold, 'M2', self.dictionary)
        self.assertEqual(a['C'], b['C'])
        self.assertEqual(a['validation_ap'], b['validation_ap'])
        self.assertEqual([r['score'] for r in pa], [r['score'] for r in pb])
        self.assertEqual([r['warnings'] for r in pa], [r['warnings'] for r in pb])

    def test_shared_text_features_and_ablation_shapes(self):
        X = [self.samples[i].snapshot for i in self.fold.train]
        y = [self.samples[i].label for i in self.fold.train]
        m2 = make_pipeline('M2', self.dictionary).fit(X, y)
        m3 = make_pipeline('M3', self.dictionary).fit(X, y)
        for name in ('word', 'char'):
            left = dict(m2.named_steps['features'].transformer_list)[name].named_steps['tfidf']
            right = dict(m3.named_steps['features'].transformer_list)[name].named_steps['tfidf']
            self.assertEqual(left.vocabulary_, right.vocabulary_)
            np.testing.assert_equal(left.idf_, right.idf_)
        full = SnapshotNumeric('M3', self.dictionary).transform(X).shape[1]
        for block, width in (('organization', 2), ('domain', 4), ('intention', 3)):
            self.assertEqual(SnapshotNumeric('M3-no-' + block, self.dictionary).transform(X).shape[1], full-width)

    def test_metadata_and_missing_html_rejected(self):
        with self.assertRaises(TypeError):
            SnapshotNumeric().transform([{'url': 'https://a.test/', 'label': 1}])
        with self.assertRaises(ValueError):
            SnapshotNumeric('M2').transform([prepare_snapshot('https://a.test/')])

    def test_all_variants_and_rule_are_runnable(self):
        for variant in ('M0', 'M1', 'M2', 'M3', 'M3-no-organization', 'M3-no-domain', 'M3-no-intention', 'B-rule'):
            _, report, rows = fit_fold(self.samples, self.fold, variant, self.dictionary, candidates=(1.0,))
            self.assertEqual(len(rows), len(self.fold.test))
            self.assertTrue(0 <= report['test_ap'] <= 1)


class BootstrapTests(unittest.TestCase):
    def test_resampling_keeps_whole_groups_with_multiplicity(self):
        indices = resample_group_indices(['a', 'a', 'b', 'b', 'b'], np.random.default_rng(17))
        self.assertEqual(indices.count(0), indices.count(1))
        self.assertEqual(indices.count(2), indices.count(3))
        self.assertEqual(indices.count(3), indices.count(4))

    def test_identical_predictions_have_zero_difference(self):
        result = paired_bootstrap([0, 1, 0, 1], ['a', 'a', 'b', 'b'], [0, 1, 0, 1], [0, 1, 0, 1], repetitions=30)
        self.assertEqual(result['recall']['ci95'], [0.0, 0.0])
        self.assertEqual(result['fpr']['undefined_replicates'], 0)

    def test_undefined_replicates_are_counted_and_reproducible(self):
        args = ([0, 1], ['a', 'b'], [0, 1], [0, 1])
        result = paired_bootstrap(*args, repetitions=50)
        self.assertEqual(result, paired_bootstrap(*args, repetitions=50))
        self.assertGreater(result['recall']['undefined_replicates'], 0)
        self.assertEqual(result['recall']['valid_replicates'] + result['recall']['undefined_replicates'], 50)

    def test_missing_or_misaligned_decisions_rejected(self):
        with self.assertRaises(ValueError):
            paired_bootstrap([0, 1], ['a', 'b'], [0, None], [0, 1])
        with self.assertRaises(ValueError):
            paired_bootstrap([0, 1], ['a', 'b'], [0], [0, 1])


if __name__ == '__main__':
    unittest.main()
