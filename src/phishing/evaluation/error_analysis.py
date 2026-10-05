"""Inspect paired M2/M3 fixture OOF errors without fitting or choosing thresholds."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

from phishing.evaluation.metrics import validate_scores
from phishing.training.plan import RunPlan


def analyze(manifest, index, folds, reports, predictions):
    if manifest.get('scope') != 'synthetic_fixture_only' or manifest.get('research_evidence') is not False:
        raise ValueError('Only synthetic fixture runs are supported')
    samples = {r['sample_id']: r for r in index}
    if not samples or len(samples) != len(index) or len(index) != manifest['samples']:
        raise ValueError('Nonempty unique sample index must match manifest')
    if any(type(r['label']) is not int or r['label'] not in (0, 1) for r in index):
        raise ValueError('Binary integer fixture labels required')
    seeds, targets = manifest['seeds'], manifest['targets']
    if not seeds or len(seeds) != len(set(seeds)) or targets != [0.01, 0.05]:
        raise ValueError('Unique seeds and 1%/5% operating points required')
    expected_folds = {(s, f) for s in seeds for f in range(manifest['outer_folds'])}
    fold_map = {(f['seed'], f['number']): f for f in folds}
    if len(fold_map) != len(folds) or set(fold_map) != expected_folds:
        raise ValueError('Missing, unexpected or duplicate folds')
    assignment = {}
    for (seed, number), fold in fold_map.items():
        partitions = []
        for part in ('train', 'validation', 'test'):
            indices = fold[part]
            if any(type(i) is not int or not 0 <= i < len(index) for i in indices):
                raise ValueError('Invalid fold indices')
            partitions.append(tuple(index[i]['sample_id'] for i in indices))
        if set(sum(partitions, ())) != set(samples):
            raise ValueError('Each fold must partition the common cohort')
        RunPlan('M2', seed, *partitions).validate({sid: r['group_id'] for sid, r in samples.items()})
        for sid in partitions[2]:
            if (seed, sid) in assignment:
                raise ValueError('Repeated OOF test sample')
            assignment[seed, sid] = number
    if set(assignment) != {(s, sid) for s in seeds for sid in samples}:
        raise ValueError('Incomplete OOF fold coverage')
    relevant = [r for r in reports if r['variant'] in ('M2', 'M3')]
    report_map = {(r['seed'], r['fold'], r['variant']): r for r in relevant}
    expected_reports = {(s, f, v) for s, f in expected_folds for v in ('M2', 'M3')}
    if len(report_map) != len(relevant) or set(report_map) != expected_reports:
        raise ValueError('Missing or duplicate M2/M3 fold reports')
    paired = {}
    for p in predictions:
        if p['variant'] not in ('M2', 'M3'):
            continue
        key = p['seed'], p['sample_id'], p['variant']
        if key in paired or (p['seed'], p['sample_id']) not in assignment:
            raise ValueError('Duplicate or unexpected OOF prediction')
        sample = samples[p['sample_id']]
        if p['fold'] != assignment[p['seed'], p['sample_id']] or any(p[k] != sample[k] for k in ('label', 'group_id')):
            raise ValueError('OOF fold, group or label mismatch')
        validate_scores([p['label']], [p['score']])
        report = report_map[p['seed'], p['fold'], p['variant']]
        for target in targets:
            point, warning = report['operating_points'][str(target)], p['warnings'][str(target)]
            threshold = point['threshold']
            if threshold is None:
                if warning is not None or point['test'] is not None:
                    raise ValueError('Missing threshold cannot produce a decision')
            else:
                validate_scores([0], [threshold])
                if type(warning) is not int or warning != int(p['score'] >= threshold):
                    raise ValueError('Decision differs from saved threshold/score')
        paired[key] = p
    if set(paired) != {(s, sid, v) for s in seeds for sid in samples for v in ('M2', 'M3')}:
        raise ValueError('M2/M3 must cover the same complete cohort')
    errors, summaries = [], []
    for seed in seeds:
        for target in targets:
            counts = Counter({name: 0 for name in ('m3_corrected', 'm3_regressed', 'both_wrong', 'both_correct', 'missing_operating_point')})
            model_errors = {v: Counter({'false_positive': 0, 'false_negative': 0, 'missing': 0}) for v in ('M2', 'M3')}
            for sid in sorted(samples):
                row = {'seed': seed, 'target_fpr': target, 'sample_id': sid,
                       'group_id': samples[sid]['group_id'], 'label': samples[sid]['label'],
                       'fold': assignment[seed, sid]}
                correct = []
                for variant in ('M2', 'M3'):
                    p = paired[seed, sid, variant]
                    warning = p['warnings'][str(target)]
                    outcome = ('missing' if warning is None else 'correct' if warning == p['label']
                               else 'false_positive' if p['label'] == 0 else 'false_negative')
                    if outcome != 'correct':
                        model_errors[variant][outcome] += 1
                    row.update({variant + '_score': p['score'], variant + '_warning': warning,
                                variant + '_threshold': report_map[seed, p['fold'], variant]['operating_points'][str(target)]['threshold'],
                                variant + '_outcome': outcome})
                    correct.append(None if warning is None else outcome == 'correct')
                category = ('missing_operating_point' if None in correct else
                            {(False, True): 'm3_corrected', (True, False): 'm3_regressed',
                             (False, False): 'both_wrong', (True, True): 'both_correct'}[tuple(correct)])
                counts[category] += 1
                if category != 'both_correct':
                    errors.append({**row, 'category': category})
            summaries.append({'seed': seed, 'target_fpr': target, 'samples': len(samples),
                              'paired_status': 'complete' if not counts['missing_operating_point'] else 'incomplete_operating_points',
                              'categories': dict(counts), 'model_errors': {v: dict(c) for v, c in model_errors.items()}})
    return errors, {'scope': 'synthetic_fixture_only', 'research_evidence': False,
                    'unique_samples': len(samples), 'summaries': summaries,
                    'notes': ['Counts are separate by seed and target; repeated seeds are not independent samples.',
                              'Target FPR is the validation constraint, not a promise about test FPR.',
                              'Saved thresholds are reused unchanged. Missing points are not benign decisions.',
                              'Paired changes describe decisions; they do not establish causality for organization signals.',
                              'No raw URLs or HTML exported; invented labels are not research ground truth.']}


def analyze_run(run_dir, output):
    run_dir, output = Path(run_dir), Path(output)
    names = ('manifest.json', 'sample_index.json', 'folds.json', 'metrics.json', 'predictions.jsonl')
    blobs = {name: (run_dir / name).read_bytes() for name in names}
    manifest, index, folds, reports = [json.loads(blobs[n]) for n in names[:4]]
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in blobs.items()}
    declared = manifest.get('artifact_sha256')
    if declared is not None:
        if any(declared.get(name) != hashes[name] for name in names[1:]):
            raise ValueError('Input artifact hash differs from run manifest')
    predictions = [json.loads(line) for line in blobs['predictions.jsonl'].splitlines() if line.strip()]
    errors, summary = analyze(manifest, index, folds, reports, predictions)
    summary.update({'input_sha256': hashes, 'input_run': str(run_dir.resolve()),
                    'input_integrity': 'checked_against_run_manifest' if declared is not None else 'recorded_only_legacy_run',
                    'inspector_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    'error_case_rows': len(errors)})
    if output.resolve() == run_dir.resolve():
        raise ValueError('Use a separate analysis directory; preserve the input run')
    output.mkdir(parents=True, exist_ok=False)
    columns = ['seed', 'target_fpr', 'sample_id', 'group_id', 'label', 'fold', 'category',
               'M2_score', 'M2_threshold', 'M2_warning', 'M2_outcome',
               'M3_score', 'M3_threshold', 'M3_warning', 'M3_outcome']
    csv_path = output / 'error_cases.csv'
    with csv_path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(errors)
    summary['error_cases_sha256'] = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    (output / 'error_summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return summary
