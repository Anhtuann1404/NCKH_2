"""Synthetic flow checks for 599c7d9; never uses actual annotation/cohort data."""
import json
from pathlib import Path
import pytest
from phishing.data.main_sampling import run_main_batch1_sampling, supersede_lot_sampling
from phishing.data.lot_ledger import LotManagementLedger
from scripts.data.receive_main_batch1 import receive_main_batch1
from scripts.data.run_main_batch1_pipeline import export_main_batch1
from phishing.annotation.kappa_3x3 import compute_kappa_3x3_from_records
import scripts.annotate_cli as cli

def pool():
    return [{'candidate_uid':f'fixture_{i:04}', 'url':f'https://fixture-{i}.example.test/',
             'html':f'<html><body>Fixture {i}</body></html>','source_row':i,
             'source_shard':'train-001.parquet','source_revision':'fixture-revision'} for i in range(130)]

def prepare(tmp_path):
    export_main_batch1(pool(),tmp_path/'restricted',tmp_path/'public',
        seed_lot_100=11,seed_b_subset_30=22,seed_release_shuffle=33,
        blind_salt='synthetic-fixture-only',ledger_path=tmp_path/'ledger.json')
    rest=tmp_path/'restricted'
    for role in ('a','b'):
        mp=rest/f'manifest_{role}.json'; mf=json.loads(mp.read_text())
        # Simulated fixture approval, not a project authorization.
        mf['ready_for_annotation']=True;mf['acceptance']={'B':'approved','D':'approved'}
        mp.write_text(json.dumps(mf))
    return rest

def run_cli(tmp_path, rest, monkeypatch):
    view_a=json.loads((rest/'blind_view_a.json').read_text())
    labels={s['sample_id']:str(i%3+1) for i,s in enumerate(view_a['samples'])}
    records={}; receipts={}
    for role in ('A','B'):
        vp=rest/f'blind_view_{role.lower()}.json'
        samples=json.loads(vp.read_text())['samples']; cursor=-1;current_label=None
        def answer(prompt=''):
            nonlocal cursor,current_label
            if 'Nhãn phân loại' in prompt:
                cursor+=1;current_label=labels[samples[cursor]['sample_id']];return current_label
            if 'Trạng thái tổ chức' in prompt:return '2' if current_label=='3' else '3'
            if 'Tên dịch vụ' in prompt:return 'Synthetic fixture'
            if 'Kiểu phishing' in prompt:return '5'
            if 'Kiểu hard benign' in prompt:return '0'
            if 'Vai trò danh tính' in prompt:return '3'
            if 'Vai trò tên miền' in prompt:return '5'
            if 'Ghi chú bằng chứng' in prompt:return 'Scripted fixture input only'
            if 'Đánh dấu ca khó' in prompt:return 'n'
            if 'Độ tin cậy' in prompt:return '1'
            raise AssertionError('Unexpected fixture CLI prompt: '+prompt)
        monkeypatch.setattr('builtins.input',answer)
        out=tmp_path/f'fixture_{role}.jsonl'
        cli.annotate_interactive_session(role,vp,out,manifest_path=rest/f'manifest_{role.lower()}.json')
        records[role]=[json.loads(line) for line in out.read_text().splitlines()]
        receipts[role]=receive_main_batch1(out,role,out_root=tmp_path/'intake',restricted_dir=rest)
        assert receipts[role]['status']=='accepted',receipts[role]
    return records,receipts

def test_export_real_cli_intake_and_three_class_kappa(tmp_path,monkeypatch):
    rest=prepare(tmp_path);records,receipts=run_cli(tmp_path,rest,monkeypatch)
    assert len(records['A'])==100 and len(records['B'])==30
    assert all('random_subset' not in r for rs in records.values() for r in rs)
    # Read accepted JSONL bytes instead of pairing an independently assembled label list.
    saved={role:[json.loads(line) for line in Path(rcp['saved_path']).read_text().splitlines()]
           for role,rcp in receipts.items()}
    target=[s['sample_id'] for s in json.loads((rest/'blind_view_b.json').read_text())['samples']]
    result=compute_kappa_3x3_from_records(saved['A'],saved['B'],target_sample_ids=target,bootstrap_iterations=100)
    assert result.sample_count==30
    assert result.kappa==pytest.approx(1.0)

def test_valid_retry_after_supersede_must_preserve_new_ids(tmp_path):
    candidates=pool();ledger=LotManagementLedger(tmp_path/'ledger.json')
    run_main_batch1_sampling(candidates,ledger=ledger,lot_id='fixture_lot',
        seed_lot_100=11,seed_b_subset_30=22,seed_release_shuffle=33,blind_salt='synthetic-old')
    rotated=supersede_lot_sampling(candidates,ledger=ledger,lot_id='fixture_lot',
        new_blind_salt='synthetic-new',new_seed_release_shuffle=44)
    retried=run_main_batch1_sampling(candidates,ledger=ledger,lot_id='fixture_lot',
        seed_lot_100=11,seed_b_subset_30=22,seed_release_shuffle=44,blind_salt='synthetic-new')
    assert retried.lot_100_blind_ids==rotated.lot_100_blind_ids
    assert retried.b_subset_30_blind_ids==rotated.b_subset_30_blind_ids

def test_successful_recheck_keeps_old_accepted_receipt(tmp_path,monkeypatch):
    rest=prepare(tmp_path);_,receipts=run_cli(tmp_path,rest,monkeypatch)
    first=receipts['A']; rp=tmp_path/'intake'/'A'/f"{first['file_sha256']}.receipt.json"
    before=rp.read_bytes();mp=rest/'manifest_a.json';mf=json.loads(mp.read_text())
    mf['fixture_recheck_note']='new verification context';mp.write_text(json.dumps(mf))
    again=receive_main_batch1(tmp_path/'fixture_A.jsonl','A',out_root=tmp_path/'intake',restricted_dir=rest)
    assert again['status']=='accepted'
    assert rp.read_bytes()==before

def test_multiple_rejected_rechecks_keep_all_attempts(tmp_path,monkeypatch):
    rest=prepare(tmp_path);_,receipts=run_cli(tmp_path,rest,monkeypatch)
    mp=rest/'manifest_a.json';mf=json.loads(mp.read_text());mf['ready_for_annotation']=False
    mp.write_text(json.dumps(mf));a=receive_main_batch1(tmp_path/'fixture_A.jsonl','A',out_root=tmp_path/'intake',restricted_dir=rest)
    assert a['status']=='rejected'
    ann=tmp_path/'intake'/'A';prior={p.name:p.read_bytes() for p in ann.glob('*.json')}
    mf['ready_for_annotation']=True;mf['acceptance']={'B':'approved','D':'approved'};mf['blind_contract_version']='9.9.9'
    mp.write_text(json.dumps(mf));b=receive_main_batch1(tmp_path/'fixture_A.jsonl','A',out_root=tmp_path/'intake',restricted_dir=rest)
    assert b['status']=='rejected'
    assert all((ann/name).read_bytes()==content for name,content in prior.items())
