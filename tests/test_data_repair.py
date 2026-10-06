"""Self-contained negative probes. All rows here are invented fixtures, not research evidence."""
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import pytest
import pyarrow as pa
import pyarrow.parquet as pq
from phishing.data.exclusion import ExclusionRegistry
from phishing.data.loader import (adapt_source_row_to_record, load_phreshphish_shard,
    build_corpus_index, reconstitute_html_from_locator, filter_eligible_records,
    join_verified_labels_and_filter_eligible, load_phishvn_records)

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / 'data' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reg(tmp_path, blocked=True):
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps({'training_blocked': blocked, 'exclusions': [{'exclusion_id': 'fixture-exclusion', 'mapping_status': 'resolved', 'rows_api_revision_pinned': True, 'samples': [{'url_sha256': '0' * 64}]}]}))
    return ExclusionRegistry(path)


def row(label='phish', html='<p>Fixture</p>', **kwargs):
    return adapt_source_row_to_record(sample_id='fixture-1', source_id='synthetic',
        source_revision='fixture', source_split='unverified', locator={},
        raw_url='https://fixture.example/login', raw_html=html, raw_date=None,
        raw_label=label, **kwargs)


def shard(tmp_path):
    path = tmp_path / 'train-000.parquet'
    pq.write_table(pa.table({'url': ['https://fixture.example/'], 'html': ['<p>Fixture</p>'],
                             'label': [0], 'date': ['2025-01-01']}), path)
    manifest = {'source_id': 'phreshphish', 'source_split': 'train', 'revision': 'a' * 40,
                'files': [{'file_name': path.name, 'relative_path': 'data/' + path.name,
                           'byte_size': path.stat().st_size,
                           'source_metadata_lfs_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}]}
    mf = tmp_path / 'source.json'
    mf.write_text(json.dumps(manifest))
    return path, mf


@pytest.mark.parametrize('label', [0, False, '0', 'false'])
def test_zero_label_is_preserved_but_not_verified(label):
    record = row(label)
    assert record.source_label == 'benign'
    assert record.label_status == 'source_binary_unverified'
    assert record.exclusion_reason is None


def test_real_shard_requires_manifest_checksum_and_registry(tmp_path):
    path, mf = shard(tmp_path)
    registry = reg(tmp_path)
    with pytest.raises(ValueError, match='manifest'):
        list(load_phreshphish_shard(path, exclusion_registry=registry))
    record = list(load_phreshphish_shard(path, source_manifest_path=mf, exclusion_registry=registry))[0]
    assert 'a' * 40 in record.sample_id
    assert record.source_label == 'benign'
    assert record.source_split == 'train'
    with pytest.raises(ValueError):
        list(load_phreshphish_shard(path, source_manifest_path=mf,
                                  exclusion_registry=registry, verify_checksum=False))
    data = json.loads(mf.read_text()); data['files'][0]['source_metadata_lfs_sha256'] = '0' * 64
    mf.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='checksum'):
        list(load_phreshphish_shard(path, source_manifest_path=mf, exclusion_registry=registry))


def test_parquet_adapter_streams_and_locator_rejects_changed_shard(tmp_path, monkeypatch):
    path, mf = shard(tmp_path)
    monkeypatch.setattr(pq, 'read_table', lambda *a, **k: pytest.fail('Full-table read'))
    record = list(load_phreshphish_shard(path, source_manifest_path=mf, exclusion_registry=reg(tmp_path), limit=1))[0]
    assert reconstitute_html_from_locator(record, tmp_path) == '<p>Fixture</p>'
    path.write_bytes(path.read_bytes() + b'changed')
    with pytest.raises(ValueError, match='checksum'):
        reconstitute_html_from_locator(record, tmp_path)


def test_snapshot_and_missing_date_constraints():
    record = row()
    with pytest.raises(ValueError, match='checksum'):
        record.to_prepared_snapshot('<p>changed</p>')
    assert filter_eligible_records([record]) == [record]
    assert filter_eligible_records([record], require_date=True) == []
    with pytest.raises(ValueError, match='capture_mode'):
        row(capture_mode='invented')
    with pytest.raises(ValueError):
        replace(record, raw_html=None).to_prepared_snapshot()


def test_index_read_failure_preserves_previous_run(tmp_path):
    output = tmp_path / 'output'; output.mkdir()
    paths = {key: output / filename for key, filename in
        [('output_index_path', 'corpus_index.jsonl'), ('output_vault_path', 'restricted_vault.jsonl'),
         ('output_manifest_path', 'index_manifest.json')]}
    for path in paths.values():
        path.write_bytes(b'old evidence')
    def broken():
        yield row()
        raise ValueError('late input failure')
    with pytest.raises(ValueError, match='late input'):
        build_corpus_index(broken(), **paths)
    assert all(path.read_bytes() == b'old evidence' for path in paths.values())
    assert not list(tmp_path.glob('.index-staging-*'))
    _, manifest = build_corpus_index([row()], training_blocked=False, **paths)
    assert manifest['ready_for_training'] is False
    assert manifest['training_readiness_status'] == 'audit_only_labels_unverified'


def test_index_publish_failure_rolls_back(tmp_path, monkeypatch):
    import phishing.data.loader as loader
    output = tmp_path / 'output'; output.mkdir()
    paths = {key: output / name for key, name in
             [('output_index_path', 'index'), ('output_vault_path', 'vault'), ('output_manifest_path', 'manifest')]}
    for path in paths.values(): path.write_bytes(b'old')
    real = loader.os.replace
    calls = []
    def fail_second(src, dst):
        calls.append(dst)
        if len(calls) == 2: raise OSError('publish failure')
        return real(src, dst)
    monkeypatch.setattr(loader.os, 'replace', fail_second)
    with pytest.raises(OSError): build_corpus_index([row()], **paths)
    assert all(p.read_bytes() == b'old' for p in paths.values())


def test_verified_join_needs_registry_and_final_label_provenance(tmp_path):
    record = row(); index = [record.to_index_dict()]; vault = {'fixture-1': record.to_vault_dict()}
    with pytest.raises(ValueError): join_verified_labels_and_filter_eligible(index, vault)
    registry = reg(tmp_path, False)
    assert join_verified_labels_and_filter_eligible(index, vault, registry) == []
    vault['fixture-1'].update(label_status='verified_binary', class_label='phishing',
        html_sha256=record.html_sha256, verified_by='reviewer', verification_method='manual',
        verification_evidence='restricted-review-log')
    assert len(join_verified_labels_and_filter_eligible(index, vault, registry)) == 1
    vault['fixture-1']['html_sha256'] = 'wrong'
    assert join_verified_labels_and_filter_eligible(index, vault, registry) == []


def test_phishvn_real_revision_not_invented(tmp_path):
    path = tmp_path / 'dataset.csv'
    path.write_text('url,label,tier,source\nhttps://fixture.example/,malware,bronze,fixture-feed\n')
    with pytest.raises(ValueError, match='manifest'):
        list(load_phishvn_records(path, exclusion_registry=reg(tmp_path)))
    record = list(load_phishvn_records(path, is_real_data_mode=False))[0]
    assert record.source_revision == 'unverified'
    assert record.source_tier == 'bronze'
    assert record.source_sub_source == 'fixture-feed'
    assert 'out_of_scope' in record.exclusion_reason


def test_builder_rejects_missing_exposure_and_detects_group_content_overlap(tmp_path):
    builder = load_script('build_real_pilot_v2')
    registry = reg(tmp_path).path
    evidence = tmp_path / 'prior.json'; evidence.write_text('{"packages": []}')
    with pytest.raises(ValueError, match='exposure evidence'):
        builder.load_blocked_entities(evidence, registry)
    fp = builder.record_fingerprints('https://fixture.example/login', '<p>Fixture</p>')
    empty = {key: set() for key in fp}
    blocked = {key: set() for key in fp}; blocked['group_sha256'].add(fp['group_sha256'])
    with pytest.raises(ValueError, match='group_sha256'): builder.check_deduplication([fp], blocked)
    blocked = {key: set() for key in fp}; blocked['view_content_sha256'].add(fp['view_content_sha256'])
    with pytest.raises(ValueError, match='view_content_sha256'): builder.check_deduplication([fp], blocked)
    with pytest.raises(ValueError): builder.check_deduplication([fp, fp], empty)
    assert builder.record_fingerprints('https://fixture.example/login', ' <p>Fixture</p>')['html_sha256'] != fp['html_sha256']


def test_v2_manifest_cannot_be_opened_by_toggling_approval(tmp_path):
    spec = importlib.util.spec_from_file_location('annotation_cli', ROOT / 'scripts' / 'annotate_cli.py')
    cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
    mf = json.loads((ROOT / 'configs' / 'pilot_manifest_v2.json').read_text())
    mf.update(ready_for_annotation=True, acceptance={'B': 'approved', 'D': 'approved'})
    path = tmp_path / 'manifest.json'; path.write_text(json.dumps(mf))
    with pytest.raises(ValueError, match='BLOCKED'):
        cli.validate_manifest_preflight(path, tmp_path / 'missing-view.json', {})


def test_builder_verified_fixture_end_to_end_pending_and_preflight(tmp_path):
    """Toy Parquet exercises contracts only; it is not a real research pilot."""
    builder = load_script('build_real_pilot_v2')
    repo = tmp_path / 'repo'
    for subdir in ['configs', 'docs', 'data/raw/inputs', 'data']:
        (repo / subdir).mkdir(parents=True, exist_ok=True)
    for relative in ['docs/CODEBOOK_V1.md', 'configs/dictionary_v1.json']:
        shutil.copy2(ROOT / relative, repo / relative)
    source = tmp_path / 'source'; (source / 'data').mkdir(parents=True)
    source_path = source / 'data/train-000.parquet'
    pq.write_table(pa.table({'url': [f'https://fixture-new-{i}.com/login' for i in range(32)],
        'html': [f'<p>Invented new fixture {i}</p>' for i in range(32)],
        'label': [1] * 20 + [0] * 12, 'date': ['2025-01-01'] * 32}), source_path)
    manifest = {'source_id': 'phreshphish', 'source_split': 'train', 'revision': 'a' * 40,
        'files': [{'file_name': source_path.name, 'relative_path': 'data/' + source_path.name,
                   'byte_size': source_path.stat().st_size, 'source_metadata_lfs_sha256': builder.file_hash(source_path)}]}
    (repo / 'configs/source_manifest.json').write_text(json.dumps(manifest))
    registry = {'training_blocked': True, 'exclusions': [{'exclusion_id': 'original', 'samples': [{'url_sha256': '0' * 64}]}]}
    registry_path = repo / 'data/exclusion_registry.json'; registry_path.write_text(json.dumps(registry))
    inputs = repo / 'data/raw/inputs'
    selection = inputs / 'selection.json'
    selection.write_text(json.dumps({'revision': 'a' * 40, 'records': [
        {'relative_path': 'data/train-000.parquet', 'row_offset': i} for i in range(32)]}))
    packages = []
    for kind, count in [('practice', 20), ('v1', 32), ('audit', 20), ('v2_unverified', 32)]:
        path = inputs / (kind + '.json')
        path.write_text(json.dumps([{'url': f'https://fixture-prior-{kind.replace("_", "-")}-{i}.com/',
            'html': f'<p>Invented prior {kind} {i}</p>'} for i in range(count)]))
        packages.append({'kind': kind, 'path': path.name, 'sha256': builder.file_hash(path)})
    prior = inputs / 'prior.json'; prior.write_text(json.dumps({'packages': packages}))
    original_registry = registry_path.read_bytes()
    output = repo / 'data/raw/new-package'
    mf_path = builder.build_real_pilot_v2(selection, source, prior, output, repo_root=repo)
    mf = json.loads(mf_path.read_text()); view_path = output / 'blind_view_pilot_real_v2.json'
    view = json.loads(view_path.read_text())
    assert view['sampling_plan_version'] == mf['sampling_plan_version'] == builder.PLAN
    assert len(view['samples']) == 32 and all(sample['random_subset'] for sample in view['samples'])
    assert mf['source_verification_status'] == 'verified_pinned_train_rows'
    assert mf['acceptance'] == {'B': 'pending', 'D': 'pending'} and not mf['ready_for_annotation']
    assert registry_path.read_bytes() == original_registry
    assert json.loads((output / 'exclusion_registry.proposed.json').read_text())['exclusions'][0] == registry['exclusions'][0]
    with pytest.raises(FileExistsError):
        builder.build_real_pilot_v2(selection, source, prior, output, repo_root=repo)
    spec = importlib.util.spec_from_file_location('fixture_cli', ROOT / 'scripts/annotate_cli.py')
    cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
    with pytest.raises(ValueError, match='BLOCKED'):
        cli.validate_manifest_preflight(mf_path, view_path, view,
            repo / 'docs/CODEBOOK_V1.md', repo / 'configs/dictionary_v1.json')
    # Only this toy fixture is approved to exercise the consumer contract; no repo approval changes.
    mf.update(acceptance={'B': 'approved', 'D': 'approved'}, ready_for_annotation=True,
              exposure_review={'A': 'approved', 'B': 'approved', 'D': 'approved'})
    mf_path.write_text(json.dumps(mf))
    assert cli.validate_manifest_preflight(mf_path, view_path, view,
        repo / 'docs/CODEBOOK_V1.md', repo / 'configs/dictionary_v1.json')['sample_count'] == 32
    damaged = json.loads(selection.read_text()); damaged['records'][0]['html'] = '<p>invented</p>'
    selection.write_text(json.dumps(damaged))
    with pytest.raises(ValueError, match='locators only'):
        builder.load_verified_candidates(selection, source, repo / 'configs/source_manifest.json')


def test_cli_failed_overwrite_keeps_run_and_zero_label(tmp_path):
    fixture = tmp_path / 'rows.jsonl'
    fixture.write_text(json.dumps({'url': 'https://fixture.example/', 'html': '<p>fixture</p>', 'label': 0}) + '\n')
    output = tmp_path / 'run'
    command = [sys.executable, str(ROOT / 'scripts/data/index_corpus.py'), '--source', 'jsonl',
               '--input-path', str(fixture), '--output-dir', str(output), '--allow-unverified-fixture']
    success = subprocess.run(command, capture_output=True, text=True)
    assert success.returncode == 0, success.stderr
    assert json.loads((output / 'restricted_vault.jsonl').read_text())['source_label'] == 'benign'
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    fixture.write_text(fixture.read_text() + 'not valid JSON\n')
    failure = subprocess.run(command + ['--overwrite'], capture_output=True, text=True)
    assert failure.returncode != 0
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}


def test_index_preserves_backup_if_rollback_fails(tmp_path, monkeypatch):
    import phishing.data.loader as loader
    output = tmp_path / "output"; output.mkdir()
    paths = {key: output / name for key, name in [("output_index_path", "index"),
        ("output_vault_path", "vault"), ("output_manifest_path", "manifest")]}
    for path in paths.values(): path.write_bytes(b"old evidence")
    original_replace, original_copy = loader.os.replace, loader.shutil.copy2
    calls = []
    def fail_publish(src, dst):
        calls.append(dst)
        if len(calls) == 2: raise OSError("publish failed")
        return original_replace(src, dst)
    def fail_restore(src, dst):
        if Path(src).parent.name == "backup": raise OSError("restore failed")
        return original_copy(src, dst)
    monkeypatch.setattr(loader.os, "replace", fail_publish)
    monkeypatch.setattr(loader.shutil, "copy2", fail_restore)
    with pytest.raises(RuntimeError, match="retained backup"):
        build_corpus_index([row()], **paths)
    backups = list(tmp_path.glob(".index-staging-*/backup"))
    assert len(backups) == 1
    assert all((backups[0] / p.name).read_bytes() == b"old evidence" for p in paths.values())


@pytest.mark.parametrize("field", ["status", "source_verification_status", "exposure_review"])
def test_common_pilot_gate_blocks_annotation_and_evaluation(field):
    from phishing.annotation.blind_view import assert_pilot_review_status
    mf = {"dataset_id": "REAL-PILOT-32-V2", "sample_count": 32,
        "status": "pending_lead_acceptance", "source_verification_status": "verified_pinned_train_rows",
        "exposure_review": {"A": "approved", "B": "approved", "D": "approved"}}
    mf[field] = "blocked_rebuild_required" if field == "status" else "unverified"
    with pytest.raises(ValueError, match="BLOCKED"): assert_pilot_review_status(mf)
