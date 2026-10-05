"""Fixture-only input contract check; never authorizes research training."""

import hashlib
import json
from pathlib import Path

from phishing.training.plan import RunPlan


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique_keys)


def check_training_inputs(manifest_path):
    root = Path(manifest_path).resolve().parent
    manifest = read_json(manifest_path)
    if manifest.get('contract_version') != 'training-input-fixture-v0':
        raise ValueError('Unsupported input contract')
    if manifest.get('scope') != 'synthetic_fixture_only':
        raise ValueError('Research inputs blocked: C adapter and approvals are not integrated')
    names = {'index', 'labels', 'groups', 'split', 'exclusion'}
    if set(manifest.get('artifacts', {})) != names:
        raise ValueError('Index, labels, groups, split and exclusion artifacts required')

    def resolve(relative):
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise ValueError('Artifact paths must be relative to the manifest')
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Artifact path escapes the package')
        return path

    artifacts = {}
    for name, entry in manifest['artifacts'].items():
        path = resolve(entry['path'])
        if sha256(path) != entry['sha256']:
            raise ValueError(f'Checksum mismatch: {name}')
        artifacts[name] = read_json(path)

    def index_rows(rows):
        indexed = {}
        if not isinstance(rows, list) or not rows:
            raise ValueError('Nonempty record list required')
        for row in rows:
            sid = row.get('sample_id')
            if not isinstance(sid, str) or not sid.strip() or sid != sid.strip() or sid in indexed:
                raise ValueError('Nonempty unique sample IDs required')
            indexed[sid] = row
        return indexed

    index, labels = index_rows(artifacts['index']), index_rows(artifacts['labels'])
    groups, split, exclusions = artifacts['groups'], artifacts['split'], artifacts['exclusion']
    if set(index) != set(labels) or set(index) != set(groups):
        raise ValueError('Index/label/group sample IDs do not match')
    if any(not isinstance(g, str) or not g.strip() for g in groups.values()):
        raise ValueError('Provided nonempty group IDs required')
    for sid, row in index.items():
        if row.get('exclusion_reason') is not None:
            raise ValueError('Excluded sample entered input cohort')
        if row.get('capture_mode') not in {'stored_html', 'rendered_dom'}:
            raise ValueError('Paired cohort requires an explicit content capture mode')
        if sha256(resolve(row['html_path'])) != row['html_sha256']:
            raise ValueError('HTML checksum mismatch')
        if labels[sid].get('final') is not True or labels[sid].get('class_label') not in {'phishing', 'benign'}:
            raise ValueError('Final binary reference labels required')
    excluded_ids = exclusions['excluded_ids']
    if not isinstance(excluded_ids, list) or any(not isinstance(s, str) or not s.strip() for s in excluded_ids):
        raise ValueError('Explicit exclusion ID list required')
    if type(split['seed']) is not int:
        raise ValueError('Integer seed required')
    partitions = [split[name] for name in ('train_ids', 'validation_ids', 'test_ids')]
    if any(not isinstance(part, list) or any(not isinstance(s, str) for s in part) for part in partitions):
        raise ValueError('Split partitions must contain sample ID lists')
    plan = RunPlan(split['variant'], split['seed'], *(tuple(part) for part in partitions))
    counts = plan.validate(groups, frozenset(excluded_ids))
    if set().union(*map(set, partitions)) != set(index):
        raise ValueError('Split must cover the declared input cohort')
    for part in partitions:
        if {labels[s]['class_label'] for s in part} != {'phishing', 'benign'}:
            raise ValueError('Each train/validation/test partition needs both classes')
    return {'status': 'fixture_inputs_valid', 'research_training_allowed': False,
            'scope': manifest['scope'], 'contract_version': manifest['contract_version'], **counts}
