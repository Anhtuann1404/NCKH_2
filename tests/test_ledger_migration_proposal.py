"""Fixture test verifying Proposal A for Main Annotation Ledger Migration (Block 2).

PURPOSE & DESIGN (100% SYNTHETIC & SELF-CONTAINED):
- This test operates exclusively on synthetic dummy data (in-memory / tmp_path).
- ZERO reads or dependencies on data/restricted/ or operational secrets.
- Suitable for independent QA execution by Annotator B (Minh) on a clean checkout.

VERIFIED BEHAVIORS:
1. Successor Block (Block 2) with full active state schema preserves cryptographic hash-chaining.
2. get_active_lot_details retrieves the complete state required by sampler (allocated_candidate_ids, B30, etc.).
3. Tampering checks:
   - Mismatched seed triggers fail-closed ValueError.
   - Mismatched population fingerprint triggers fail-closed ValueError.
4. Idempotent rerun:
   - Valid rerun retrieves preserved cohort without re-sampling.
   - Running twice strictly preserves state and appends NO new blocks.
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

# SYNTHETIC TEST CONSTANTS (Explicitly dummy, non-operational)
SYNTHETIC_LOT_ID = "synthetic_lot_proposal_a_001"
SYNTHETIC_DUMMY_SEED_LOT_100 = 7101
SYNTHETIC_DUMMY_SEED_B_SUBSET_30 = 8202
SYNTHETIC_DUMMY_SEED_RELEASE_SHUFFLE = 9303
SYNTHETIC_DUMMY_SALT = "synthetic_dummy_salt_for_proposal_a_test_only_xyz"


def _create_synthetic_candidate_pool(count: int = 150):
    """Generate a deterministic synthetic candidate pool with no external dependencies."""
    candidates = []
    for i in range(count):
        uid = f"cand_synthetic_{i:04d}_{hashlib.sha256(f'syn:{i}'.encode()).hexdigest()[:8]}"
        candidates.append({
            "candidate_uid": uid,
            "url": f"http://synthetic-domain-{i:04d}.test/page",
            "html": f"<html><body><h1>Synthetic Domain {i}</h1></body></html>",
            "source_row": i,
            "source_shard": "synthetic-shard-001.parquet",
            "source_revision": "0000000000000000000000000000000000000000",
        })
    return candidates


def test_synthetic_ledger_migration_proposal_a_idempotent(tmp_path: Path):
    """Test Proposal A on a 100% synthetic ledger and synthetic candidate pool."""
    test_ledger_file = tmp_path / "synthetic_test_ledger.json"
    ledger = LotManagementLedger(test_ledger_file)
    assert len(ledger.events) == 1
    assert ledger.events[0].seq == 0
    assert ledger.events[0].event_id == "GENESIS"

    # 1. Create synthetic candidate pool
    candidates = _create_synthetic_candidate_pool(150)
    pop_fp = compute_population_fingerprint(candidates)
    seed_commit = compute_seed_commitment(
        SYNTHETIC_DUMMY_SEED_LOT_100,
        SYNTHETIC_DUMMY_SEED_B_SUBSET_30,
        SYNTHETIC_DUMMY_SEED_RELEASE_SHUFFLE,
        SYNTHETIC_DUMMY_SALT,
    )

    # 2. Append Block 1: Baseline Lot Reservation (seq: 1)
    # Deterministic selection of 100 candidates from pool
    rng_lot = random.Random(SYNTHETIC_DUMMY_SEED_LOT_100)
    lot_100_candidates = rng_lot.sample(candidates, 100)
    alloc_uids = [c["candidate_uid"] for c in lot_100_candidates]

    b1_details = {
        "population_count": len(candidates),
        "population_hash": pop_fp,
        "available_candidates_count": len(candidates),
        "lot_size": 100,
        "b_subset_size": 30,
        "seed_lot_100": SYNTHETIC_DUMMY_SEED_LOT_100,
        "seed_b_subset_30": SYNTHETIC_DUMMY_SEED_B_SUBSET_30,
        "seed_release_shuffle": SYNTHETIC_DUMMY_SEED_RELEASE_SHUFFLE,
        "seed_commitment": seed_commit,
        "allocated_candidate_ids": alloc_uids,
    }

    ev1 = ledger.append_event(
        event_type="SAMPLE_LOT_RESERVATION",
        actor="Synthetic Tester",
        lot_id=SYNTHETIC_LOT_ID,
        status="RESERVED",
        details=b1_details,
    )
    assert ev1.seq == 1
    assert ev1.prev_hash == ledger.events[0].event_hash
    assert len(ledger.events) == 2

    # 3. Build Block 2: Proposal A - Successor State Snapshot (seq: 2)
    # Deterministic B30 selection using seed_b_subset_30
    rng_b = random.Random(SYNTHETIC_DUMMY_SEED_B_SUBSET_30)
    b_indices = rng_b.sample(range(100), 30)
    b_indices.sort()
    b_uids = [alloc_uids[i] for i in b_indices]

    enriched_details = {
        "population_count": len(candidates),
        "population_hash": pop_fp,
        "historical_population_hash": pop_fp,
        "available_candidates_count": len(candidates),
        "lot_size": 100,
        "b_subset_size": 30,
        "seed_lot_100": SYNTHETIC_DUMMY_SEED_LOT_100,
        "seed_b_subset_30": SYNTHETIC_DUMMY_SEED_B_SUBSET_30,
        "seed_release_shuffle": SYNTHETIC_DUMMY_SEED_RELEASE_SHUFFLE,
        "seed_commitment": seed_commit,
        "cohort_seed_commitment": seed_commit,
        "allocated_candidate_ids": alloc_uids,
        "b_subset_candidate_ids": b_uids,
        "b_indices_in_lot100": b_indices,
        "blind_ids": [generate_blind_id(SYNTHETIC_DUMMY_SALT, uid) for uid in alloc_uids],
        "predecessor_event_id": ev1.event_id,
        "predecessor_seq": 1,
        "migration_reason": "Synthetic fixture proposal A verification",
        "lineage_audit_hash": hashlib.sha256(b"synthetic_lineage_dummy").hexdigest(),
    }

    ev2 = ledger.append_event(
        event_type="MIGRATE_MAIN_BATCH1_LINEAGE_ENRICHMENT",
        actor="Synthetic Tester",
        lot_id=SYNTHETIC_LOT_ID,
        status="RESERVED",
        details=enriched_details,
    )
    assert ev2.seq == 2
    assert ev2.prev_hash == ev1.event_hash
    assert len(ledger.events) == 3

    # 4. Verify cryptographic integrity on reload
    reloaded_ledger = LotManagementLedger(test_ledger_file)
    assert len(reloaded_ledger.events) == 3
    assert reloaded_ledger.events[1].event_hash == ev1.event_hash
    assert reloaded_ledger.events[2].event_hash == ev2.event_hash

    # 5. Verify get_active_lot_details retrieves the full active state
    active_details = reloaded_ledger.get_active_lot_details(SYNTHETIC_LOT_ID)
    assert active_details is not None
    assert active_details["population_hash"] == pop_fp
    assert active_details["allocated_candidate_ids"] == alloc_uids
    assert active_details["b_subset_candidate_ids"] == b_uids
    assert active_details["b_indices_in_lot100"] == b_indices

    # 6. Tampering check 1: Mismatched seed must fail-closed
    with pytest.raises(ValueError, match="seed_commitment không khớp"):
        run_main_batch1_sampling(
            candidates,
            seed_lot_100=9999,  # Intentionally wrong seed
            seed_b_subset_30=SYNTHETIC_DUMMY_SEED_B_SUBSET_30,
            seed_release_shuffle=SYNTHETIC_DUMMY_SEED_RELEASE_SHUFFLE,
            blind_salt=SYNTHETIC_DUMMY_SALT,
            ledger=reloaded_ledger,
            lot_id=SYNTHETIC_LOT_ID,
        )

    # 7. Tampering check 2: Mismatched population fingerprint must fail-closed
    tampered_candidates = copy.deepcopy(candidates)
    tampered_candidates[0]["html"] = "<html><body>TAMPERED_CONTENT</body></html>"
    with pytest.raises(ValueError, match="population_hash không khớp"):
        run_main_batch1_sampling(
            tampered_candidates,
            seed_lot_100=SYNTHETIC_DUMMY_SEED_LOT_100,
            seed_b_subset_30=SYNTHETIC_DUMMY_SEED_B_SUBSET_30,
            seed_release_shuffle=SYNTHETIC_DUMMY_SEED_RELEASE_SHUFFLE,
            blind_salt=SYNTHETIC_DUMMY_SALT,
            ledger=reloaded_ledger,
            lot_id=SYNTHETIC_LOT_ID,
        )

    # 8. Success check: Rerun on migrated ledger is strictly idempotent
    res1 = run_main_batch1_sampling(
        candidates,
        seed_lot_100=SYNTHETIC_DUMMY_SEED_LOT_100,
        seed_b_subset_30=SYNTHETIC_DUMMY_SEED_B_SUBSET_30,
        seed_release_shuffle=SYNTHETIC_DUMMY_SEED_RELEASE_SHUFFLE,
        blind_salt=SYNTHETIC_DUMMY_SALT,
        ledger=reloaded_ledger,
        lot_id=SYNTHETIC_LOT_ID,
    )
    assert len(res1.lot_100_blind_ids) == 100
    assert len(res1.b_subset_30_blind_ids) == 30
    assert len(reloaded_ledger.events) == 3  # No new block appended!

    # 9. Second rerun must still append NO new block
    res2 = run_main_batch1_sampling(
        candidates,
        seed_lot_100=SYNTHETIC_DUMMY_SEED_LOT_100,
        seed_b_subset_30=SYNTHETIC_DUMMY_SEED_B_SUBSET_30,
        seed_release_shuffle=SYNTHETIC_DUMMY_SEED_RELEASE_SHUFFLE,
        blind_salt=SYNTHETIC_DUMMY_SALT,
        ledger=reloaded_ledger,
        lot_id=SYNTHETIC_LOT_ID,
    )
    assert res1.lot_100_blind_ids == res2.lot_100_blind_ids
    assert res1.b_subset_30_blind_ids == res2.b_subset_30_blind_ids
    assert len(reloaded_ledger.events) == 3  # Still exactly 3 blocks!
