"""Read-only metadata checks and proposal rehearsal on COPY; no sample labels."""
from pathlib import Path
import sys,zipfile,json,hashlib,tempfile,copy,subprocess
ROOT=Path('/private/tmp/nckh-main-ac2cf1d-review');sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'scripts')]
import annotate_cli
import pyarrow.parquet as pq
from phishing.data.lot_ledger import LotManagementLedger
from phishing.data.main_sampling import run_main_batch1_sampling,compute_population_fingerprint,compute_seed_commitment
base=Path('/Users/yingjunn_/Downloads')
with zipfile.ZipFile(base/'MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_2_STAGING.zip') as z:raw={n:z.read(n) for n in z.namelist()};crc=z.testzip()
with zipfile.ZipFile(base/'MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_1_STAGING.zip') as z:oldraw={n:z.read(n) for n in z.namelist()}
d={n:json.loads(v) for n,v in raw.items() if n.endswith('.json')};sha=lambda b:hashlib.sha256(b).hexdigest();matches=[]
for line in raw['SHA256SUMS.txt'].decode().splitlines():
 expected,n=line.split(None,1);matches.append(expected.lower()==sha(raw[n.strip()]))
out={'date':'2026-11-23','zip_bytes':(base/'MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_2_STAGING.zip').stat().st_size,'zip_sha256':sha((base/'MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_2_STAGING.zip').read_bytes()),'crc_ok':crc is None,'component_hashes_matched':sum(matches),'component_hashes_total':len(matches),'reported_commit':'ac2cf1d82d9a742ec0f5e9af81e0ce116fdfbe3d','reported_commit_matches_remote':True,'core_fix_commit':'fb487540aa6c877553eeb9e0978437642a4173b1'}
keep=['blind_view_a.json','blind_view_b.json','mapping_restricted.json','population_1232_canonical_records_v1.json','population_1232_sealed.json','exclusion_registry.json','pilot_batch1_recovery_dossier_restricted_v4.json','clean_calibration_exclusion_mapping_c_32.json','provenance_recovery_audit_log.json','main_annotation_lot_management_ledger.json']
out['unchanged_from_v4_1']={n:raw[n]==oldraw[n] for n in keep}
S=d['seed_salt_specification_restricted.json'];oldS=json.loads(oldraw['seed_salt_specification_restricted.json']);out['salt_and_selection_seeds_unchanged']=S['salt_specification']['blind_salt']==oldS['salt_specification']['blind_salt'] and S['sampling_seeds']==oldS['sampling_seeds']
required=['dataset_id','sample_count','sampling_plan_version','codebook_version','codebook_status','dictionary_version','dictionary_status','acceptance','ready_for_annotation','blind_view_sha256','codebook_sha256','dictionary_sha256']
with tempfile.TemporaryDirectory() as tmp:
 tmp=Path(tmp);checks={}
 for role in ['a','b']:
  mf=d[f'manifest_{role}.json'];vp=tmp/f'view_{role}.json';mp=tmp/f'manifest_{role}.json';op=tmp/f'out_{role}.jsonl';vp.write_bytes(raw[f'blind_view_{role}.json']);mp.write_bytes(raw[f'manifest_{role}.json'])
  r={'all_mandatory_fields_present':all(k in mf for k in required),'view_hash_matches':mf['blind_view_sha256']==sha(vp.read_bytes()),'codebook_hash_matches':mf['codebook_sha256']==sha((ROOT/'docs/CODEBOOK_V1_1.md').read_bytes()),'dictionary_hash_matches':mf['dictionary_sha256']==sha((ROOT/'configs/dictionary_v1.json').read_bytes()),'acceptance':mf['acceptance'],'ready':mf['ready_for_annotation']}
  try:annotate_cli.annotate_interactive_session(role.upper(),vp,op,manifest_path=mp);r['unexpected_open']=True
  except ValueError as e:r.update({'blocked_for_pending': 'CHƯA NGHIỆM THU' in str(e),'output_created':op.exists()})
  checks[role]=r
 out['role_manifests']=checks
 lp=tmp/'copy.json';lp.write_bytes(raw['main_annotation_lot_management_ledger.json']);ledger=LotManagementLedger(lp);old_events=copy.deepcopy(ledger.events);proposal=d['proposal_block2_active_state_snapshot.json'];hist=ledger.events[1].details['seed_commitment'];params=S['sampling_seeds'];salt=S['salt_specification']['blind_salt'];new=compute_seed_commitment(params['seed_lot_100'],params['seed_b_subset_30'],params['seed_release_shuffle'],salt)
 out['proposal_commitments']={'cohort_matches_block1':proposal['details']['cohort_seed_commitment']==hist,'release_commitment_matches_new':proposal['details']['seed_commitment']==new,'commitments_distinct':hist!=new}
 ledger.append_event(**proposal);ledger=LotManagementLedger(lp);snapshot=lp.read_bytes()
 records=d['population_1232_canonical_records_v1.json']['records']
 expected_a=d['blind_view_a.json']['samples'];expected_b=d['blind_view_b.json']['samples']
 args=dict(seed_lot_100=params['seed_lot_100'],seed_b_subset_30=params['seed_b_subset_30'],seed_release_shuffle=params['seed_release_shuffle'],blind_salt=salt,ledger=ledger)
 source=Path('/private/tmp/nckh-train001-source-20261123/train-001.parquet')
 if source.exists():
  assert sha(source.read_bytes())=='260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74'
  table=pq.read_table(source,columns=['url','html']);urls=table['url'].to_pylist();htmls=table['html'].to_pylist();records=d['population_1232_canonical_records_v1.json']['records'];candidates=[{'candidate_uid':r['candidate_uid'],'url':urls[r['source_row']],'html':htmls[r['source_row']] or '', 'source_row':r['source_row'],'source_shard':r['source_shard'],'source_revision':r['source_revision']} for r in records]
  args=dict(seed_lot_100=params['seed_lot_100'],seed_b_subset_30=params['seed_b_subset_30'],seed_release_shuffle=params['seed_release_shuffle'],blind_salt=salt,ledger=ledger)
  a=run_main_batch1_sampling(candidates,**args);b=run_main_batch1_sampling(candidates,**args)
  expected_a=d['blind_view_a.json']['samples'];expected_b=d['blind_view_b.json']['samples']
  out['raw_source_exact_proposal_rehearsal']={'old_events_unchanged':ledger.events[:2]==old_events,'events_after_two_reruns':len(ledger.events),'ledger_copy_unchanged_by_reruns':lp.read_bytes()==snapshot,'a_view_matches_package':a.blind_view_a==expected_a,'b_view_matches_package':a.blind_view_b==expected_b,'two_reruns_equal':a.blind_view_a==b.blind_view_a and a.blind_view_b==b.blind_view_b,'applied_to_real_ledger':False}
 else:
  out['raw_source_exact_proposal_rehearsal']={'repeated_this_session':False,'reason':'Previously verified temporary Parquet is no longer present; source-related artifacts and views remain byte-identical to V4'}
 meta=[{'candidate_uid':r['candidate_uid'],'url':r['url_raw'],'url_raw':r['url_raw'],'url_normalized':r['url_normalized'],'url_sha256':r['url_sha256'],'html_sha256':r['html_sha256'],'source_row':r['source_row'],'source_shard':r['source_shard'],'source_revision':r['source_revision']} for r in records]
 try:
  run_main_batch1_sampling(meta,**args)
  out['metadata_only_rejection']={'rejected':False}
 except ValueError as e:
  out['metadata_only_rejection']={'rejected':True,'error_type':'ValueError','ledger_copy_still_unchanged':lp.read_bytes()==snapshot}
 out['text_counts']={'a_total':len(expected_a),'a_nonempty':sum(bool(r['page_text'].strip()) for r in expected_a),'a_empty':sum(not r['page_text'].strip() for r in expected_a),'b_total':len(expected_b),'b_nonempty':sum(bool(r['page_text'].strip()) for r in expected_b)}
out['governance']=d['release_manifest.json']['governance_status']
Path('/private/tmp/main_v42_metadata_summary.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(json.dumps(out,indent=2,ensure_ascii=False))
