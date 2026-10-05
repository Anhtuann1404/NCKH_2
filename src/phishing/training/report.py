"""Aggregate fixture OOF decisions per seed, never pool repeated seeds."""
import csv
from dataclasses import asdict
import hashlib
import json
from statistics import mean, pstdev

from phishing.evaluation.metrics import binary_metrics


def spread(values):
    values = [v for v in values if v is not None]
    return {'count': len(values), 'mean': mean(values) if values else None,
            'std_population': pstdev(values) if values else None,
            'min': min(values) if values else None, 'max': max(values) if values else None}


def summarize(manifest, index, reports, predictions, comparisons):
    if manifest.get('scope') != 'synthetic_fixture_only' or manifest.get('research_evidence') is not False:
        raise ValueError('This reporter accepts synthetic fixtures only')
    expected = {row['sample_id']: row for row in index}
    if not expected or len(expected) != len(index) or len(index) != manifest['samples']:
        raise ValueError('Invalid sample index')
    rows = []
    expected_runs = {(s, v) for s in manifest['seeds'] for v in manifest['variants']}
    if {(p['seed'], p['variant']) for p in predictions} != expected_runs:
        raise ValueError('Unexpected or missing prediction runs')
    for seed, variant in sorted(expected_runs):
        cohort = [p for p in predictions if (p['seed'], p['variant']) == (seed, variant)]
        ids = [p['sample_id'] for p in cohort]
        if len(ids) != len(set(ids)) or set(ids) != set(expected):
            raise ValueError('Duplicate or incomplete OOF coverage')
        for p in cohort:
            if any(p[key] != expected[p['sample_id']][key] for key in ('label', 'group_id')):
                raise ValueError('OOF label/group differs from sample index')
        folds = [r for r in reports if (r['seed'], r['variant']) == (seed, variant)]
        fold_ids = [r['fold'] for r in folds]
        if len(fold_ids) != manifest['outer_folds'] or set(fold_ids) != set(range(manifest['outer_folds'])):
            raise ValueError('Duplicate or missing fold reports')
        for fold in folds:
            if sum(p['fold'] == fold['fold'] for p in cohort) != fold['test_samples']:
                raise ValueError('Fold prediction count differs from report')
        for target in manifest['targets']:
            key = str(target)
            warnings = [p['warnings'][key] for p in cohort]
            if any(w is not None and (type(w) is not int or w not in (0, 1)) for w in warnings):
                raise ValueError('Invalid warning decision')
            complete = None not in warnings
            for fold in folds:
                members = [p for p in cohort if p['fold'] == fold['fold']]
                point = fold['operating_points'][key]
                if point['threshold'] is None:
                    if any(p['warnings'][key] is not None for p in members) or point['test'] is not None:
                        raise ValueError('Missing threshold cannot produce test decisions')
                else:
                    metrics = asdict(binary_metrics([p['label'] for p in members],
                                                    [p['score'] for p in members], point['threshold']))
                    if metrics != point['test'] or any(p['warnings'][key] != int(p['score'] >= point['threshold']) for p in members):
                        raise ValueError('Threshold/metrics/decisions disagree')
            metrics = asdict(binary_metrics([p['label'] for p in cohort], warnings, 0.5)) if complete else None
            rows.append({'seed': seed, 'variant': variant, 'target_fpr': target,
                         'samples': len(cohort), 'phishing': sum(p['label'] for p in cohort),
                         'benign': sum(p['label'] == 0 for p in cohort),
                         'groups': len({p['group_id'] for p in cohort}),
                         'status': 'estimated' if complete else 'not_estimated_missing_operating_point',
                         'missing_decisions': warnings.count(None), 'metrics': metrics,
                         'fold_average_precision': spread([f['test_ap'] for f in folds]),
                         'fold_recall': spread([f['operating_points'][key]['test']['recall']
                                               if f['operating_points'][key]['test'] else None for f in folds]),
                         'fold_fpr': spread([f['operating_points'][key]['test']['fpr']
                                            if f['operating_points'][key]['test'] else None for f in folds])})
    variation = []
    for variant in manifest['variants']:
        for target in manifest['targets']:
            subset = [r for r in rows if r['variant'] == variant and r['target_fpr'] == target]
            complete = all(r['metrics'] is not None for r in subset)
            variation.append({'variant': variant, 'target_fpr': target,
                              'seeds': len(subset), 'unique_samples': len(index),
                              'status': 'estimated' if complete else 'not_estimated_missing_operating_point',
                              'recall': spread([r['metrics']['recall'] for r in subset]) if complete else None,
                              'fpr': spread([r['metrics']['fpr'] for r in subset]) if complete else None})
    return {'scope': 'synthetic_fixture_only', 'research_evidence': False,
            'rows': rows, 'seed_variation': variation, 'paired_comparisons': comparisons,
            'notes': ['OOF counts and rates are calculated separately for each seed.',
                      'Average precision is reported across folds; cross-fit scores are not pooled.',
                      'Spread describes fold/seed variation, not a confidence interval.',
                      'Paired group bootstrap CI conditions on fitted models; no retraining.',
                      'Missing operating points remain missing; no partial-cohort estimate.',
                      'Invented data cannot establish real-world detection performance or 1% FPR.']}


