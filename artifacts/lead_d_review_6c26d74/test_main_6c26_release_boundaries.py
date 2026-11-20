"""Independent synthetic boundary checks; no real Main samples or approvals."""
import json
from pathlib import Path
import pytest
from phishing.annotation.blind_view import compute_sample_content_hash, validate_annotation_record, assert_no_label_leak
from phishing.data.main_sampling import run_main_batch1_sampling, supersede_lot_sampling
from phishing.data.lot_ledger import LotManagementLedger
from scripts.data.receive_main_batch1 import receive_main_batch1, verify_main_batch1_records
from scripts.data.verify_git_isolation import scan_public_docs_for_leaks
import scripts.data.run_main_batch1_pipeline as runner

def pool(n=130):
    return [{'candidate_uid':f'fixture_{i:04}', 'url':f'https://fixture-{i}.example.test/',
             'html':f'<html><body>Fixture {i}</body></html>', 'source_row':i,
             'source_shard':'train-001.parquet','source_revision':'fixture-revision'} for i in range(n)]

def sample(candidates,ledger,seed=11):
    return run_main_batch1_sampling(candidates,ledger=ledger,lot_id='fixture_lot',
        seed_lot_100=seed,seed_b_subset_30=22,seed_release_shuffle=33,
        blind_salt='synthetic-fixture-only')

def export(tmp_path):
    return runner.export_main_batch1(pool(),tmp_path/'restricted',tmp_path/'public',
        seed_lot_100=11,seed_b_subset_30=22,seed_release_shuffle=33,
        blind_salt='synthetic-fixture-only',ledger_path=tmp_path/'ledger.json')

def intake_fixture(tmp_path,annotator='A',approved=True):
    export(tmp_path)
    rest=tmp_path/'restricted'; role=annotator.lower()
    vp=rest/f'blind_view_{role}.json'; mp=rest/f'manifest_{role}.json'
    view=json.loads(vp.read_text()); mf=json.loads(mp.read_text())
    if approved:
        # Explicitly simulated acceptance for fixture tests, never a project approval.
        mf['ready_for_annotation']=True;mf['acceptance']={'B':'approved','D':'approved'}
        mp.write_text(json.dumps(mf))
    records=[]
    for s in view['samples']:
        records.append({'annotator_id':annotator,'sample_id':s['sample_id'],'pass_id':1,
          'class_label':'insufficient_evidence','primary_org_status':'unknown',
          'catalog_status':'unresolved','observed_service':'unknown','org_targets':[],
          'primary_org':'unknown','identity_role':'unclear','domain_role':'unverified',
          'evidence_note':'Synthetic fixture only','seconds_spent':1.0,'difficult_case':False,
          'codebook_version':'1.1.0','org_evidence':[],'primary_phishing_type':None,
          'hard_benign_type':None,'confidence':'low','pause_count':0,'paused_seconds':0.0,
          'blind_contract_version':'1.2.0','dataset_id':mf['dataset_id'],
          'dataset_hash':mf['blind_view_sha256'],'codebook_hash':mf['codebook_sha256'],
          'sample_content_hash':compute_sample_content_hash(s),
          'sampling_plan_version':mf['sampling_plan_version'],'timestamp_utc':'2026-11-20T00:00:00Z',
          'is_dry_run':False,'is_synthetic':False})
    inp=tmp_path/'fixture_submission.jsonl'
    inp.write_text(''.join(json.dumps(r)+'\n' for r in records))
    return mp,vp,records,inp

@pytest.mark.parametrize('annotator',['A','B'])
def test_valid_main_intake_positive_control(tmp_path,annotator):
    mp,vp,rs,_=intake_fixture(tmp_path,annotator)
    assert verify_main_batch1_records(rs,annotator,mp,vp)['sample_count']==len(rs)

def test_third_isolation_scan_failure_must_not_return_success(tmp_path,monkeypatch):
    outcomes=iter([{'overall_status':'PASS'},{'overall_status':'PASS'},{'overall_status':'FAIL'}])
    monkeypatch.setattr(runner,'verify_git_isolation',lambda *a,**k:next(outcomes))
    with pytest.raises(RuntimeError):export(tmp_path)

