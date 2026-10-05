"""Paired whole-group percentile bootstrap, conditioned on fitted models."""

import numpy as np
from dataclasses import asdict
from phishing.evaluation.metrics import binary_metrics


def resample_group_indices(groups, rng):
    unique = list(dict.fromkeys(groups))
    lookup = {group: [] for group in unique}
    for i, group in enumerate(groups):
        lookup[group].append(i)
    return [i for pick in rng.integers(0, len(unique), size=len(unique)) for i in lookup[unique[pick]]]


def paired_bootstrap(labels, groups, baseline, candidate, *, repetitions=2000, seed=813):
    if not labels or not (len(labels) == len(groups) == len(baseline) == len(candidate)):
        raise ValueError('Aligned nonempty predictions required')
    if any(not group for group in groups) or len(set(groups)) < 2:
        raise ValueError('At least two nonempty groups required')
    if repetitions < 2 or any(value not in (0, 1) for value in baseline + candidate):
        raise ValueError('Binary decisions and >=2 repetitions required')
    # Validate labels before drawing, including all-one/all-zero cohorts.
    def metrics(y, decisions):
        return asdict(binary_metrics(y, [float(v) for v in decisions], 0.5))
    left, right = metrics(labels, baseline), metrics(labels, candidate)
    draws = {name: [] for name in ('recall', 'fpr', 'precision', 'f1')}
    rng = np.random.default_rng(seed)
    for _ in range(repetitions):
        indices = resample_group_indices(groups, rng)
        a = metrics([labels[i] for i in indices], [baseline[i] for i in indices])
        b = metrics([labels[i] for i in indices], [candidate[i] for i in indices])
        for name in draws:
            if a[name] is not None and b[name] is not None:
                draws[name].append(b[name] - a[name])
    return {name: {
        'difference_candidate_minus_baseline': right[name] - left[name] if right[name] is not None and left[name] is not None else None,
        'ci95': np.quantile(values, [0.025, 0.975], method='linear').tolist() if values else None,
        'valid_replicates': len(values), 'undefined_replicates': repetitions - len(values),
    } for name, values in draws.items()}
