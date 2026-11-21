import copy
from pathlib import Path
import pytest
from phishing.annotation.blind_view import assert_no_label_leak, validate_annotation_record
from phishing.data.lot_ledger import LotManagementLedger
from phishing.data.main_sampling import run_main_batch1_sampling
from scripts.data.verify_git_isolation import scan_public_docs_for_leaks

def pool(n=300):
    return [{'candidate_uid':f'fixture_{i:04}', 'url':f'https://fixture-{i}.example.test/',
             'html':f'<html><body>Fixture {i}</body></html>', 'source_row':i,
             'source_shard':'train-001.parquet','source_revision':'fixture-revision'} for i in range(n)]

def sample(candidates, ledger, lot='fixture_lot1', seed=11):
    return run_main_batch1_sampling(candidates, ledger=ledger, lot_id=lot,
             seed_lot_100=seed, seed_b_subset_30=22, seed_release_shuffle=33,
             blind_salt='synthetic-fixture-salt-not-operational')

def record():
    return {'annotator_id':'A','sample_id':'BLIND-0123abcd','pass_id':1,
            'class_label':'insufficient_evidence','primary_org_status':'unknown',
            'catalog_status':'unresolved','observed_service':'unknown','org_targets':[],
            'primary_org':'unknown','identity_role':'unclear','domain_role':'unverified',
            'evidence_note':'Synthetic empty snapshot','seconds_spent':1.0,
            'difficult_case':False,'codebook_version':'1.1.0','org_evidence':[],
            'primary_phishing_type':None,'hard_benign_type':None,'confidence':'low',
            'pause_count':0,'paused_seconds':0.0,'blind_contract_version':'1.2.0',
            'dataset_id':'MAIN-FIXTURE','dataset_hash':'a'*64,'codebook_hash':'b'*64,
            'sample_content_hash':'c'*64,'timestamp_utc':'2026-11-19T00:00:00Z',
            'sampling_plan_version':'FIXTURE-PLAN'}

def test_same_lot_changed_seed_must_not_resample(tmp_path):
    ledger=LotManagementLedger(tmp_path/'ledger.json'); candidates=pool()
    sample(candidates, ledger)
    with pytest.raises(ValueError):
        sample(candidates, ledger, seed=99)

def test_same_lot_retry_preserves_cohort_after_other_lot_allocation(tmp_path):
    ledger=LotManagementLedger(tmp_path/'ledger.json'); candidates=pool()
    first=sample(candidates, ledger)
    sample(candidates, ledger, lot='fixture_lot2')
    again=sample(candidates, ledger)
    assert again.lot_100_blind_ids == first.lot_100_blind_ids

def test_main_record_missing_contract_cannot_downgrade_to_legacy():
    data=record(); del data['blind_contract_version']; data['random_subset']=True
    with pytest.raises(ValueError): validate_annotation_record(data)

def test_main_record_missing_provenance_must_be_rejected():
    data=record()
    for key in ('dataset_id','dataset_hash','codebook_hash','sample_content_hash','timestamp_utc'):
        del data[key]
    with pytest.raises(ValueError): validate_annotation_record(data)

def test_main_envelope_cannot_embed_legacy_random_subset():
    env={'blind_contract_version':'1.2.0', 'samples':[
        {'sample_id':'SMP-999','url':'https://fixture.example.test/',
         'random_subset':True,'codebook_version':'1.1.0','translation_provided':False}]}
    with pytest.raises(ValueError): assert_no_label_leak(env)

def test_unknown_envelope_contract_cannot_embed_main_samples():
    env={'blind_contract_version':'9.9.9','samples':[
        {'sample_id':'BLIND-0123abcd','url':'https://fixture.example.test/',
         'blind_contract_version':'1.2.0','codebook_version':'1.1.0','translation_provided':False}]}
    with pytest.raises(ValueError): assert_no_label_leak(env)

def test_new_hardcoded_secret_is_not_mistaken_for_clean_scan(tmp_path):
    scripts=tmp_path/'scripts'; scripts.mkdir()
    (scripts/'runner.py').write_text('DEFAULT_BLIND_SALT = "synthetic-new-operating-secret"\n')
    assert scan_public_docs_for_leaks([str(scripts)])['status']=='FAIL'

def test_main_mapping_requires_actual_source_row(tmp_path):
    candidates=pool(120)
    for c in candidates: del c['source_row']
    with pytest.raises(ValueError): sample(candidates, LotManagementLedger(tmp_path/'ledger.json'))

def test_failed_post_export_scan_must_not_overwrite_previous_package(tmp_path, monkeypatch):
    import scripts.data.run_main_batch1_pipeline as runner
    restricted=tmp_path/'restricted'; restricted.mkdir()
    previous=restricted/'blind_view_a.json'; previous.write_bytes(b'previous sealed fixture package')
    outcomes=iter([{'overall_status':'PASS'}, {'overall_status':'FAIL'}])
    monkeypatch.setattr(runner,'verify_git_isolation',lambda *a,**k:next(outcomes))
    with pytest.raises(RuntimeError,match='EXPORT BLOCKED'):
        runner.export_main_batch1(pool(120), restricted, tmp_path/'public',
             seed_lot_100=11,seed_b_subset_30=22,seed_release_shuffle=33,
             blind_salt='synthetic-fixture-salt-not-operational',ledger_path=tmp_path/'ledger.json')
    assert previous.read_bytes()==b'previous sealed fixture package'