def write_report(output, summary):
    paths = [output / name for name in ('summary.json', 'summary.csv', 'report.md')]
    if any(path.exists() for path in paths):
        raise FileExistsError('Summary outputs already exist; use a new run directory')
    paths[0].write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    columns = ['seed', 'variant', 'target_fpr', 'samples', 'phishing', 'benign', 'groups',
               'status', 'missing_decisions', 'tp', 'fn', 'fp', 'tn', 'recall', 'fpr', 'precision', 'f1',
               'fold_ap_mean', 'fold_ap_std']
    with paths[1].open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in summary['rows']:
            writer.writerow({**{k: row[k] for k in columns[:9]}, **(row['metrics'] or {}),
                             'fold_ap_mean': row['fold_average_precision']['mean'],
                             'fold_ap_std': row['fold_average_precision']['std_population']})
    fmt = lambda v: 'NA' if v is None else f'{v:.4f}'
    lines = ['# SYNTHETIC ONLY — NOT RESEARCH EVIDENCE', '',
             *summary['notes'], '', '| Seed | Model | Target validation FPR | N | Recall OOF | FPR OOF | Mean fold AP | Status |',
             '|---|---|---|---|---|---|---|---|']
    for r in summary['rows']:
        m = r['metrics'] or {}
        lines.append(f"| {r['seed']} | {r['variant']} | {r['target_fpr']} | {r['samples']} | {fmt(m.get('recall'))} | {fmt(m.get('fpr'))} | {fmt(r['fold_average_precision']['mean'])} | {r['status']} |")
    lines += ['', '## Variation across seeds (descriptive, not CI)', '',
              '| Model | Target validation FPR | Unique N | Recall mean / std | FPR mean / std |',
              '|---|---|---|---|---|']
    for r in summary['seed_variation']:
        recall, fpr = r['recall'] or {}, r['fpr'] or {}
        lines.append(f"| {r['variant']} | {r['target_fpr']} | {r['unique_samples']} | {fmt(recall.get('mean'))} / {fmt(recall.get('std_population'))} | {fmt(fpr.get('mean'))} / {fmt(fpr.get('std_population'))} |")
    lines += ['', '## Paired differences: M3 minus baseline', '',
              '| Seed | Baseline | Target validation FPR | Metric | Difference | CI95 | Valid replicates |',
              '|---|---|---|---|---|---|---|']
    for c in summary['paired_comparisons']:
        if c['metrics'] is None:
            lines.append(f"| {c['seed']} | {c['baseline']} | {c['target_fpr']} | NA | NA | NA | 0 |")
            continue
        for metric, result in c['metrics'].items():
            interval = result['ci95']
            ci = 'NA' if interval is None else f'[{fmt(interval[0])}, {fmt(interval[1])}]'
            lines.append(f"| {c['seed']} | {c['baseline']} | {c['target_fpr']} | {metric} | {fmt(result['difference_candidate_minus_baseline'])} | {ci} | {result['valid_replicates']} |")
    paths[2].write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