def test_publish_io_error_preserves_all_previous_files(tmp_path,monkeypatch):
    restricted=tmp_path/'restricted';restricted.mkdir()
    expected={name:b'previous sealed fixture' for name in ('mapping_restricted.json','blind_view_a.json','blind_view_b.json','population_1232_sealed.json','manifest_a.json','manifest_b.json')}
    for n,b in expected.items():(restricted/n).write_bytes(b)
    original=runner.os.replace
    replaced=0
    def fail_on_view(src,dst):
        nonlocal replaced
        if Path(dst).parent==restricted:
            replaced+=1
            if replaced==2:raise OSError('Injected synthetic publication error after first replacement')
        return original(src,dst)
    monkeypatch.setattr(runner.os,'replace',fail_on_view)
    with pytest.raises(OSError):export(tmp_path)
    assert {n:(restricted/n).read_bytes() for n in expected}==expected

def test_supersede_without_sealed_b_subset_must_stop(tmp_path):
    ledger=LotManagementLedger(tmp_path/'ledger.json');cs=pool();sample(cs,ledger)
    details=dict(ledger.get_active_lot_details('fixture_lot'))
    details.pop('b_subset_candidate_ids');details.pop('b_indices_in_lot100')
    ledger.append_event('SIMULATE_LEGACY_DETAILS','FIXTURE','fixture_lot','RESERVED',details)
    with pytest.raises(ValueError):
        supersede_lot_sampling(cs,ledger=ledger,lot_id='fixture_lot',
            new_blind_salt='synthetic-rotation',new_seed_release_shuffle=44)

def test_rerun_after_supersede_still_rejects_changed_seeds(tmp_path):
    ledger=LotManagementLedger(tmp_path/'ledger.json');cs=pool();sample(cs,ledger)
    supersede_lot_sampling(cs,ledger=ledger,lot_id='fixture_lot',
        new_blind_salt='synthetic-rotation',new_seed_release_shuffle=44)
    with pytest.raises(ValueError):sample(cs,ledger,seed=999)

def test_pending_manifest_cannot_accept_official_intake(tmp_path):
    mp,vp,rs,_=intake_fixture(tmp_path,approved=False)
    with pytest.raises(ValueError):verify_main_batch1_records(rs,'A',mp,vp)

def test_wrong_pass_cannot_enter_main_pass1_intake(tmp_path):
    mp,vp,rs,_=intake_fixture(tmp_path)
    for r in rs:r['pass_id']=2
    with pytest.raises(ValueError):verify_main_batch1_records(rs,'A',mp,vp)

def test_string_dry_run_flag_cannot_bypass_intake(tmp_path):
    mp,vp,rs,_=intake_fixture(tmp_path)
    for r in rs:r['is_dry_run']='true'
    with pytest.raises(ValueError):verify_main_batch1_records(rs,'A',mp,vp)

def test_reverification_cannot_overwrite_accepted_receipt(tmp_path):
    mp,vp,rs,inp=intake_fixture(tmp_path)
    out=tmp_path/'intake';rest=tmp_path/'restricted'
    first=receive_main_batch1(inp,'A',out_root=out,restricted_dir=rest)
    assert first['status']=='accepted'
    receipt=out/'A'/f"{first['file_sha256']}.receipt.json";before=receipt.read_bytes()
    mp.write_text('{}')
    again=receive_main_batch1(inp,'A',out_root=out,restricted_dir=rest)
    assert again['status']=='rejected'
    assert receipt.read_bytes()==before

def test_invalid_main_timestamp_must_be_rejected(tmp_path):
    _,_,rs,_=intake_fixture(tmp_path)
    r=dict(rs[0],timestamp_utc='definitely-not-a-timestamp')
    with pytest.raises(ValueError):validate_annotation_record(r)

def test_nested_random_subset_cannot_leak_in_main_envelope():
    env={'blind_contract_version':'1.2.0','samples':[{'sample_id':'BLIND-0123abcd',
         'url':'https://fixture.example.test/','page_text':'Fixture','structure_summary':{},
         'blind_contract_version':'1.2.0','codebook_version':'1.1.0','translation_provided':False}],
         'release_info':{'random_subset':True}}
    with pytest.raises(ValueError):assert_no_label_leak(env)

def test_isolation_report_must_redact_detected_secret(tmp_path):
    scripts=tmp_path/'scripts';scripts.mkdir();secret='synthetic-operating-secret-fixture'
    (scripts/'runner.py').write_text('DEFAULT_BLIND_SALT = '+repr(secret)+'\n')
    result=scan_public_docs_for_leaks([scripts])
    assert result['status']=='FAIL'
    assert secret not in json.dumps(result)
