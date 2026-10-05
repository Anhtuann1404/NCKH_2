import copy
import json
from pathlib import Path
import tempfile
import unittest

from dataclasses import asdict
from phishing.evaluation.metrics import binary_metrics
from phishing.training.config import load_config, validate_config
from phishing.training.report import summarize, write_report


class ExperimentReportTests(unittest.TestCase):
    def fixture(self):
        # Unequal fold sizes expose incorrect averaging of fold rates.
        index = [{'sample_id': str(i), 'label': label, 'group_id': f'g{i}'}
                 for i, label in enumerate([1, 0, 1, 1, 1, 0, 0, 0])]
        manifest = {'scope': 'synthetic_fixture_only', 'research_evidence': False,
                    'samples': 8, 'seeds': [17, 42], 'variants': ['M3'],
                    'outer_folds': 2, 'targets': [0.01]}
        predictions, reports = [], []
        for seed in manifest['seeds']:
            for number, part in enumerate((index[:2], index[2:])):
                scores = [float(number) for _ in part]
                reports.append({'seed': seed, 'variant': 'M3', 'fold': number,
                                'test_samples': len(part), 'test_ap': 0.5,
                                'operating_points': {'0.01': {
                                    'threshold': 0.5,
                                    'test': asdict(binary_metrics([r['label'] for r in part], scores, 0.5))}}})
                predictions.extend({**r, 'seed': seed, 'variant': 'M3', 'fold': number,
                                    'score': score, 'warnings': {'0.01': int(score >= 0.5)}}
                                   for r, score in zip(part, scores))
        return manifest, index, reports, predictions, []

    def test_aggregate_counts_not_mean_of_fold_rates_or_seed_pool(self):
        result = summarize(*self.fixture())
        self.assertEqual(len(result['rows']), 2)
        self.assertEqual(result['rows'][0]['metrics']['recall'], 0.75)
        self.assertEqual(result['rows'][0]['metrics']['fpr'], 0.75)
        self.assertEqual(result['rows'][0]['samples'], 8)
        self.assertEqual(result['seed_variation'][0]['unique_samples'], 8)

    def test_missing_threshold_does_not_estimate_on_partial_cohort(self):
        args = self.fixture()
        args[2][0]['operating_points']['0.01'] = {'threshold': None, 'test': None}
        for p in args[3]:
            if p['seed'] == 17 and p['fold'] == 0:
                p['warnings']['0.01'] = None
        result = summarize(*args)
        self.assertIsNone(result['rows'][0]['metrics'])
        self.assertEqual(result['rows'][0]['missing_decisions'], 2)
        self.assertIsNone(result['seed_variation'][0]['recall'])

    def test_duplicate_missing_or_changed_oof_rows_rejected(self):
        for mutation in ('duplicate', 'missing', 'label', 'group_id', 'decision'):
            with self.subTest(mutation=mutation):
                args = self.fixture()
                if mutation == 'duplicate':
                    args[3].append(copy.deepcopy(args[3][0]))
                elif mutation == 'missing':
                    args[3].pop()
                elif mutation == 'decision':
                    args[3][0]['warnings']['0.01'] = 1
                else:
                    args[3][0][mutation] = 'changed'
                with self.assertRaises(ValueError):
                    summarize(*args)

    def test_report_csv_and_markdown_and_no_overwrite(self):
        result = summarize(*self.fixture())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            hashes = write_report(output, result)
            self.assertEqual(len(hashes), 3)
            self.assertIn('NOT RESEARCH EVIDENCE', (output / 'report.md').read_text())
            self.assertEqual(json.loads((output / 'summary.json').read_text()), result)
            with self.assertRaises(FileExistsError):
                write_report(output, result)

    def test_config_scope_protocol_and_types_cannot_be_overridden(self):
        for field, value in (('scope', 'research'), ('research_evidence', True),
                             ('seeds', [42]), ('targets', [0.1]), ('groups', True),
                             ('bootstrap_repetitions', 1)):
            config = load_config()
            config[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_config(config)
        self.assertEqual(load_config(groups=20, repetitions=50)['groups'], 20)


if __name__ == '__main__':
    unittest.main()
