#!/usr/bin/env python3
"""Build a pending pilot from verified local train shards; never invent records.

Selection and prior-exposure files are restricted C/D inputs, never shared with A/B.
The builder writes a NEW private directory and a proposed registry, never approvals.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import secrets
import shutil
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / 'src'))
from phishing.annotation import BlindSample, export_blind_view, extract_safe_view_content
from phishing.data.grouping import extract_group_id, GROUP_RULES_VERSION, PSL_SNAPSHOT_SHA256
from phishing.preprocessing.urls import normalize_url
from phishing.data.loader import verify_source_file

DATASET_ID = 'REAL-PILOT-32-V2'
PLAN = 'PILOT-PLAN-V2-FULL-OVERLAP'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def html_bytes(value) -> bytes:
    if isinstance(value, bytes) and value:
        value.decode('utf-8')  # Fail on unsupported encoding, never silently change bytes.
        return value
    if isinstance(value, str) and value:
        return value.encode('utf-8')
    raise ValueError('Missing/non-text HTML in source record')


def record_fingerprints(url: str, html) -> dict[str, str]:
    raw = html_bytes(html)
    group = extract_group_id(url)
    if group == 'unknown':
        raise ValueError('Invalid URL/group in source record')
    normalized = normalize_url(url)
    text, structure = extract_safe_view_content(raw.decode('utf-8'), normalized, max_html_characters=2_000_000)
    # Also compare what annotators saw, independent of ID and raw markup changes.
    view_hash = sha256(json.dumps([text, structure], ensure_ascii=False, sort_keys=True,
                                 separators=(',', ':')).encode('utf-8'))
    return {'url_sha256': sha256(url.encode('utf-8')),
            'normalized_url_sha256': sha256(normalized.encode('utf-8')),
            'html_sha256': sha256(raw), 'group_sha256': sha256(group.encode('utf-8')),
            'view_content_sha256': view_hash}


def load_verified_candidates(selection_path: Path, source_root: Path, manifest_path: Path) -> list[dict]:
    """Resolve restricted locators to actual rows after full shard SHA/size checks."""
    import pyarrow.parquet as pq
    manifest = read_json(manifest_path)
    selection = read_json(selection_path)
    revision = manifest.get('revision')
    if (manifest.get('source_id') != 'phreshphish' or manifest.get('source_split') != 'train'
            or not isinstance(revision, str) or not re.fullmatch(r'[0-9a-f]{40}', revision)
            or selection.get('revision') != revision):
        raise ValueError('Require pinned PhreshPhish train revision matching selection')
    locators = selection.get('records')
    if not isinstance(locators, list) or len(locators) != 32:
        raise ValueError('Selection must contain exactly 32 source locators')
    entries = {entry['relative_path']: entry for entry in manifest['files']}
    requested: dict[str, list[int]] = {}
    for locator in locators:
        if set(locator) != {'relative_path', 'row_offset'}:
            raise ValueError('Selection contains labels/HTML or unexpected fields; locators only')
        relative, offset = locator['relative_path'], locator['row_offset']
        if relative not in entries or type(offset) is not int or offset < 0:
            raise ValueError('Unknown shard or invalid row offset')
        requested.setdefault(relative, []).append(offset)
    rows = {}
    for relative, offsets in requested.items():
        if len(offsets) != len(set(offsets)):
            raise ValueError('Duplicate source locator')
        path = (source_root / relative).resolve()
        if not path.is_relative_to(source_root.resolve()):
            raise ValueError('Shard escapes source root')
        entry = entries[relative]
        expected = entry.get('source_metadata_lfs_sha256')
        verify_source_file(path, manifest_path, 'phreshphish')
        parquet = pq.ParquetFile(path)
        if not {'url', 'html', 'label', 'date'} <= set(parquet.schema.names):
            raise ValueError('Source schema missing url/html/label/date')
        remaining = set(offsets)
        start = 0
        for batch in parquet.iter_batches(batch_size=128, columns=['url', 'html', 'label', 'date']):
            for offset in sorted(remaining & set(range(start, start + batch.num_rows))):
                row = batch.slice(offset - start, 1).to_pylist()[0]
                label = row['label']
                if type(label) is int and label in (0, 1):
                    label = 'phish' if label == 1 else 'benign'
                elif isinstance(label, str):
                    label = {'phishing': 'phish', 'phish': 'phish', 'benign': 'benign'}.get(label.strip().lower())
                else:
                    label = None
                if label not in {'phish', 'benign'}:
                    raise ValueError('Missing/out-of-scope source label')
                if hasattr(row['date'], 'isoformat'):
                    row['date'] = row['date'].isoformat()
                fingerprints = record_fingerprints(row['url'], row['html'])
                rows[(relative, offset)] = dict(row, source_label=label, source_path=relative,
                    source_row_offset=offset, source_revision=revision, source_file_sha256=expected,
                    **fingerprints)
                remaining.remove(offset)
            start += batch.num_rows
            if not remaining:
                break
        if remaining:
            raise ValueError('Source row offset outside shard')
    result = [rows[(loc['relative_path'], loc['row_offset'])] for loc in locators]
    if sum(row['source_label'] == 'phish' for row in result) != 20:
        raise ValueError('Source labels must give 20 phishing and 12 benign')
    return result


def load_blocked_entities(evidence_path: Path, registry_path: Path) -> dict[str, set[str]]:
    """Require complete raw exposure batches, including audit and former V2.

    C/D must verify evidence file hashes against their retained handoff records.
    Missing raw inputs are a blocker, not permission to assert zero overlap.
    """
    blocked = {key: set() for key in record_fingerprints('https://shape.example/', '<p>shape</p>')}
    packages = read_json(evidence_path).get('packages', [])
    expected_counts = {'practice': 20, 'v1': 32, 'audit': 20, 'v2_unverified': 32}
    if len(packages) != 4 or {p.get('kind') for p in packages} != set(expected_counts):
        raise ValueError('Require practice, V1, audit and unverified V2 exposure evidence')
    for package in packages:
        path = (evidence_path.parent / package['path']).resolve()
        if file_hash(path) != package['sha256']:
            raise ValueError('Prior exposure checksum mismatch')
        records = read_json(path)
        if not isinstance(records, list) or len(records) != expected_counts[package['kind']]:
            raise ValueError('Incomplete prior exposure batch')
        for row in records:
            for key, value in record_fingerprints(row['url'], row['html']).items():
                blocked[key].add(value)
    registry = read_json(registry_path)
    if registry.get('training_blocked') is not True:
        raise ValueError('Training guard must remain closed')
    for entry in registry.get('exclusions', []):
        for row in entry.get('samples', []):
            for key in blocked:
                if row.get(key):
                    blocked[key].add(row[key])
    return blocked


def check_deduplication(records: list[dict], blocked: dict[str, set[str]]) -> None:
    seen = {key: set() for key in blocked}
    for row in records:
        for key in blocked:
            value = row[key]
            if value in blocked[key] or value in seen[key]:
                raise ValueError(f'Exposure/internal overlap: {key}')
            seen[key].add(value)


def build_real_pilot_v2(selection: Path, source_root: Path, prior_evidence: Path,
                        output: Path, repo_root: Path = REPO_ROOT) -> Path:
    """Never overwrite an existing package, registry, manifest or approvals."""
    if output.exists():
        raise FileExistsError('Output already exists; preserve previous evidence')
    private_root = (repo_root / 'data' / 'raw').resolve()
    for restricted in (selection, prior_evidence, output):
        if not restricted.resolve().is_relative_to(private_root):
            raise ValueError('Selection, exposure evidence and output must stay in data/raw (C/D only)')
    source_manifest = repo_root / 'configs' / 'source_manifest.json'
    registry_path = repo_root / 'data' / 'exclusion_registry.json'
    records = load_verified_candidates(selection, source_root, source_manifest)
    blocked = load_blocked_entities(prior_evidence, registry_path)
    check_deduplication(records, blocked)
    cb_path, dict_path = repo_root / 'docs' / 'CODEBOOK_V1.md', repo_root / 'configs' / 'dictionary_v1.json'
    cb_text = cb_path.read_text(encoding='utf-8')
    version = re.search(r'\*\*Phiên bản:\*\*\s*`?v?([0-9.]+)', cb_text)
    if not version or not re.search(r'\*\*Trạng thái:\*\*\s*`?locked\b', cb_text):
        raise ValueError('Codebook on disk must be locked')
    dictionary = read_json(dict_path)
    if dictionary.get('status') != 'locked':
        raise ValueError('Dictionary on disk must be locked')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.pilot-staging-', dir=output.parent))
    try:
        order = list(range(32))
        secrets.SystemRandom().shuffle(order)
        samples, mapping = [], []
        for index, position in enumerate(order, 1):
            row = records[position]
            normalized = normalize_url(row['url'])
            text, structure = extract_safe_view_content(html_bytes(row['html']).decode('utf-8'), normalized,
                                                        max_html_characters=2_000_000)
            sid = f'PILOT-{index:03d}'
            samples.append(BlindSample(sample_id=sid, url=normalized, page_text=text,
                structure_summary=structure, random_subset=True, codebook_version=version.group(1)))
            mapping.append({key: value for key, value in row.items() if key != 'html'} | {'sample_id': sid})
        view = staging / 'blind_view_pilot_real_v2.json'
        export_blind_view(samples, view, dataset_id=DATASET_ID, dataset_type='real_pilot_v2_pending_acceptance',
                          is_synthetic=False, sampling_plan_version=PLAN)
        write_json(staging / 'source_mapping.json', mapping)
        write_json(staging / 'blind_order.json', order)
        manifest = {'dataset_id': DATASET_ID, 'is_synthetic': False, 'sample_count': 32,
            'source_class_counts': {'phish': 20, 'benign': 12}, 'status': 'pending_lead_acceptance',
            'ready_for_annotation': False, 'acceptance': {'B': 'pending', 'D': 'pending'},
            'codebook_version': version.group(1), 'codebook_status': 'locked',
            'dictionary_version': dictionary['version'], 'dictionary_status': 'locked',
            'codebook_sha256': file_hash(cb_path), 'dictionary_sha256': file_hash(dict_path),
            'blind_view_path': (output / view.name).relative_to(repo_root).as_posix(),
            'blind_view_sha256': file_hash(view), 'sampling_plan_version': PLAN,
            'restricted_source_mapping_sha256': file_hash(staging / 'source_mapping.json'),
            'restricted_blind_order_sha256': file_hash(staging / 'blind_order.json'),
            'source_verification_status': 'verified_pinned_train_rows',
            'source_manifest_sha256': file_hash(source_manifest), 'selection_sha256': file_hash(selection),
            'prior_exposure_evidence_sha256': file_hash(prior_evidence),
            'exclusion_registry_sha256': file_hash(registry_path),
            'group_rules_version': GROUP_RULES_VERSION, 'psl_sha256': PSL_SNAPSHOT_SHA256,
            'exposure_review': {'A': 'pending', 'B': 'pending', 'D': 'pending'},
            'official_test_used': False}
        write_json(staging / 'pilot_manifest_v2.json', manifest)
        registry = read_json(registry_path)
        # Append a new entry; never replace the old unverified V2 exclusions.
        registry['exclusions'].append({'exclusion_id': 'EXCL-PILOT-02-REBUILD-' + manifest['blind_view_sha256'][:12],
            'dataset_id': DATASET_ID, 'source': 'phreshphish', 'split': 'train',
            'source_metadata_revision': read_json(source_manifest)['revision'],
            'rows_api_revision_pinned': True, 'mapping_status': 'resolved',
            'action': 'permanently_exclude_from_train_val_test', 'n_samples': 32,
            'samples': [{key: row[key] for key in blocked} for row in records]})
        registry['training_blocked'] = True
        registry['total_excluded_entries'] = len(registry['exclusions'])
        registry['total_excluded_samples'] = sum(len(e['samples']) for e in registry['exclusions'])
        registry['counting_note'] = 'Entry memberships, not deduplicated unique samples; prior exclusions preserved.'
        registry['updated_at_utc'] = datetime.now(timezone.utc).isoformat()
        write_json(staging / 'exclusion_registry.proposed.json', registry)
        staging.rename(output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return output / 'pilot_manifest_v2.json'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--prior-evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = build_real_pilot_v2(args.selection, args.source_root, args.prior_evidence, args.output)
    print(f'Pending manifest: {manifest}; no approval, registry publication or training performed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
