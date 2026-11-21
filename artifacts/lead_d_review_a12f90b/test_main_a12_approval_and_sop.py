"""Independent synthetic checks of replacement authority and executable SOP."""
import ast
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT=Path.cwd()
spec=importlib.util.spec_from_file_location('fixture599',ROOT/'artifacts/lead_d_review_599c7d9/test_main_599_followup.py')
fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)
from scripts.data.receive_main_batch1 import receive_main_batch1

def fixture_submission(tmp_path,monkeypatch):
    rest=fixtures.prepare(tmp_path)
    records,_=fixtures.run_cli(tmp_path,rest,monkeypatch)
    return rest,records

def test_unverified_replacement_reference_cannot_unlock_submission(tmp_path,monkeypatch):
    rest,records=fixture_submission(tmp_path,monkeypatch)
    changed=[dict(r) for r in records['A']]
    changed[0]['evidence_note']='Different synthetic submission without any Lead D decision'
    replacement=tmp_path/'replacement_fixture.jsonl'
    replacement.write_text(''.join(json.dumps(r)+'\n' for r in changed))
    result=receive_main_batch1(replacement,'A',out_root=tmp_path/'intake',restricted_dir=rest,
        d_replacement_approval='NOT_AN_EXISTING_OR_APPROVED_D_DECISION')
    assert result['status']=='rejected','An arbitrary string must not stand in for a verified scoped replacement decision'

def test_documented_replacement_cli_flag_is_supported():
    result=subprocess.run([sys.executable,str(ROOT/'scripts/data/receive_main_batch1.py'),'--help'],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert '--d-replacement-approval' in result.stdout

def sop_code():
    text=(ROOT/'docs/QUY_TRINH_KIEM_TRA_INTAKE_MAIN_BATCH1.md').read_text()
    blocks=re.findall(r'```python\s*\n(.*?)```',text,re.S)
    assert len(blocks)==1
    return blocks[0]

def test_exact_documented_kappa_script_runs_on_accepted_fixture(tmp_path,monkeypatch):
    rest,_=fixture_submission(tmp_path,monkeypatch)
    code=sop_code()
    shutil.copytree(rest,tmp_path/'data/restricted/main_batch1')
    shutil.copytree(tmp_path/'intake',tmp_path/'data/labels/intake_main_batch1')
    monkeypatch.chdir(tmp_path)
    # Execute the SOP verbatim on artificial accepted files only.
    exec(compile(code,str(ROOT/'docs/QUY_TRINH_KIEM_TRA_INTAKE_MAIN_BATCH1.md'),'exec'),{})

def test_sop_preserves_locked_bootstrap_count():
    tree=ast.parse(sop_code())
    counts=[kw.value.value for node in ast.walk(tree) if isinstance(node,ast.Call)
        for kw in node.keywords if kw.arg=='bootstrap_iterations' and isinstance(kw.value,ast.Constant)]
    # Main plan §2: B=1,000; B=100 is reserved for the synthetic smoke test.
    assert counts==[1000]
