"""Inspect C split artifacts and adapt a verified fixture fold for D's runner.

This module never authorizes training on research data or verifies final labels.
"""

from pathlib import Path
import re

from phishing.evaluation.grouped import Fold
from phishing.training.plan import RunPlan
from phishing.training.readiness import read_json, sha256
from phishing.training.synthetic import assert_fixture_cohort


def inspect_c_split_artifacts(manifest_path):
    """Check artifact bytes and the shared input identity; return audit-only data."""
    root = Path(manifest_path).resolve().parent
    manifest = read_json(manifest_path)
    if manifest.get('manifest_type') != 'DATA-03_SPLIT_MANIFEST':
        raise ValueError('Unsupported C split manifest')
    artifacts = manifest.get('artifacts')
    if not isinstance(artifacts, dict):
        raise ValueError('Split artifacts required')
    result = {}
    for name in ('groups_json', 'grouped_5fold_splits_json', 'temporal_splits_json'):
        entry = artifacts.get(name)
        if name == 'temporal_splits_json' and entry is None:
            continue
        if not isinstance(entry, dict) or not isinstance(entry.get('path'), str):
            raise ValueError(f'Missing {name}')
        relative = Path(entry['path'])
        if relative.is_absolute() or not relative.parts or '..' in relative.parts:
            raise ValueError('Artifact path escapes split package')
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or sha256(path) != entry.get('sha256'):
            raise ValueError(f'Split artifact checksum mismatch: {name}')
        result[name] = read_json(path)
    expected = manifest.get('input_sha256')
    if not isinstance(expected, str) or re.fullmatch(r'[0-9a-f]{64}', expected) is None or any(
        result[name].get('metadata', {}).get('input_sha256') != expected for name in result
    ):
        raise ValueError('Split artifacts refer to different inputs')
    group_metadata = result['groups_json']['metadata']
    grouped_metadata = result['grouped_5fold_splits_json']['metadata']
    if any(not group_metadata.get(name) or group_metadata.get(name) != grouped_metadata.get(name)
           for name in ('group_rules_version', 'psl_snapshot_sha256')):
        raise ValueError('Grouping rule provenance mismatch')
    return result['groups_json'], result['grouped_5fold_splits_json']


def fold_from_c_grouped_split(samples, groups, grouped, *, seed, number, excluded_ids=frozenset()):
    """Validate C's inner/outer partition before a synthetic fit_fold call."""
    assert_fixture_cohort(samples)
    ids = [sample.sample_id for sample in samples]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError('Unique sample IDs required')
    lookup = {sid: index for index, sid in enumerate(ids)}
    provided_groups = groups.get('sample_groups')
    if not isinstance(provided_groups, dict) or set(provided_groups) != set(lookup):
        raise ValueError('Group/sample cohort mismatch')
    if any(provided_groups[sample.sample_id] != sample.group_id for sample in samples):
        raise ValueError('Group assignments differ from model samples')
    metadata = grouped.get('metadata', {})
    if metadata.get('anti_leakage_verified') is not True or seed not in metadata.get('seeds', []):
        raise ValueError('Grouped split not verified for this seed')
    folds = grouped.get('splits_by_seed', {}).get(str(seed))
    if not isinstance(folds, list) or type(number) is not int or not 0 <= number < len(folds):
        raise ValueError('Missing grouped fold')
    selected = folds[number]
    if (selected.get('fold') != number or selected.get('seed') != seed
            or selected.get('is_usable') is not True
            or selected.get('class_sufficiency', {}).get('status') != 'sufficient'):
        raise ValueError('Grouped fold is not usable')
    names = ('inner_train_indices', 'inner_val_indices', 'test_indices')
    parts = [selected.get(name) for name in names]
    if any(not isinstance(part, list) or not part or any(sid not in lookup for sid in part) for part in parts):
        raise ValueError('Invalid grouped fold IDs')
    outer_train = selected.get('train_indices')
    if (not isinstance(outer_train, list) or len(outer_train) != len(set(outer_train))
            or set(outer_train) != set(parts[0]) | set(parts[1])):
        raise ValueError('Inner partitions do not cover outer train')
    if set(outer_train) | set(parts[2]) != set(lookup):
        raise ValueError('Outer fold does not cover sample cohort')
    RunPlan('M0', seed, *(tuple(part) for part in parts)).validate(provided_groups, frozenset(excluded_ids))
    return Fold(seed, number, *(tuple(lookup[sid] for sid in part) for part in parts))
