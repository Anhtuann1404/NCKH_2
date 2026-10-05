"""Reusable outer grouped CV and an inner grouped holdout; never refit on val."""

from dataclasses import dataclass
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from phishing.training.plan import RunPlan


@dataclass(frozen=True)
class Fold:
    seed: int
    number: int
    train: tuple[int, ...]
    validation: tuple[int, ...]
    test: tuple[int, ...]


def make_folds(samples, *, seeds=(17, 42, 2026), outer_splits=5, inner_splits=3, excluded_ids=frozenset()):
    ids = [s.sample_id for s in samples]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError('Nonempty unique sample IDs required')
    groups = [s.group_id for s in samples]
    labels = [s.label for s in samples]
    if set(labels) != {0, 1} or len(set(groups)) < outer_splits:
        raise ValueError('Insufficient groups/classes; do not silently reduce folds')
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError('Seeds must be nonempty and unique')
    index = np.arange(len(samples))
    result = []
    for seed in seeds:
        outer = StratifiedGroupKFold(outer_splits, shuffle=True, random_state=seed)
        for number, (development, test) in enumerate(outer.split(index, labels, groups)):
            if len({groups[i] for i in development}) < inner_splits:
                raise ValueError('Insufficient inner groups')
            inner = StratifiedGroupKFold(inner_splits, shuffle=True, random_state=seed + number + 1)
            fit_local, val_local = next(inner.split(development,
                [labels[i] for i in development], [groups[i] for i in development]))
            train, validation = development[fit_local], development[val_local]
            for part in (train, validation, test):
                if {labels[i] for i in part} != {0, 1}:
                    raise ValueError('Each partition needs both classes')
            plan = RunPlan('M0', seed, *(tuple(ids[i] for i in part) for part in (train, validation, test)))
            plan.validate(dict(zip(ids, groups)), excluded_ids)
            result.append(Fold(seed, number, *(tuple(int(i) for i in part) for part in (train, validation, test))))
    return result
