import copy
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from phishing.evaluation.error_analysis import analyze, analyze_run


def fixture():
    index = [{'sample_id': f's{i}', 'label': i % 2, 'group_id': f'g{i // 2}'} for i in range(6)]
    manifest = {'scope': 'synthetic_fixture_only', 'research_evidence': False,
                'samples': 6, 'seeds': [17, 42], 'outer_folds': 3, 'targets': [0.01, 0.05]}
    folds, reports, predictions = [], [], []
    for seed in manifest['seeds']:
        for f in range(3):
            parts = [[i for i in range(6) if i // 2 == (f + offset) % 3] for offset in (1, 2, 0)]
            folds.append(dict(seed=seed, number=f, train=parts[0], validation=parts[1], test=parts[2]))
            for variant in ('M2', 'M3'):
                reports.append(dict(seed=seed, fold=f, variant=variant,
                                    operating_points={str(t): {'threshold': 0.5, 'test': {}} for t in manifest['targets']}))
                for i in parts[2]:
                    correct = ((f == 0 and variant == 'M3') or (f == 1 and variant == 'M2') or (f == 2 and i % 2 == 0))
                    warning = index[i]['label'] if correct else 1 - index[i]['label']
                    predictions.append({**index[i], 'seed': seed, 'fold': f, 'variant': variant,
                                        'score': 0.9 if warning else 0.1,
                                        'warnings': {str(t): warning for t in manifest['targets']}})
    return manifest, index, folds, reports, predictions


class ErrorAnalysisTests(unittest.TestCase):
    def test_corrected_regressed_and_fp_fn_separate_by_seed_target(self):
        errors, summary = analyze(*fixture())
        self.assertEqual(len(summary['summaries']), 4)
        self.assertEqual(summary['unique_samples'], 6)
        for row in summary['summaries']:
            self.assertEqual(row['categories'], {'m3_corrected': 2, 'm3_regressed': 2,
                                                'both_wrong': 1, 'both_correct': 1, 'missing_operating_point': 0})
            self.assertEqual(row['model_errors']['M2']['false_positive'], 1)
            self.assertEqual(row['model_errors']['M2']['false_negative'], 2)
            self.assertEqual(row['samples'], 6)
        self.assertEqual(len(errors), 20)
        self.assertEqual(summary, analyze(*[copy.deepcopy(x) for x in fixture()])[1])

    def test_missing_point_is_not_benign_or_regression(self):
        args = fixture()
        args[3][0]['operating_points']['0.01'] = {'threshold': None, 'test': None}
        for p in args[4]:
            if (p['seed'], p['fold'], p['variant']) == (17, 0, 'M2'):
                p['warnings']['0.01'] = None
        errors, summary = analyze(*args)
        row = summary['summaries'][0]
        self.assertEqual(row['categories']['missing_operating_point'], 2)
        self.assertEqual(row['categories']['m3_corrected'], 0)
        self.assertEqual(row['model_errors']['M2']['missing'], 2)
        self.assertEqual(row['paired_status'], 'incomplete_operating_points')

    def test_duplicate_missing_misaligned_or_wrong_decisions_blocked(self):
        for change in ('duplicate', 'missing', 'label', 'group', 'fold', 'decision', 'score', 'scope'):
            with self.subTest(change=change):
                args = fixture()
                if change == 'duplicate':
                    args[4].append(copy.deepcopy(args[4][0]))
                elif change == 'missing':
                    args[4].pop()
                elif change == 'scope':
                    args[0]['scope'] = 'research'
                else:
                    p = args[4][0]
                    if change == 'decision':
                        p['warnings']['0.01'] = 1 - p['warnings']['0.01']
                    else:
                        p[{'group': 'group_id'}.get(change, change)] = {'label': 1, 'group': 'wrong', 'fold': 1, 'score': float('nan')}[change]
                with self.assertRaises(ValueError):
                    analyze(*args)

    def test_csv_hash_and_preservation_and_tampered_run(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run, out = root / 'run', root / 'analysis'
            run.mkdir()
            args = fixture()
            for name, value in zip(('manifest.json', 'sample_index.json', 'folds.json', 'metrics.json'), args[:4]):
                (run / name).write_text(json.dumps(value))
            (run / 'predictions.jsonl').write_text('\n'.join(map(json.dumps, args[4])))
            before = {p.name: p.read_bytes() for p in run.iterdir()}
            summary = analyze_run(run, out)
            self.assertEqual(summary['input_integrity'], 'recorded_only_legacy_run')
            self.assertEqual(summary['error_case_rows'], 20)
            with (out / 'error_cases.csv').open() as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), 20)
            self.assertEqual({p.name: p.read_bytes() for p in run.iterdir()}, before)
            with self.assertRaises(FileExistsError):
                analyze_run(run, out)
            args[0]['artifact_sha256'] = {n: hashlib.sha256(b).hexdigest() for n, b in before.items() if n != 'manifest.json'}
            (run / 'manifest.json').write_text(json.dumps(args[0]))
            self.assertEqual(analyze_run(run, root / 'checked')['input_integrity'], 'checked_against_run_manifest')
            (run / 'predictions.jsonl').write_bytes(before['predictions.jsonl'] + b'\n')
            with self.assertRaisesRegex(ValueError, 'hash'):
                analyze_run(run, root / 'tampered')
            self.assertFalse((root / 'tampered').exists())


if __name__ == '__main__':
    unittest.main()
