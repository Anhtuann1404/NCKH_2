#!/usr/bin/env python3
"""Audit script reproducing the exact pairwise union and cardinality of Exclusion Registry (10 Batches).

Outputs:
- Declared items per batch
- Valid (raw_url_sha256, raw_html_sha256) pairs per batch
- Unique pairs in first 9 batches (194)
- Unique pairs in batch 10 (32)
- Intersection between batch 10 and first 9 batches (0)
- Total unique pairs across all 10 batches (226)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def audit_10_batches_pairwise_union(registry_path: Path | str = "data/exclusion_registry.json") -> dict:
    reg_p = Path(registry_path)
    if not reg_p.exists():
        raise FileNotFoundError(f"Exclusion registry not found at '{reg_p}'")

    reg = json.loads(reg_p.read_text(encoding="utf-8"))
    exclusions = reg.get("exclusions", [])

    batch_sets = []
    batch_summaries = []

    for idx, b in enumerate(exclusions):
        eid = b.get("exclusion_id")
        declared = b.get("n_samples") or len(b.get("samples", []))
        samples = b.get("samples", [])
        ref = b.get("restricted_dossier_reference")

        # Ưu tiên đọc mapping từ tệp restricted nếu có tham chiếu (đảm bảo đầy đủ cặp URL/HTML hash)
        if ref:
            ref_path = Path(ref)
            if not ref_path.exists():
                raise FileNotFoundError(
                    f"Restricted dossier '{ref_path}' referenced by '{eid}' does not exist on disk."
                )
            # Verify SHA-256 against registry commitment
            expected_sha = b.get("commitment_sha256")
            actual_sha = hashlib.sha256(ref_path.read_bytes()).hexdigest()
            if expected_sha and actual_sha != expected_sha:
                raise ValueError(
                    f"Integrity error on '{ref_path}': expected {expected_sha}, got {actual_sha}"
                )
            ref_data = json.loads(ref_path.read_text(encoding="utf-8"))
            samples = ref_data.get("mapping", [])

        pairs = []
        for s in samples:
            u = s.get("raw_url_sha256") or s.get("url_sha256")
            h = s.get("raw_html_sha256") or s.get("html_sha256")
            if u and h:
                pairs.append((u.strip().lower(), h.strip().lower()))

        pair_set = set(pairs)
        batch_sets.append(pair_set)
        batch_summaries.append({
            "batch_index": idx + 1,
            "exclusion_id": eid,
            "declared_count": declared,
            "valid_pairs_count": len(pairs),
            "unique_in_batch_count": len(pair_set),
            "intra_batch_duplicates_count": len(pairs) - len(pair_set),
        })

    first_9_union = set().union(*batch_sets[:9])
    batch_10_set = batch_sets[9]
    intersection = first_9_union.intersection(batch_10_set)
    total_union = first_9_union.union(batch_10_set)

    return {
        "batch_breakdown": batch_summaries,
        "total_declared_items_across_10_batches": sum(s["declared_count"] for s in batch_summaries),
        "total_valid_pairs_across_10_batches": sum(s["valid_pairs_count"] for s in batch_summaries),
        "first_9_batches_unique_pairs": len(first_9_union),
        "batch_10_unique_pairs": len(batch_10_set),
        "intersection_between_batch_10_and_first_9_batches": len(intersection),
        "total_unique_pairs_across_all_10_batches": len(total_union),
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    res = audit_10_batches_pairwise_union()

    print("================================================================================")
    print("EXCLUSION REGISTRY 10-BATCH PAIRWISE UNION & CARDINALITY AUDIT")
    print("================================================================================")
    for b in res["batch_breakdown"]:
        print(
            f"Batch {b['batch_index']:2d} | {b['exclusion_id']:50s} | "
            f"declared={b['declared_count']:2d} | valid={b['valid_pairs_count']:2d} | "
            f"unique={b['unique_in_batch_count']:2d} | dups={b['intra_batch_duplicates_count']}"
        )
    print("--------------------------------------------------------------------------------")
    print(f"Tổng mục khai báo theo lô (Declared):      {res['total_declared_items_across_10_batches']} mục")
    print(f"Tổng số cặp mã băm hợp lệ:                {res['total_valid_pairs_across_10_batches']} cặp")
    print(f"Số cặp duy nhất trong 9 lô đầu (Batches 1-9): {res['first_9_batches_unique_pairs']} cặp")
    print(f"Số cặp duy nhất trong Lô 10 (Batch 10):        {res['batch_10_unique_pairs']} cặp")
    print(f"Số giao giữa Lô 10 và 9 lô đầu (Intersection): {res['intersection_between_batch_10_and_first_9_batches']} cặp")
    print(f"Tổng cặp duy nhất toàn registry (10 lô):      {res['total_unique_pairs_across_all_10_batches']} cặp duy nhất")
    print("================================================================================")


if __name__ == "__main__":
    main()
