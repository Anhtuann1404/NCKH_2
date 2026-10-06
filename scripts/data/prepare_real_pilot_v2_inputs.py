#!/usr/bin/env python3
"""Prepare restricted V2 inputs from pinned train shards and retained exposure evidence.

Reads source bytes and the old Git literal as data; does not execute page or Git code.
Writes only fingerprints and source locators under data/raw. Never approves a pilot.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phishing.data.loader import verify_source_file
from build_real_pilot_v2 import (check_deduplication, file_hash, record_fingerprints,
                                 write_json)

OLD_V2_COMMIT = '27a7170e23ea6dd0d65bad077313b491b1f760f8'
SHARDS = ('data/train-000.parquet', 'data/train-055.parquet')


def old_v2_fingerprints(registry: dict) -> list[dict[str, str]]:
    source = subprocess.check_output(
        ['git', 'show', f'{OLD_V2_COMMIT}:scripts/data/build_real_pilot_v2.py'],
        cwd=ROOT, text=True)
    tree = ast.parse(source)
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == 'define_pilot_v2_candidates')
    literal = next(n.value for n in function.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'candidates' for t in n.targets))
    if not isinstance(literal, ast.List) or len(literal.elts) != 32:
        raise ValueError('Old V2 literal does not contain exactly 32 candidates')
    result = []
    for item in literal.elts:
        if not isinstance(item, ast.Dict):
            raise ValueError('Old V2 candidate is not a literal dictionary')
        fields = {ast.literal_eval(key): value for key, value in zip(item.keys, item.values)
                  if key is not None and ast.literal_eval(key) in ('raw_url', 'html')}
        if set(fields) != {'raw_url', 'html'}:
            raise ValueError('Old V2 candidate lacks URL or HTML')
        result.append(record_fingerprints(ast.literal_eval(fields['raw_url']),
                                          ast.literal_eval(fields['html'])))
    old = next(e for e in registry['exclusions'] if e['exclusion_id'] == 'EXCL-PILOT-02')
    for field in ('url_sha256', 'html_sha256'):
        if {r[field] for r in result} != {r[field] for r in old['samples']}:
            raise ValueError('Old V2 literal disagrees with retained exclusion registry')
    return result


def prepare(source_root: Path, raw20: Path, output: Path) -> dict:
    import pyarrow.parquet as pq
    private_root = (ROOT / 'data/raw').resolve()
    if not output.resolve().is_relative_to(private_root):
        raise ValueError('Output must stay under restricted data/raw')
    if output.exists():
        raise FileExistsError('Never overwrite prepared evidence')
    manifest_path = ROOT / 'configs/source_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    registry = json.loads((ROOT / 'data/exclusion_registry.json').read_text())
    old20 = next(e for e in registry['exclusions'] if e['exclusion_id'] == 'EXCL-PILOT-01')
    if file_hash(raw20) != old20['batch_sha256']:
        raise ValueError('Raw20 batch checksum mismatch')
    summary = json.loads((ROOT / 'data/source_audit/phreshphish/pilot_summary.json').read_text())
    if summary['pilot_sha256'] != file_hash(raw20):
        raise ValueError('Audit summary does not describe this raw20 batch')
    retained = json.loads(raw20.read_text())['rows']
    if len(retained) != 20 or any(r.get('truncated_cells') for r in retained):
        raise ValueError('Incomplete/truncated raw20 exposure batch')
    raw20_pairs = {(hashlib.sha256(r['row']['url'].encode()).hexdigest(),
                    hashlib.sha256(r['row']['html'].encode()).hexdigest()) for r in retained}
    if len(raw20_pairs) != 20:
        raise ValueError('Duplicate raw20 fingerprints')
    v1_entry = next(e for e in registry['exclusions'] if e['exclusion_id'] == 'EXCL-REAL-PILOT-32')
    v1_pairs = {(s['url_sha256'], s['html_sha256']) for s in v1_entry['samples']}
    v1_by_pair = {(s['url_sha256'], s['html_sha256']): s for s in v1_entry['samples']}
    if len(v1_pairs) != 32:
        raise ValueError('Incomplete V1 registry')
    practice, v1, candidates = [], [], []
    invalid_source_rows = 0
    prior_v2 = old_v2_fingerprints(registry)
    blocked = {key: set() for key in prior_v2[0]}
    for relative in SHARDS:
        path = (source_root / relative).resolve()
        if not path.is_relative_to(source_root.resolve()):
            raise ValueError('Source path escapes source root')
        verify_source_file(path, manifest_path, 'phreshphish')
        offset = 0
        for batch in pq.ParquetFile(path).iter_batches(batch_size=128,
            columns=['url', 'html', 'label', 'date']):
            for row in batch.to_pylist():
                pair = (hashlib.sha256(row['url'].encode()).hexdigest(),
                        hashlib.sha256(row['html'].encode()).hexdigest())
                try:
                    fp = record_fingerprints(row['url'], row['html'])
                except ValueError:
                    if pair in raw20_pairs:
                        practice.append({'url_sha256': pair[0], 'html_sha256': pair[1]})
                    if pair in v1_pairs:
                        v1.append({key: v1_by_pair[pair][key] for key in
                                   ('url_sha256', 'html_sha256', 'group_sha256')})
                    invalid_source_rows += 1
                    offset += 1
                    continue
                if pair in raw20_pairs:
                    practice.append(fp)
                if pair in v1_pairs:
                    v1.append(fp)
                label = row['label']
                if label in ('phish', 'benign') and '2024-10-01' <= str(row['date'])[:10] <= '2025-09-08':
                    candidates.append(({'relative_path': relative, 'row_offset': offset}, label, fp))
                offset += 1
    if len(practice) != 20 or len(v1) != 32:
        raise ValueError('Recovered shards do not fully reconstruct practice/V1 exposures')
    for batch in (practice, v1, prior_v2):
        for fp in batch:
            for field, value in fp.items():
                blocked[field].add(value)
    for entry in registry['exclusions']:
        for sample in entry.get('samples', []):
            for field in blocked:
                if sample.get(field):
                    blocked[field].add(sample[field])
    rng = random.Random(2026)
    rng.shuffle(candidates)
    selected = []
    remaining = {'phish': 20, 'benign': 12}
    for locator, label, fp in candidates:
        if remaining[label] == 0:
            continue
        try:
            check_deduplication([fp], blocked)
        except ValueError:
            continue
        selected.append(locator)
        remaining[label] -= 1
        for field, value in fp.items():
            blocked[field].add(value)
        if not any(remaining.values()):
            break
    if any(remaining.values()):
        raise ValueError('Verified local shards lack sufficient independent candidates')
    output.mkdir(parents=True)
    packages = []
    for kind, rows in [('practice', practice), ('v1', v1), ('audit', practice),
                       ('v2_unverified', prior_v2)]:
        path = output / f'{kind}.fingerprints.json'
        write_json(path, rows)
        packages.append({'kind': kind, 'path': path.name, 'sha256': file_hash(path)})
    write_json(output / 'prior_evidence.json', {'packages': packages,
        'source_revision': manifest['revision'], 'old_v2_git_commit': OLD_V2_COMMIT,
        'raw20_sha256': file_hash(raw20), 'source_manifest_sha256': file_hash(manifest_path)})
    write_json(output / 'selection.json', {'revision': manifest['revision'], 'records': selected,
        'selection_seed': 2026, 'source_shards': list(SHARDS)})
    return {'practice': len(practice), 'v1': len(v1), 'old_v2': len(prior_v2),
            'candidate_pool': len(candidates), 'invalid_source_rows': invalid_source_rows,
            'selected': len(selected), 'selection_seed': 2026}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--raw20', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source_root, args.raw20, args.output), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
