"""Synthetic receipt lifecycle checks; no real samples, labels or approvals."""
from pathlib import Path
import importlib.util
import json
import hashlib
from scripts.data.receive_main_batch1 import receive_main_batch1

REPO=Path.cwd()
spec=importlib.util.spec_from_file_location('d_fixture599',REPO/'artifacts/lead_d_review_599c7d9/test_main_599_followup.py')
fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)

def setup_fixture(tmp_path,monkeypatch):
    rest=fixtures.prepare(tmp_path)
    records,_=fixtures.run_cli(tmp_path,rest,monkeypatch)
    # A separate simulated intake starts with no accepted receipt.
    return rest,records,tmp_path/'history_intake'

def test_accepted_attempt_prevents_second_submission_without_d_decision(tmp_path,monkeypatch):
    rest,records,out=setup_fixture(tmp_path,monkeypatch)
    mp=rest/'manifest_a.json'; mf=json.loads(mp.read_text());mf['ready_for_annotation']=False
    mp.write_text(json.dumps(mf))
    first=receive_main_batch1(tmp_path/'fixture_A.jsonl','A',out_root=out,restricted_dir=rest)
    assert first['status']=='rejected'
    mf['ready_for_annotation']=True;mp.write_text(json.dumps(mf))
    accepted=receive_main_batch1(tmp_path/'fixture_A.jsonl','A',out_root=out,restricted_dir=rest)
    assert accepted['status']=='accepted'
    replacement=[dict(r) for r in records['A']]
    replacement[0]['evidence_note']='Different synthetic submission after acceptance'
    new_file=tmp_path/'replacement_fixture_A.jsonl'
    new_file.write_text(''.join(json.dumps(r)+'\n' for r in replacement))
    result=receive_main_batch1(new_file,'A',out_root=out,restricted_dir=rest)
    assert result['status']=='rejected', 'An accepted attempt must lock this annotator/release against another input hash'

def test_rejected_checks_bind_each_changed_manifest_context(tmp_path,monkeypatch):
    rest,_,out=setup_fixture(tmp_path,monkeypatch)
    mp=rest/'manifest_a.json';mf=json.loads(mp.read_text());mf['ready_for_annotation']=False
    mp.write_text(json.dumps(mf))
    a=receive_main_batch1(tmp_path/'fixture_A.jsonl','A',out_root=out,restricted_dir=rest)
    assert a['status']=='rejected'
    old_bytes={p.name:p.read_bytes() for p in (out/'A').glob('*.json')}
    mf['fixture_context']='changed manifest, same rejection category';mp.write_text(json.dumps(mf))
    b=receive_main_batch1(tmp_path/'fixture_A.jsonl','A',out_root=out,restricted_dir=rest)
    assert b['status']=='rejected'
    assert all((out/'A'/n).read_bytes()==raw for n,raw in old_bytes.items())
    attempts=list((out/'A').glob('*.json'))
    assert len(attempts)>=2, 'A new manifest context must not be collapsed into an old rejected receipt'
    assert b.get('manifest_sha256')==hashlib.sha256(mp.read_bytes()).hexdigest()
