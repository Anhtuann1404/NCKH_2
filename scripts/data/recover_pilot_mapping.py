#!/usr/bin/env python3
"""Reproduce restricted URL+HTML byte matching for retained raw20 and invalidated V1.

No labels, targets, scripts or page rendering. This does not approve a pilot or training.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from phishing.data.loader import verify_source_file, file_sha256


def content_key(row):
    if not isinstance(row.get('url'), str) or not isinstance(row.get('html'), str):
        raise ValueError('Matching requires original URL and HTML strings')
    return tuple(hashlib.sha256(row[k].encode('utf-8')).hexdigest() for k in ('url', 'html'))


def recover(raw20: Path, source_root: Path, shards: list[str], output: Path) -> dict:
    import pyarrow.parquet as pq
    if not output.resolve().is_relative_to((ROOT / 'data/raw').resolve()):
        raise ValueError('Mapping must remain in restricted data/raw')
    if output.exists():
        raise FileExistsError('Preserve existing mapping evidence; use a new output')
    registry_path = ROOT / 'data/exclusion_registry.json'
    registry = json.loads(registry_path.read_text())
    old20 = next(e for e in registry['exclusions'] if e['exclusion_id'] == 'EXCL-PILOT-01')
    v1 = next(e for e in registry['exclusions'] if e['exclusion_id'] == 'EXCL-REAL-PILOT-32')
    if file_sha256(raw20) != old20['batch_sha256']:
        raise ValueError('Retained batch hash does not match registry')
    retained = json.loads(raw20.read_text())['rows']
    if len(retained) != 20 or any(r.get('truncated_cells') for r in retained):
        raise ValueError('Require complete, untruncated 20 rows')
    raw_keys = {content_key(item['row']): index for index, item in enumerate(retained)}
    if len(raw_keys) != 20:
        raise ValueError('Duplicate raw20 content requires manual resolution')
    v1_keys = {(r['url_sha256'], r['html_sha256']) for r in v1['samples']}
    if len(v1_keys) != 32:
        raise ValueError('Incomplete/nonunique V1 registry fingerprints')
    matches20, matches_v1, verified = [], [], []
    for relative in shards:
        path = (source_root / relative).resolve()
        if not path.is_relative_to(source_root.resolve()):
            raise ValueError('Shard outside source root')
        manifest, entry = verify_source_file(path, ROOT / 'configs/source_manifest.json', 'phreshphish')
        verified.append({'relative_path': relative, 'sha256': entry['source_metadata_lfs_sha256']})
        offset = 0
        for batch in pq.ParquetFile(path).iter_batches(batch_size=128, columns=['url', 'html']):
            for row in batch.to_pylist():
                pair = content_key(row)
                match = {'relative_path': relative, 'row_offset': offset,
                         'url_sha256': pair[0], 'html_sha256': pair[1]}
                if pair in raw_keys:
                    matches20.append(dict(match, pilot_row_idx=raw_keys[pair]))
                if pair in v1_keys:
                    matches_v1.append(match)
                offset += 1
    complete20 = len(matches20) == 20 and len({r['pilot_row_idx'] for r in matches20}) == 20
    complete_v1 = len(matches_v1) == 32 and len({(r['url_sha256'], r['html_sha256']) for r in matches_v1}) == 32
    report = {'source_revision': manifest['revision'], 'verified_shards': verified,
              'registry_sha256': file_sha256(registry_path), 'raw20_sha256': file_sha256(raw20),
              'raw20_complete': complete20, 'v1_complete': complete_v1,
              'raw20_matches': matches20, 'v1_matches': matches_v1,
              'review_status': 'pending_independent_review', 'v1_status': 'invalidated',
              'training_blocked': True, 'pilot_ready': False}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw20', required=True, type=Path)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--shards', nargs='+', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = recover(args.raw20, args.source_root, args.shards, args.output)
    print('raw20 complete:', report['raw20_complete'], '| V1 complete:', report['v1_complete'],
          '| remains pending; training/pilot closed')
    return 0 if report['raw20_complete'] and report['v1_complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
