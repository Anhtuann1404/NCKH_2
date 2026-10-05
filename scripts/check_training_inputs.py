"""Validate fixture input artifacts without fitting any model."""
import argparse
import json
from pathlib import Path
import tempfile

from phishing.training.readiness import check_training_inputs, sha256


def write_demo_inputs(root):
    root = Path(root)
    html = root / 'fixture.html'
    html.write_text('<html><body>Invented input check fixture</body></html>', encoding='utf-8')
    ids = [f'fixture-{i}' for i in range(6)]
    artifacts = {
        'index': [{'sample_id': sid, 'exclusion_reason': None, 'capture_mode': 'stored_html',
                   'html_path': html.name, 'html_sha256': sha256(html)} for sid in ids],
        'labels': [{'sample_id': sid, 'final': True, 'class_label': 'phishing' if i % 2 else 'benign'} for i, sid in enumerate(ids)],
        'groups': {sid: f'fixture-group-{i // 2}' for i, sid in enumerate(ids)},
        'split': dict(variant='M3', seed=17, train_ids=ids[:2], validation_ids=ids[2:4], test_ids=ids[4:]),
        'exclusion': {'excluded_ids': ['reserved-fixture']},
    }
    manifest = {'contract_version': 'training-input-fixture-v0', 'scope': 'synthetic_fixture_only', 'artifacts': {}}
    for name, value in artifacts.items():
        path = root / f'{name}.json'
        path.write_text(json.dumps(value), encoding='utf-8')
        manifest['artifacts'][name] = {'path': path.name, 'sha256': sha256(path)}
    path = root / 'manifest.json'
    path.write_text(json.dumps(manifest), encoding='utf-8')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--manifest', type=Path)
    mode.add_argument('--demo-fixture', action='store_true')
    args = parser.parse_args()
    try:
        if args.demo_fixture:
            with tempfile.TemporaryDirectory(prefix='nckh-input-check-') as temp:
                result = check_training_inputs(write_demo_inputs(temp))
        else:
            result = check_training_inputs(args.manifest)
    except (ValueError, OSError, KeyError, TypeError, AttributeError):
        print(json.dumps({'status': 'blocked', 'research_training_allowed': False,
                          'reason': 'Input contract, integrity, labels, groups or split failed. See DEVELOPMENT.md.'}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
