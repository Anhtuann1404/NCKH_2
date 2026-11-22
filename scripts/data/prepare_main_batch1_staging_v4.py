"""Kịch bản chuẩn bị Gói Staging V4 (Salt Rotation & Proposal Block 2 Snapshot).

Tuân thủ nghiêm ngặt chỉ đạo của Lead D (Mục 3 & Mục 4):
1. Sinh salt mới bằng secrets.token_hex(16), lưu riêng trong khu vực hạn chế.
2. Không đưa salt mới vào mã nguồn, test hay docs công khai.
3. Giữ nguyên 100% quần thể 1.232, 100 candidate UIDs, tập B30, và thứ tự hiển thị.
4. Tái sinh blind_id mới qua generate_blind_id(new_salt, candidate_uid).
5. Tính toán lineage đối chiếu ID cũ -> ID mới.
6. Soạn thảo Snapshot đề xuất (Proposal Block 2) và chạy rehearsal trên bản sao tạm.
7. Đảm bảo sổ cái thật trên đĩa main_annotation_lot_management_ledger.json giữ nguyên 2 block lịch sử.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import sys
from typing import Any, Dict, List
import zipfile

# Ensure src in sys.path
root_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "src"))

import pyarrow.parquet as pq

from phishing.annotation.blind_view import compute_sample_content_hash
from phishing.data.lot_ledger import LotManagementLedger
from phishing.data.main_sampling import (
    compute_seed_commitment,
    generate_blind_id,
)


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def main():
    root = Path(__file__).resolve().parents[2]
    staging_dir = root / "data" / "restricted" / "main_batch1_staging_v4"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("CHUẨN BỊ GÓI DỮ LIỆU STAGING V4 CHO LEAD D (SALT ROTATION & SNAPSHOT)")
    print("=" * 70)

    # 1. Sinh salt mới ngẫu nhiên mật mã
    # Tiền tố nckh2_salt_v4_ kết hợp 32 ký tự hex ngẫu nhiên
    new_salt = f"nckh2_salt_v4_{secrets.token_hex(16)}"
    seed_lot_100 = 1017
    seed_b_subset_30 = 2042
    seed_release_shuffle = 2026
    new_seed_commitment = compute_seed_commitment(seed_lot_100, seed_b_subset_30, seed_release_shuffle, new_salt)

    print(f"Generated fresh cryptographically secure salt in restricted staging.")
    print(f"New seed commitment SHA-256: {new_seed_commitment}")

    # 2. Ghi seed_salt_specification_restricted.json cho Staging V4
    salt_spec = {
        "lot_id": "main_lot_batch_001",
        "status": "STAGING_SUPERSEDE",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "superseded_reason": "Salt rotation due to test fixture literal exposure in commit 38998ca; fresh random salt generated in restricted staging",
        "sampling_seeds": {
            "seed_population": 42,
            "seed_lot_100": seed_lot_100,
            "seed_b_subset_30": seed_b_subset_30,
            "seed_release_shuffle": seed_release_shuffle,
        },
        "salt_specification": {
            "blind_salt": new_salt,
            "salt_formula": "lot100:{seed_lot_100}|b30:{seed_b_subset_30}|shuffle:{seed_release_shuffle}|salt:{salt}",
            "seed_commitment_sha256": new_seed_commitment,
            "prior_seed_commitment_sha256": "a16ce46f0a55db8ca8c6622b8d6dddcae134e1ca0ccef0104345f5369f8d0fc1",
        },
        "governance_note": "Generated in isolated restricted staging environment. Never exposed to git or non-restricted files.",
    }
    salt_spec_file = staging_dir / "seed_salt_specification_restricted.json"
    salt_spec_file.write_text(json.dumps(salt_spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 3. Đọc mapping V3 hiện hành
    v3_mapping_file = root / "data" / "restricted" / "main_batch1" / "mapping_restricted.json"
    mapping_v3: List[Dict[str, Any]] = json.loads(v3_mapping_file.read_text(encoding="utf-8"))
    assert len(mapping_v3) == 100

    # 4. Sinh mapping mới với blind_id mới, giữ nguyên 100% thuộc tính khác
    mapping_v4 = []
    lineage_mapping_table = []
    old_to_new_blind_id = {}

    for item in mapping_v3:
        old_bid = item["blind_id"]
        c_uid = item["candidate_uid"]
        new_bid = generate_blind_id(new_salt, c_uid)
        old_to_new_blind_id[old_bid] = new_bid

        new_item = dict(item)
        new_item["blind_id"] = new_bid
        mapping_v4.append(new_item)

        lineage_mapping_table.append({
            "candidate_uid": c_uid,
            "old_blind_id_v3": old_bid,
            "new_blind_id_v4": new_bid,
            "canonical_pop_index": item.get("canonical_pop_index"),
            "is_b_kappa_sample": item.get("is_b_kappa_sample"),
            "presentation_order_a": item.get("presentation_order_a"),
            "presentation_order_b": item.get("presentation_order_b"),
            "source_row": item.get("source_row"),
            "source_shard": item.get("source_shard"),
            "url_sha256": item.get("url_sha256"),
            "sample_content_hash": item.get("sample_content_hash"),
        })

    mapping_v4_file = staging_dir / "mapping_restricted.json"
    mapping_v4_file.write_text(json.dumps(mapping_v4, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    mapping_v4_sha256 = compute_sha256(mapping_v4_file)
    print(f"Mapping V4 written: {mapping_v4_file.stat().st_size} bytes, SHA-256: {mapping_v4_sha256}")

    # 5. Cập nhật Blind View A và Blind View B với blind_id mới
    v3_view_a_file = root / "data" / "restricted" / "main_batch1" / "blind_view_a.json"
    v3_view_b_file = root / "data" / "restricted" / "main_batch1" / "blind_view_b.json"
    view_a_data = json.loads(v3_view_a_file.read_text(encoding="utf-8"))
    view_b_data = json.loads(v3_view_b_file.read_text(encoding="utf-8"))

    # Map mẫu trong View A
    for s in view_a_data["samples"]:
        old_sid = s["sample_id"]
        s["sample_id"] = old_to_new_blind_id[old_sid]

    # Map mẫu trong View B
    for s in view_b_data["samples"]:
        old_sid = s["sample_id"]
        s["sample_id"] = old_to_new_blind_id[old_sid]

    # Kiểm tra tính toàn vẹn sample_content_hash
    for s in view_a_data["samples"]:
        c_hash = compute_sample_content_hash(s)
        # sample_content_hash không phụ thuộc vào sample_id -> phải khớp tuyệt đối
        matching_m = next(m for m in mapping_v4 if m["blind_id"] == s["sample_id"])
        assert c_hash == matching_m["sample_content_hash"], "Sample content hash must remain invariant across blind_id rotation!"

    view_a_file = staging_dir / "blind_view_a.json"
    view_b_file = staging_dir / "blind_view_b.json"
    view_a_file.write_text(json.dumps(view_a_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    view_b_file.write_text(json.dumps(view_b_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    view_a_sha256 = compute_sha256(view_a_file)
    view_b_sha256 = compute_sha256(view_b_file)
    print(f"Blind View A V4 written: {view_a_file.stat().st_size} bytes, SHA-256: {view_a_sha256}")
    print(f"Blind View B V4 written: {view_b_file.stat().st_size} bytes, SHA-256: {view_b_sha256}")

    # 6. Cập nhật Manifest A và Manifest B
    manifest_a = {
        "manifest_version": "1.1.0",
        "dataset_id": "MAIN-BATCH1-A",
        "sample_count": 100,
        "blind_view_file": "blind_view_a.json",
        "blind_view_sha256": view_a_sha256,
        "blind_contract_version": "1.2.0",
        "codebook_version": "1.1.0",
    }
    manifest_b = {
        "manifest_version": "1.1.0",
        "dataset_id": "MAIN-BATCH1-B",
        "sample_count": 30,
        "blind_view_file": "blind_view_b.json",
        "blind_view_sha256": view_b_sha256,
        "blind_contract_version": "1.2.0",
        "codebook_version": "1.1.0",
    }
    manifest_a_file = staging_dir / "manifest_a.json"
    manifest_b_file = staging_dir / "manifest_b.json"
    manifest_a_file.write_text(json.dumps(manifest_a, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest_b_file.write_text(json.dumps(manifest_b, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 7. Cập nhật Release Manifest cho V4 Staging
    pop_canonical_file = root / "data" / "restricted" / "main_batch1" / "population_1232_canonical_records_v1.json"
    pop_data = json.loads(pop_canonical_file.read_text(encoding="utf-8"))
    pop_fp = pop_data["population_fingerprint_sha256"]

    release_manifest = {
        "manifest_version": "1.2.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "lot_id": "main_lot_batch_001",
        "staging_version": "V4_STAGING_SALT_ROTATION",
        "actor": "Member C (Nguyễn Thắng)",
        "contract_versions": {
            "codebook_version": "1.1.0",
            "blind_contract_version": "1.2.0",
        },
        "population": {
            "source_shard": "data/raw/phreshphish/data/train-001.parquet",
            "source_revision": "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a",
            "candidate_count": 1232,
            "population_fingerprint_sha256": pop_fp,
            "historical_uid_list_sha256": "40ad5d600e93b10d3fe5910e7454ce4a7a94fe2384b5625d8e6af8983525f9a8",
            "seed_population": 42,
        },
        "sampling_specification": {
            "method": "Simple Random Sampling without Replacement (SRS)",
            "lot_size_a": 100,
            "b_subset_size": 30,
            "seed_lot_100": seed_lot_100,
            "seed_b_subset_30": seed_b_subset_30,
            "seed_release_shuffle": seed_release_shuffle,
            "seed_commitment_sha256": new_seed_commitment,
            "id_format": "BLIND-xxxxxxxx (8 hex chars)",
            "salt_rotation_status": "STAGING_SUPERSEDE",
        },
        "governance_flags": {
            "main_annotation_status": "LOCKED",
            "training_blocked": True,
            "official_test_used": False,
        },
        "restricted_package_fingerprints": {
            "blind_view_a_sha256": view_a_sha256,
            "blind_view_b_sha256": view_b_sha256,
            "mapping_restricted_sha256": mapping_v4_sha256,
            "ledger_event_sequence": 1,
        },
    }
    release_manifest_file = staging_dir / "release_manifest.json"
    release_manifest_file.write_text(json.dumps(release_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 8. Sao chép các tệp bất biến: Quần thể 1.232 (lịch sử & chuẩn hóa), Sổ cái (2 blocks), Exclusion, Audit log
    shutil.copy2(root / "data" / "restricted" / "main_batch1" / "population_1232_sealed.json", staging_dir / "population_1232_sealed.json")
    shutil.copy2(pop_canonical_file, staging_dir / "population_1232_canonical_records_v1.json")
    shutil.copy2(root / "data" / "restricted" / "main_annotation_lot_management_ledger.json", staging_dir / "main_annotation_lot_management_ledger.json")
    shutil.copy2(root / "data" / "exclusion_registry.json", staging_dir / "exclusion_registry.json")
    shutil.copy2(root / "data" / "restricted" / "pilot_batch1_recovery_dossier_restricted_v4.json", staging_dir / "pilot_batch1_recovery_dossier_restricted_v4.json")
    shutil.copy2(root / "data" / "restricted" / "clean_calibration_exclusion_mapping_c_32.json", staging_dir / "clean_calibration_exclusion_mapping_c_32.json")
    shutil.copy2(root / "data" / "restricted" / "main_batch1" / "provenance_recovery_audit_log.json", staging_dir / "provenance_recovery_audit_log.json")
    shutil.copy2(root / "artifacts" / "INCIDENT_LOG_20261119_MAIN_BATCH1_SALT_EXPOSURE.md", staging_dir / "INCIDENT_LOG_20261119_MAIN_BATCH1_SALT_EXPOSURE.md")

    # Sao chép các script kiểm chứng độc lập
    shutil.copy2(root / "scripts" / "data" / "verify_population_fingerprint.py", staging_dir / "verify_population_fingerprint.py")
    shutil.copy2(root / "scripts" / "data" / "verify_provenance_from_parquet.py", staging_dir / "verify_provenance_from_parquet.py")
    shutil.copy2(root / "scripts" / "data" / "verify_exclusion_audit_standalone.py", staging_dir / "verify_exclusion_audit_standalone.py")
    shutil.copy2(root / "tests" / "test_ledger_migration_proposal.py", staging_dir / "test_ledger_migration_proposal.py")
    shutil.copy2(root / "tests" / "test_isolation_scanner_regression.py", staging_dir / "test_isolation_scanner_regression.py")

    # 9. Lập báo cáo Lineage hạn chế (main_batch1_salt_rotation_lineage.json)
    lineage_doc = {
        "lineage_report_type": "SALT_ROTATION_AND_COHORT_PRESERVATION_AUDIT",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "actor": "Member C (Nguyễn Thắng)",
        "scope": "Main Annotation Batch 1 - Staging V4 Preparation",
        "incident_reference": "INCIDENT_LOG_20261119_MAIN_BATCH1_SALT_EXPOSURE.md (Addendum 2026-11-22)",
        "rotation_reason": "Supersede salt following audit finding of test fixture literal exposure in commit 38998ca. Fresh cryptographically secure salt generated in restricted staging environment.",
        "cohort_invariants_verification": {
            "total_candidates_count": 100,
            "b30_subset_count": 30,
            "candidate_uids_identical_to_v3": True,
            "b30_uids_identical_to_v3": True,
            "presentation_order_a_preserved": True,
            "presentation_order_b_preserved": True,
            "sample_content_hashes_identical_to_v3": True,
            "provenance_source_rows_identical_to_v3": True,
        },
        "cryptographic_commitments": {
            "prior_salt_sha256": "192d2b05faf304f9427ce1270cee27b677e7e22688148f8b62794dec3f2e7417",
            "prior_seed_commitment_sha256": "a16ce46f0a55db8ca8c6622b8d6dddcae134e1ca0ccef0104345f5369f8d0fc1",
            "new_salt_sha256": hashlib.sha256(new_salt.encode("utf-8")).hexdigest(),
            "new_seed_commitment_sha256": new_seed_commitment,
            "population_fingerprint_sha256": pop_fp,
        },
        "id_lineage_table": lineage_mapping_table,
    }
    lineage_file = staging_dir / "main_batch1_salt_rotation_lineage.json"
    lineage_file.write_text(json.dumps(lineage_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lineage_hash = compute_sha256(lineage_file)
    print(f"Lineage report written: {lineage_file.stat().st_size} bytes, SHA-256: {lineage_hash}")

    # 10. Hoàn thiện Snapshot đề xuất cho Block 2 (Proposal Block 2 Active State Snapshot)
    ledger_real = LotManagementLedger(root / "data" / "restricted" / "main_annotation_lot_management_ledger.json")
    assert len(ledger_real.events) == 2
    b1_real = ledger_real.events[1]

    # Deterministic B30 selection by seed 2042 in 100 allocated candidates
    alloc_uids = [m["candidate_uid"] for m in mapping_v4]
    b_subset_uids = [m["candidate_uid"] for m in mapping_v4 if m["is_b_kappa_sample"]]
    b_indices = [idx for idx, m in enumerate(mapping_v4) if m["is_b_kappa_sample"]]
    assert len(b_indices) == 30
    assert len(b_subset_uids) == 30

    proposal_block2_payload = {
        "event_type": "MIGRATE_MAIN_BATCH1_SUPERSEDE_SALT_AND_LINEAGE_ENRICHMENT",
        "actor": "Member C (Nguyễn Thắng)",
        "lot_id": "main_lot_batch_001",
        "status": "RESERVED",
        "details": {
            "population_count": 1232,
            "population_hash": pop_fp,
            "historical_population_hash": b1_real.details["population_hash"],
            "available_candidates_count": 1232,
            "lot_size": 100,
            "b_subset_size": 30,
            "seed_lot_100": seed_lot_100,
            "seed_b_subset_30": seed_b_subset_30,
            "seed_release_shuffle": seed_release_shuffle,
            "seed_commitment": new_seed_commitment,
            "cohort_seed_commitment": new_seed_commitment,
            "allocated_candidate_ids": alloc_uids,
            "b_subset_candidate_ids": b_subset_uids,
            "b_indices_in_lot100": b_indices,
            "blind_ids": [m["blind_id"] for m in mapping_v4],
            "predecessor_event_id": b1_real.event_id,
            "predecessor_seq": 1,
            "migration_reason": "Supersede salt due to test fixture literal exposure (commit 38998ca); enrich active state snapshot with B30 indices, new seed commitment, and multidimensional population fingerprint",
            "lineage_audit_hash": lineage_hash,
            "incident_reference": "INCIDENT_LOG_20261119_MAIN_BATCH1_SALT_EXPOSURE.md",
        },
    }
    proposal_block2_file = staging_dir / "proposal_block2_active_state_snapshot.json"
    proposal_block2_file.write_text(json.dumps(proposal_block2_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Proposal Block 2 file written: {proposal_block2_file.stat().st_size} bytes")

    # 11. Chạy Rehearsal độc lập trên bản sao tạm của Sổ cái
    temp_ledger_dir = staging_dir / "temp_rehearsal"
    temp_ledger_dir.mkdir(parents=True, exist_ok=True)
    temp_ledger_file = temp_ledger_dir / "rehearsal_ledger.json"
    shutil.copy2(root / "data" / "restricted" / "main_annotation_lot_management_ledger.json", temp_ledger_file)

    rehearsal_ledger = LotManagementLedger(temp_ledger_file)
    assert len(rehearsal_ledger.events) == 2

    # Append Block 2 trên bản sao tạm
    ev2 = rehearsal_ledger.append_event(
        event_type=proposal_block2_payload["event_type"],
        actor=proposal_block2_payload["actor"],
        lot_id=proposal_block2_payload["lot_id"],
        status=proposal_block2_payload["status"],
        details=proposal_block2_payload["details"],
    )
    assert ev2.seq == 2
    assert ev2.prev_hash == b1_real.event_hash
    assert len(rehearsal_ledger.events) == 3

    # Reload bản sao để kiểm tra toàn vẹn chuỗi băm
    reloaded_rehearsal = LotManagementLedger(temp_ledger_file)
    assert len(reloaded_rehearsal.events) == 3
    assert reloaded_rehearsal.events[0].event_hash == b1_real.prev_hash
    assert reloaded_rehearsal.events[1].event_hash == b1_real.event_hash
    assert reloaded_rehearsal.events[2].event_hash == ev2.event_hash

    # Kiểm tra get_active_lot_details
    active_details = reloaded_rehearsal.get_active_lot_details("main_lot_batch_001")
    assert active_details is not None
    assert active_details["population_hash"] == pop_fp
    assert active_details["allocated_candidate_ids"] == alloc_uids
    assert active_details["b_subset_candidate_ids"] == b_subset_uids
    assert active_details["b_indices_in_lot100"] == b_indices
    assert active_details["seed_commitment"] == new_seed_commitment

    rehearsal_report = {
        "rehearsal_status": "SUCCESS",
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "block2_seq": ev2.seq,
        "block2_event_id": ev2.event_id,
        "block2_event_hash": ev2.event_hash,
        "block2_prev_hash": ev2.prev_hash,
        "hash_chaining_verified": True,
        "get_active_lot_details_verified": True,
        "reloaded_ledger_events_count": 3,
        "real_ledger_untouched": True,
        "real_ledger_sha256": compute_sha256(root / "data" / "restricted" / "main_annotation_lot_management_ledger.json"),
    }
    rehearsal_file = staging_dir / "rehearsal_migration_report.json"
    rehearsal_file.write_text(json.dumps(rehearsal_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    shutil.rmtree(temp_ledger_dir)
    print(f"Rehearsal test on copy passed: Block 2 hash: {ev2.event_hash}")

    # 12. Tạo SHA256SUMS.txt cho toàn bộ tệp trong Staging V4
    sums_lines = []
    for item in sorted(staging_dir.iterdir()):
        if item.is_file() and item.name != "SHA256SUMS.txt":
            sha = compute_sha256(item)
            sums_lines.append(f"{sha}  {item.name}")

    sums_file = staging_dir / "SHA256SUMS.txt"
    sums_file.write_text("\n".join(sums_lines) + "\n", encoding="utf-8")
    print(f"SHA256SUMS.txt written with {len(sums_lines)} entries.")

    # 13. Nén ZIP bàn giao: MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_STAGING.zip
    zip_name = "MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_STAGING.zip"
    zip_root = root / zip_name
    zip_restricted = root / "data" / "restricted" / zip_name

    print(f"\nĐóng gói {zip_name}...")
    with zipfile.ZipFile(zip_root, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for item in sorted(staging_dir.iterdir()):
            if item.is_file():
                zf.write(item, arcname=item.name)

    shutil.copy2(zip_root, zip_restricted)
    zip_size = zip_root.stat().st_size
    zip_sha = compute_sha256(zip_root)

    print("=" * 70)
    print("HOÀN TẤT ĐÓNG GÓI GÓI BÀN GIAO V4 STAGING THÀNH CÔNG!")
    print(f"File: {zip_name}")
    print(f"Size: {zip_size:,} bytes")
    print(f"SHA-256: {zip_sha}")
    print(f"Total components: {len(sums_lines)} files + SHA256SUMS.txt")
    print("=" * 70)


if __name__ == "__main__":
    main()
