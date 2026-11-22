"""Fixture test verifying Proposal A for Main Annotation Ledger Migration (Block 2).

This test proves:
1. Adding Successor Block (Block 2) with full active state schema preserves cryptographic hash-chaining.
2. get_active_lot_details retrieves the complete state required by sampler.
3. Rerun on migrated ledger is strictly idempotent: preserves cohort 100, B30 subset, and appends no new blocks.
4. Tampering with commitments triggers fail-closed behavior.
"""

import copy
import hashlib
import json
from pathlib import Path
import random
import pytest

from phishing.data.lot_ledger import LotManagementLedger
from phishing.data.main_sampling import (
    compute_population_fingerprint,
    compute_seed_commitment,
    generate_blind_id,
    run_main_batch1_sampling,
)


def test_ledger_migration_proposal_a_full_state_idempotent(tmp_path: Path):
    # 1. Load real ledger history (Block 0 and Block 1)
    real_ledger_path = Path("data/restricted/main_annotation_lot_management_ledger.json")
    assert real_ledger_path.exists()
    real_data = json.loads(real_ledger_path.read_text(encoding="utf-8"))
    assert len(real_data["events"]) == 2

    # Copy to tmp_path
    test_ledger_file = tmp_path / "test_ledger.json"
    test_ledger_file.write_text(json.dumps(real_data, indent=2, ensure_ascii=False), encoding="utf-8")

    ledger = LotManagementLedger(test_ledger_file)
    assert len(ledger.events) == 2
    b1 = ledger.events[1]
    assert b1.seq == 1
    assert b1.lot_id == "main_lot_batch_001"

    # 2. Build candidates pool for fixture test
    alloc_uids = b1.details["allocated_candidate_ids"]
    assert len(alloc_uids) == 100
    candidates = []
    for uid in alloc_uids:
        uid_clean = uid.replace("_", "-")
        candidates.append({
            "candidate_uid": uid,
            "url": f"http://example-{uid_clean}.org",
            "html": f"<html><body>{uid}</body></html>",
            "source_row": 1,
            "source_shard": "train-001.parquet",
            "source_revision": "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a",
        })

    new_pop_fp = compute_population_fingerprint(candidates)
    salt = "nckh2_main_batch1_blind_salt_secure_2026"
    seed_commit = compute_seed_commitment(1017, 2042, 2026, salt)

    # Calculate deterministic B30 indices via seed 2042
    rng_b = random.Random(2042)
    b_indices = rng_b.sample(range(100), 30)
    b_indices.sort()
    b_uids = [alloc_uids[i] for i in b_indices]

    enriched_details = {
        "population_count": 100,
        "population_hash": new_pop_fp,
        "historical_population_hash": b1.details["population_hash"],
        "available_candidates_count": 100,
        "lot_size": 100,
        "b_subset_size": 30,
        "seed_lot_100": 1017,
        "seed_b_subset_30": 2042,
        "seed_release_shuffle": 2026,
        "seed_commitment": seed_commit,
        "cohort_seed_commitment": seed_commit,
        "allocated_candidate_ids": alloc_uids,
        "b_subset_candidate_ids": b_uids,
        "b_indices_in_lot100": b_indices,
        "blind_ids": [generate_blind_id(salt, uid) for uid in alloc_uids],
        "predecessor_event_id": b1.event_id,
        "predecessor_seq": 1,
        "migration_reason": "Enrich active lot state with B30 subset indices and multidimensional population fingerprint",
        "lineage_audit_hash": "5ca140df1831198354527c9cc708caf158258e97865450d02fc555a1a98b027a",
    }

    # Append Block 2
    ev2 = ledger.append_event(
        event_type="MIGRATE_MAIN_BATCH1_LINEAGE_ENRICHMENT",
        actor="Member C (Nguyễn Thắng)",
        lot_id="main_lot_batch_001",
        status="RESERVED",
        details=enriched_details,
    )

    assert ev2.seq == 2
    assert ev2.prev_hash == b1.event_hash
    assert len(ledger.events) == 3

    # Reload ledger to verify cryptographic integrity
    reloaded_ledger = LotManagementLedger(test_ledger_file)
    assert len(reloaded_ledger.events) == 3
    assert reloaded_ledger.events[0].event_hash == real_data["events"][0]["event_hash"]
    assert reloaded_ledger.events[1].event_hash == real_data["events"][1]["event_hash"]

    # 3. Test get_active_lot_details
    active_details = reloaded_ledger.get_active_lot_details("main_lot_batch_001")
    assert active_details is not None
    assert active_details["population_hash"] == new_pop_fp
    assert active_details["allocated_candidate_ids"] == alloc_uids
    assert active_details["b_subset_candidate_ids"] == b_uids
    assert active_details["b_indices_in_lot100"] == b_indices

    # 4. Tampering check: mismatched seed must fail-closed
    with pytest.raises(ValueError, match="seed_commitment không khớp"):
        run_main_batch1_sampling(
            candidates,
            seed_lot_100=9999,  # Mismatched seed
            seed_b_subset_30=2042,
            seed_release_shuffle=2026,
            blind_salt=salt,
            ledger=reloaded_ledger,
            lot_id="main_lot_batch_001",
        )

    # 5. Success check: valid rerun must be idempotent, return preserved cohort and append NO new block
    res = run_main_batch1_sampling(
        candidates,
        seed_lot_100=1017,
        seed_b_subset_30=2042,
        seed_release_shuffle=2026,
        blind_salt=salt,
        ledger=reloaded_ledger,
        lot_id="main_lot_batch_001",
    )
    assert len(res.lot_100_blind_ids) == 100
    assert len(res.b_subset_30_blind_ids) == 30
    assert len(res.blind_view_a) == 100
    assert len(res.blind_view_b) == 30
    assert len(res.mapping_restricted) == 100
    assert len(reloaded_ledger.events) == 3  # No new block appended (idempotent)!
