"""Synthetic-only integration runner. Real runs require the team data gates."""

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
from importlib.metadata import version

from sklearn.metrics import average_precision_score
from phishing.evaluation.bootstrap import paired_bootstrap
from phishing.evaluation.grouped import make_folds
from phishing.evaluation.metrics import binary_metrics, select_validation_threshold
from phishing.training.pipeline import VARIANTS, make_pipeline, rule_scores
from phishing.training.plan import RunPlan
from phishing.training.synthetic import make_dataset


def fit_fold(samples, fold, variant, dictionary, *, candidates=(0.25, 1.0, 4.0), targets=(0.01, 0.05)):
    if variant not in VARIANTS:
        raise ValueError('Unknown variant')
    indices = fold.train + fold.validation + fold.test
    if any(not isinstance(i, int) or i < 0 or i >= len(samples) for i in indices):
        raise ValueError('Invalid partition indices')
    ids = [s.sample_id for s in samples]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate sample IDs')
    RunPlan('M3' if variant.startswith('M3') else variant, fold.seed,
        *(tuple(ids[i] for i in part) for part in (fold.train, fold.validation, fold.test))).validate(
            {s.sample_id: s.group_id for s in samples})
    for part in (fold.train, fold.validation, fold.test):
        if {samples[i].label for i in part} != {0, 1}:
            raise ValueError('Each partition must have both classes')
        if any(samples[i].snapshot.html is None for i in part):
            raise ValueError('Common paired cohort must have HTML, including M0 rows')
    X = lambda indices: [samples[i].snapshot for i in indices]
    y = lambda indices: [samples[i].label for i in indices]
    fitted = None
    chosen_C = None
    if variant == 'B-rule':
        validation_scores = rule_scores(X(fold.validation), dictionary)
        test_scores = rule_scores(X(fold.test), dictionary)
    else:
        if not candidates or any(c <= 0 for c in candidates):
            raise ValueError('Positive C candidates required')
        choices = []
        for C in sorted(set(candidates)):
            model = make_pipeline(variant, dictionary, C=C, seed=fold.seed)
            model.fit(X(fold.train), y(fold.train))
            scores = model.predict_proba(X(fold.validation))[:, 1].tolist()
            choices.append((float(average_precision_score(y(fold.validation), scores)), -C, model, scores))
        _, negative_C, fitted, validation_scores = max(choices, key=lambda item: item[:2])
        chosen_C = -negative_C
        # No refit on validation: threshold and test scores use the exact same fit.
        test_scores = fitted.predict_proba(X(fold.test))[:, 1].tolist()
    points = {str(target): select_validation_threshold(y(fold.validation), validation_scores, target) for target in targets}
    report = {
        'seed': fold.seed, 'fold': fold.number, 'variant': variant, 'C': chosen_C,
        'fit_samples': len(fold.train), 'validation_samples': len(fold.validation), 'test_samples': len(fold.test),
        'validation_benign': y(fold.validation).count(0), 'test_benign': y(fold.test).count(0),
        'validation_ap': float(average_precision_score(y(fold.validation), validation_scores)),
        'test_ap': float(average_precision_score(y(fold.test), test_scores)),
        'operating_points': {key: {
            'threshold': point.threshold if point else None,
            'validation': asdict(point.validation_metrics) if point else None,
            'test': asdict(binary_metrics(y(fold.test), test_scores, point.threshold)) if point else None,
            'status': 'estimated' if point else 'no_feasible_validation_threshold',
        } for key, point in points.items()},
    }
    predictions = [{
        'sample_id': samples[i].sample_id, 'group_id': samples[i].group_id, 'label': samples[i].label,
        'seed': fold.seed, 'fold': fold.number, 'variant': variant, 'score': score,
        'warnings': {key: int(score >= point.threshold) if point else None for key, point in points.items()},
    } for i, score in zip(fold.test, test_scores)]
    return fitted, report, predictions


def run_synthetic(output, *, groups=40, seeds=(17, 42, 2026), repetitions=2000):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)  # Never overwrite an earlier run.
    samples, dictionary = make_dataset(groups)
    folds = make_folds(samples, seeds=seeds)
    reports, predictions = [], []
    for fold in folds:
        for variant in VARIANTS:
            _, report, rows = fit_fold(samples, fold, variant, dictionary)
            reports.append(report)
            predictions.extend(rows)
        print(f'SYNTHETIC ONLY: seed={fold.seed} fold={fold.number + 1}/5 complete', flush=True)
    comparisons = []
    for seed in seeds:
        by_variant = {variant: sorted(
            [row for row in predictions if row['seed'] == seed and row['variant'] == variant],
            key=lambda row: row['sample_id']) for variant in VARIANTS}
        for baseline in ('M2', 'B-rule'):
            for target in ('0.01', '0.05'):
                left, right = by_variant[baseline], by_variant['M3']
                if [r['sample_id'] for r in left] != [r['sample_id'] for r in right] or len(left) != len(samples):
                    raise ValueError('Incomplete/misaligned OOF coverage')
                a, b = [r['warnings'][target] for r in left], [r['warnings'][target] for r in right]
                complete = None not in a + b
                comparisons.append({
                    'seed': seed, 'target_fpr': float(target), 'baseline': baseline, 'candidate': 'M3',
                    'status': 'estimated' if complete else 'not_estimated_missing_operating_point',
                    'metrics': paired_bootstrap([r['label'] for r in left], [r['group_id'] for r in left],
                        a, b, repetitions=repetitions, seed=813 + seed) if complete else None,
                })
    def write(name, value):
        (output / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    write('folds.json', [asdict(fold) for fold in folds])
    write('sample_index.json', [{'sample_id': s.sample_id, 'group_id': s.group_id, 'label': s.label} for s in samples])
    write('metrics.json', reports)
    write('paired_ci.json', comparisons)
    (output / 'predictions.jsonl').write_text(''.join(json.dumps(row, allow_nan=False) + '\n' for row in predictions), encoding='utf-8')
    root = Path(__file__).resolve().parents[3]
    code_hashes = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in sorted((root / 'src/phishing').rglob('*.py'))}
    write('manifest.json', {
        'scope': 'synthetic_fixture_only', 'research_evidence': False,
        'samples': len(samples), 'groups': groups, 'seeds': list(seeds), 'outer_folds': 5, 'inner_folds': 3,
        'fit_policy': 'inner_group_holdout_no_refit', 'C_grid': [0.25, 1.0, 4.0],
        'selection': 'validation average precision; ties smaller C', 'targets': [0.01, 0.05],
        'variants': list(VARIANTS), 'bootstrap_repetitions': repetitions, 'bootstrap_seed_base': 813,
        'bootstrap': 'paired whole groups, per seed, percentile95; conditioned on fitted models',
        'dictionary': [{**item, 'rules': [asdict(rule) for rule in item['rules']]} for item in dictionary],
        'dataset_sha256': hashlib.sha256(json.dumps([asdict(s) for s in samples], sort_keys=True).encode()).hexdigest(),
        'code_sha256': code_hashes, 'python': platform.python_version(),
        'dependency_lock_sha256': hashlib.sha256((root / 'requirements-dev.lock').read_bytes()).hexdigest(),
        'packages': {name: version(name) for name in ('scikit-learn', 'numpy', 'scipy')},
        'limitations': ['invented labels/domains/templates', 'small validation benign count cannot establish 1% FPR',
                       'draft exact-alias rules; no production dictionary', 'no real-data training or API model export'],
    })
    return output
