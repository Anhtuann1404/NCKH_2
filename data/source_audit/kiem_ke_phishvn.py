"""Đếm dữ liệu công khai; đọc ZIP trong bộ nhớ, không chạy mã hay mở website."""
from pathlib import Path
import collections
import csv
import hashlib
import io
import json
import zipfile

base = Path(__file__).resolve().parent
archive = base / 'PhishVN_v3.1.0_open.zip'
with zipfile.ZipFile(archive) as bundle:
    data = bundle.read('data/dataset_url.csv')
    manifest = bundle.read('MANIFEST.txt').decode()
    rows = list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
counts = {key: dict(collections.Counter(row[key] for row in rows))
          for key in ('label', 'source', 'tier', 'scenario', 'split', 'lang')}
result = {
    'version': 'Mendeley v4; PhishVN v3.1.0 open',
    'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
    'csv_sha256': hashlib.sha256(data).hexdigest(),
    'rows': len(rows),
    'counts': counts,
    'unique_domain_field': len({row['domain'] for row in rows}),
    'source_label': dict(collections.Counter(row['source']+'|'+row['label'] for row in rows)),
    'phishing_scenario': dict(collections.Counter(row['scenario'] for row in rows if row['label']=='phishing')),
    'csv_hash_in_manifest': hashlib.sha256(data).hexdigest() in manifest,
    'archive_html_files': sum(name.endswith('.html') for name in bundle.namelist()),
}
(base / 'PhishVN_kiem_ke.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(result, ensure_ascii=False, indent=2))
