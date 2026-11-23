"""Synthetic regressions: raw bytes must remain authoritative over supplied hashes."""
import copy,hashlib
import pytest
from phishing.data.main_sampling import compute_population_fingerprint,run_main_batch1_sampling
from phishing.data.lot_ledger import LotManagementLedger
from phishing.annotation.blind_view import normalize_url

def pool():
 return [{'candidate_uid':f'fake-{i:04d}','url':f'https://fake-{i}.example.test/','html':f'<html><body>Artificial payload {i}</body></html>','source_row':i,'source_shard':'fake.parquet','source_revision':'fake-revision'} for i in range(130)]

def test_changed_raw_html_cannot_hide_behind_stale_supplied_hash():
 candidates=pool()
 for c in candidates:c['html_sha256']=hashlib.sha256(c['html'].encode()).hexdigest()
 original=compute_population_fingerprint(candidates)
 altered=copy.deepcopy(candidates);altered[0]['html']='<html><body>CHANGED RAW PAYLOAD</body></html>'
 try:changed=compute_population_fingerprint(altered)
 except ValueError:return  # Rejecting inconsistent raw/hash input is also safe.
 assert changed!=original,'Raw HTML changed but stale html_sha256 hid the change from the fingerprint'

def test_metadata_only_rerun_cannot_silently_replace_views_with_empty_text(tmp_path):
 candidates=pool();ledger=LotManagementLedger(tmp_path/'fixture_ledger.json')
 params=dict(seed_lot_100=17,seed_b_subset_30=28,seed_release_shuffle=39,blind_salt='fixture-only-v41-guard')
 original=run_main_batch1_sampling(candidates,ledger=ledger,**params)
 assert any(s['page_text'] for s in original.blind_view_a)
 metadata=[]
 for c in candidates:
  m={k:v for k,v in c.items() if k!='html'}
  m.update({'url_raw':c['url'],'url_normalized':normalize_url(c['url']),'url_sha256':hashlib.sha256(c['url'].encode()).hexdigest(),'html_sha256':hashlib.sha256(c['html'].encode()).hexdigest()})
  metadata.append(m)
 with pytest.raises(ValueError):
  run_main_batch1_sampling(metadata,ledger=ledger,**params)
