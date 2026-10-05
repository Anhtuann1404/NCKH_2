import unittest

from phishing.evaluation.metrics import binary_metrics, select_validation_threshold
from phishing.training.plan import RunPlan


class EvaluationTests(unittest.TestCase):
    def test_counts_and_inclusive_threshold(self):
        result = binary_metrics([1, 1, 0, 0], [0.8, 0.3, 0.8, 0.1], 0.8)
        self.assertEqual((result.tp, result.fn, result.fp, result.tn), (1, 1, 1, 1))
        self.assertEqual((result.recall, result.fpr, result.precision, result.f1), (0.5, 0.5, 0.5, 0.5))

    def test_undefined_metrics_remain_none(self):
        result = binary_metrics([0, 0], [0.1, 0.2], 0.9)
        self.assertIsNone(result.recall)
        self.assertIsNone(result.precision)
        self.assertIsNone(result.f1)
        self.assertEqual(result.fpr, 0)

    def test_threshold_respects_false_positive_ties(self):
        point = select_validation_threshold([1, 1, 0, 0], [0.9, 0.7, 0.7, 0.2], 0.0)
        self.assertEqual(point.threshold, 0.9)
        self.assertEqual(point.validation_metrics.recall, 0.5)
        self.assertEqual(point.validation_metrics.fpr, 0)

    def test_recall_tie_selects_higher_threshold(self):
        point = select_validation_threshold([1, 0, 0], [0.9, 0.8, 0.1], 0.5)
        self.assertEqual(point.threshold, 0.9)

    def test_impossible_threshold_and_missing_classes_are_explicit(self):
        self.assertIsNone(select_validation_threshold([1, 0], [1.0, 1.0], 0.01))
        with self.assertRaises(ValueError):
            select_validation_threshold([0, 0], [0.1, 0.2], 0.01)
        for scores in ([float('nan'), 0.2], [float('inf'), 0.2], [True, 0.2], [-0.1, 0.2]):
            with self.subTest(scores=scores), self.assertRaises(ValueError):
                binary_metrics([0, 1], scores, 0.5)

    def test_split_plan_rejects_group_and_sample_overlap(self):
        good = RunPlan('M2', 17, ('train',), ('val',), ('test',))
        self.assertEqual(good.validate({'train': 'g1', 'val': 'g2', 'test': 'g3'})['samples'], [1, 1, 1])
        with self.assertRaises(ValueError):
            good.validate({'train': 'same', 'val': 'g2', 'test': 'same'})
        with self.assertRaises(ValueError):
            RunPlan('M2', 17, ('train',), ('val',), ('train',)).validate({'train': 'g1', 'val': 'g2'})

    def test_pilot_exclusion_and_missing_groups_are_rejected(self):
        plan = RunPlan('M3', 42, ('train',), ('val',), ('test',))
        with self.assertRaises(ValueError):
            plan.validate({'train': 'g1', 'val': 'g2', 'test': 'g3'}, frozenset({'test'}))
        with self.assertRaises(ValueError):
            plan.validate({'train': 'g1', 'val': 'g2'})


if __name__ == '__main__':
    unittest.main()
