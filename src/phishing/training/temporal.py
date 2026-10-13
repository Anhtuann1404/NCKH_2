"""Validate a dated split before fixture evaluation; does not unlock real training."""

from datetime import date

from phishing.evaluation.grouped import Fold
from phishing.training.plan import RunPlan
from phishing.training.synthetic import assert_fixture_cohort


def fold_from_temporal_split(samples, split, dates_by_id, *, excluded_ids=frozenset()):
    assert_fixture_cohort(samples)
    if split.get('status') != 'evaluable':
        raise ValueError('Temporal split is not evaluable')
    ids = [sample.sample_id for sample in samples]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate sample IDs')
    lookup = {sid: index for index, sid in enumerate(ids)}
    parts = []
    for name in ('train_indices', 'val_indices', 'test_indices'):
        selected = split.get(name)
        if not isinstance(selected, list) or not selected or any(sid not in lookup for sid in selected):
            raise ValueError(f'Invalid temporal {name}')
        parts.append(tuple(selected))
    RunPlan('M0', 17, *parts).validate(
        {sample.sample_id: sample.group_id for sample in samples}, frozenset(excluded_ids))
    selected_ids = set().union(*map(set, parts))
    if any(sid in selected_ids for name in ('purged_val_indices', 'purged_test_indices')
           for sid in split.get(name, [])):
        raise ValueError('Purged sample entered temporal evaluation')
    try:
        ranges = [[date.fromisoformat(dates_by_id[sid]) for sid in part] for part in parts]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('Every temporal sample needs a valid date') from exc
    if not (max(ranges[0]) < min(ranges[1]) and max(ranges[1]) < min(ranges[2])):
        raise ValueError('Temporal partitions are not strictly ordered by calendar date')
    try:
        cutoffs = split['cutoffs']
        train_cutoff = date.fromisoformat(cutoffs['train_cutoff_date'])
        val_cutoff = date.fromisoformat(cutoffs['val_cutoff_date'])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('Temporal cutoffs are missing or invalid') from exc
    # C's cutoff is based on raw windows; purging may remove the last val day.
    if not (max(ranges[0]) == train_cutoff < min(ranges[1])
            and max(ranges[1]) <= val_cutoff < min(ranges[2])):
        raise ValueError('Temporal cutoffs do not match selected samples')
    # -1 keeps a temporal fixture report distinct from grouped fold 0.
    return Fold(17, -1, *(tuple(lookup[sid] for sid in part) for part in parts))
