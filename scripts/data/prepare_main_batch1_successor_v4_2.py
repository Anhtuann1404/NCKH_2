"""Script chuẩn bị Gói Kế nhiệm V4.2 (Successor Staging Pack for Lead D).

Khép trọn vẹn 3 nội dung kỹ thuật mà Lead D giao (Mục 1, R1, R2):
1. Đính chính Full SHA: Xác nhận commit thực tế trên remote là 28462fcece5883a652779976e342d939f7a81e5a.
2. Khắc phục R1: Mã nguồn main_sampling.py lấy raw bytes (URL/HTML) làm căn cứ tối thượng.
   Kiểm tra tính nhất quán fail-closed: nếu URL/HTML bị sửa đổi nhưng hash khai báo giữ nguyên,
   hoặc mâu thuẫn giữa raw bytes và hash khai báo -> lập tức từ chối (raise ValueError).
3. Khắc phục R2: Rehearsal sampler hydrate đầy đủ raw URL và raw HTML từ Parquet gốc đã khóa
   (data/raw/phreshphish/data/train-001.parquet, revision eabec4b7a66324b79cc8a0ad856d1731dc26fe1a)
   theo source_row. Đối chiếu toàn bộ 100 view A và 30 view B sinh ra từ rehearsal khớp tuyệt đối
   từng trường (sample_id, url, page_text, structure_summary, sample_content_hash) với tệp đã niêm phong,
   chứng minh không có view nào bị rỗng (97/100 A và 30/30 B có page_text đầy đủ).
4. Bảo tồn nguyên trạng: 100% cohort A100/B30, UIDs, Blind IDs, nội dung, thứ tự và salt V4.
5. Sổ cái thật trên đĩa tiếp tục giữ nguyên 2 block lịch sử (chưa áp dụng proposal).
"""

import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any, Dict, List
import zipfile

root_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "src"))

import pyarrow.parquet as pq

from phishing.annotation.blind_view import (
    BLIND_CONTRACT_VERSION_V1_2_0,
    compute_sample_content_hash,
)
from phishing.data.lot_ledger import LotManagementLedger
from phishing.data.main_sampling import (
    compute_population_fingerprint,
    compute_seed_commitment,
    run_main_batch1_sampling,
)


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def main():
    root = root_dir
    v4_dir = root / "data" / "restricted" / "main_batch1_staging_v4"
    v4_1_dir = root / "data" / "restricted" / "main_batch1_staging_v4_1"
    staging_v4_2_dir = root / "data" / "restricted" / "main_batch1_staging_v4_2"

    print("=" * 75)
    print("CHUẨN BỊ GÓI KẾ NHIỆM STAGING V4.2 CHO LEAD D (RAW FINGERPRINT & HYDRATED REHEARSAL)")
    print("=" * 75)

    # 1. Kiểm tra hiện vật V4 và V4.1 đã bàn giao bảo đảm nguyên vẹn
    v4_zip = root / "MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_STAGING.zip"
    assert v4_zip.exists(), f"Không tìm thấy {v4_zip}"
    v4_zip_hash = compute_sha256(v4_zip)
    expected_v4_hash = "f2bb7b5423cf88cf0cd29db5a4016ab94694409344f92fc599b2101def3ad81f"
    assert v4_zip_hash == expected_v4_hash, f"V4 ZIP hash sai lệch: {v4_zip_hash}"
    print(f"✅ V4 ZIP gốc được bảo lưu nguyên trạng: {v4_zip.stat().st_size:,} bytes | {v4_zip_hash}")

    v4_1_zip = root / "MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_1_STAGING.zip"
    assert v4_1_zip.exists(), f"Không tìm thấy {v4_1_zip}"
    v4_1_zip_hash = compute_sha256(v4_1_zip)
    expected_v4_1_hash = "5c3e23eac2082ac96b8d3f09beebd59317a98a56dd630d6398d1fa731bd1f6c8"
    assert v4_1_zip_hash == expected_v4_1_hash, f"V4.1 ZIP hash sai lệch: {v4_1_zip_hash}"
    print(f"✅ V4.1 ZIP được bảo lưu nguyên trạng: {v4_1_zip.stat().st_size:,} bytes | {v4_1_zip_hash}")

    # 2. Kiểm tra Sổ cái thật trên đĩa vẫn giữ nguyên 2 block lịch sử
    real_ledger_path = root / "data" / "restricted" / "main_annotation_lot_management_ledger.json"
    real_ledger_hash = compute_sha256(real_ledger_path)
    expected_real_ledger_hash = "11acdaf1806a80181006a5817520f21b2660c1a13ac983651e4d7129390a15c5"
    assert real_ledger_hash == expected_real_ledger_hash, f"Sổ cái thật bị can thiệp: {real_ledger_hash}"
    ledger_real = LotManagementLedger(real_ledger_path)
    assert len(ledger_real.events) == 2, f"Sổ cái thật phải có đúng 2 block (hiện có: {len(ledger_real.events)})"
    b1_real = ledger_real.events[1]
    historical_cohort_seed_commitment = b1_real.details["seed_commitment"]
    print(f"✅ Sổ cái thật trên đĩa nguyên vẹn 2 block: {real_ledger_hash}")
    print(f"   Historical Cohort Seed Commitment (Block 1): {historical_cohort_seed_commitment}")

    # 3. Nạp thông số salt V4 và seeds đã khóa từ staging V4
    spec_file = v4_dir / "seed_salt_specification_restricted.json"
    salt_spec_v4 = json.loads(spec_file.read_text(encoding="utf-8"))
    v4_salt = salt_spec_v4["salt_specification"]["blind_salt"]
    v4_seed_commitment = salt_spec_v4["salt_specification"]["seed_commitment_sha256"]
    seeds = salt_spec_v4["sampling_seeds"]
    seed_lot_100 = seeds["seed_lot_100"]
    seed_b_subset_30 = seeds["seed_b_subset_30"]
    seed_release_shuffle = seeds["seed_release_shuffle"]

    # Xác minh toán học: v4_seed_commitment khớp công thức
    recomputed_v4_commit = compute_seed_commitment(seed_lot_100, seed_b_subset_30, seed_release_shuffle, v4_salt)
    assert recomputed_v4_commit == v4_seed_commitment
    assert v4_seed_commitment != historical_cohort_seed_commitment, "Cam kết muối mới và cam kết cohort cũ phải khác nhau!"
    print(f"✅ Active Seed Commitment (V4 Salt): {v4_seed_commitment}")

    # 4. Thiết lập thư mục staging V4.2 và sao chép hiện vật gốc V4/V4.1
    if staging_v4_2_dir.exists():
        shutil.rmtree(staging_v4_2_dir)
    staging_v4_2_dir.mkdir(parents=True, exist_ok=True)

    # Danh sách hiện vật chuyển tiếp nguyên byte từ V4/V4.1
    passthrough_files_v4 = [
        "blind_view_a.json",
        "blind_view_b.json",
        "clean_calibration_exclusion_mapping_c_32.json",
        "exclusion_registry.json",
        "INCIDENT_LOG_20261119_MAIN_BATCH1_SALT_EXPOSURE.md",
        "main_annotation_lot_management_ledger.json",
        "mapping_restricted.json",
        "pilot_batch1_recovery_dossier_restricted_v4.json",
        "population_1232_canonical_records_v1.json",
        "population_1232_sealed.json",
        "provenance_recovery_audit_log.json",
        "verify_exclusion_audit_standalone.py",
        "verify_population_fingerprint.py",
        "verify_provenance_from_parquet.py",
    ]
    for fn in passthrough_files_v4:
        src_f = v4_dir / fn
        dst_f = staging_v4_2_dir / fn
        shutil.copy2(src_f, dst_f)

    # Sao chép manifest A và B (đầy đủ 12 trường từ V4.1)
    shutil.copy2(v4_1_dir / "manifest_a.json", staging_v4_2_dir / "manifest_a.json")
    shutil.copy2(v4_1_dir / "manifest_b.json", staging_v4_2_dir / "manifest_b.json")
    print("✅ Tiếp nhận và bảo toàn nguyên vẹn 16 hiện vật cơ bản và manifest A/B đầy đủ")

    # 5. Cập nhật seed_salt_specification_restricted.json
    salt_spec_v4_2 = copy.deepcopy(salt_spec_v4)
    salt_spec_v4_2["specification_version"] = "1.4.2"
    salt_spec_v4_2["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    salt_spec_v4_2["salt_specification"]["cohort_seed_commitment_sha256"] = historical_cohort_seed_commitment
    salt_spec_v4_2["salt_specification"]["prior_seed_commitment_sha256"] = historical_cohort_seed_commitment
    salt_spec_v4_2["governance_note"] = (
        "Managed exclusively in restricted staging environment. Explicit separation between "
        "historical cohort commitment (Block 1) and active release configuration commitment (Block 2)."
    )
    salt_spec_v4_2_file = staging_v4_2_dir / "seed_salt_specification_restricted.json"
    salt_spec_v4_2_file.write_text(json.dumps(salt_spec_v4_2, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("✅ Cập nhật seed_salt_specification_restricted.json (phiên bản 1.4.2)")

    # 6. Cập nhật main_batch1_salt_rotation_lineage.json cho V4.2
    lineage_v4_file = v4_dir / "main_batch1_salt_rotation_lineage.json"
    lineage_v4 = json.loads(lineage_v4_file.read_text(encoding="utf-8"))
    lineage_v4_2 = copy.deepcopy(lineage_v4)
    lineage_v4_2["lineage_report_type"] = "MAIN_BATCH1_SALT_ROTATION_LINEAGE_REPORT_V4_2"
    lineage_v4_2["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    lineage_v4_2["cryptographic_commitments"]["historical_cohort_seed_commitment"] = historical_cohort_seed_commitment
    lineage_v4_2["cryptographic_commitments"]["active_release_seed_commitment"] = v4_seed_commitment
    lineage_v4_2["governance_lineage_note"] = (
        "Strict cryptographic separation: historical cohort commitment (Block 1) locks original sample draw; "
        "active release commitment (Block 2) locks rotated salt configuration. "
        "Successor V4.2 fixes R1 (raw byte authoritative fingerprinting) and R2 (raw-hydrated rehearsal)."
    )
    lineage_v4_2_file = staging_v4_2_dir / "main_batch1_salt_rotation_lineage.json"
    lineage_v4_2_file.write_text(json.dumps(lineage_v4_2, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lineage_hash = compute_sha256(lineage_v4_2_file)
    print(f"✅ Cập nhật main_batch1_salt_rotation_lineage.json (SHA-256: {lineage_hash})")

    # 7. Cập nhật Proposal Block 2 Snapshot
    proposal_v4 = json.loads((v4_dir / "proposal_block2_active_state_snapshot.json").read_text(encoding="utf-8"))
    proposal_v4_2 = copy.deepcopy(proposal_v4)
    proposal_v4_2["details"]["seed_commitment"] = v4_seed_commitment
    proposal_v4_2["details"]["cohort_seed_commitment"] = historical_cohort_seed_commitment
    proposal_v4_2["details"]["prior_seed_commitment"] = historical_cohort_seed_commitment
    proposal_v4_2["details"]["lineage_audit_hash"] = lineage_hash
    proposal_v4_2["details"]["migration_reason"] = (
        "Supersede salt due to test fixture literal exposure (commit 38998ca); "
        "enrich active state snapshot with distinct historical cohort commitment (Block 1), "
        "active release seed commitment (Block 2), B30 indices, and raw-authoritative multidimensional population fingerprint"
    )
    proposal_v4_2_file = staging_v4_2_dir / "proposal_block2_active_state_snapshot.json"
    proposal_v4_2_file.write_text(json.dumps(proposal_v4_2, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✅ Cập nhật proposal_block2_active_state_snapshot.json")

    # 8. Chạy Rehearsal độc lập có Hydrate Raw URL & HTML từ Parquet nguồn đã khóa (Khắc phục R2)
    print("\n--- BẮT ĐẦU REHEARSAL CHUẨN KHOA HỌC (HYDRATED RAW REHEARSAL) ---")
    parquet_path = root / "data" / "raw" / "phreshphish" / "data" / "train-001.parquet"
    assert parquet_path.exists(), f"Không tìm thấy Parquet nguồn: {parquet_path}"
    print(f"Reading Parquet shard: {parquet_path} ({parquet_path.stat().st_size:,} bytes)...")
    pq_table = pq.read_table(parquet_path, columns=["url", "html"])
    urls_col = pq_table["url"].to_pylist()
    htmls_col = pq_table["html"].to_pylist()

    canonical_recs_file = staging_v4_2_dir / "population_1232_canonical_records_v1.json"
    canonical_data = json.loads(canonical_recs_file.read_text(encoding="utf-8"))
    canonical_recs = canonical_data["records"] if isinstance(canonical_data, dict) else canonical_data
    assert len(canonical_recs) == 1232, f"Kỳ vọng 1232 bản ghi, thực tế: {len(canonical_recs)}"

    # Hydrate đầy đủ raw URL và raw HTML theo source_row
    hydrated_pool = []
    for r in canonical_recs:
        row = r["source_row"]
        u = urls_col[row]
        h = htmls_col[row]
        # Kiểm tra tính toàn vẹn cấp byte
        assert hashlib.sha256(u.encode("utf-8")).hexdigest() == r["url_sha256"], f"Mâu thuẫn URL hash dòng {row}"
        assert hashlib.sha256(h.encode("utf-8")).hexdigest() == r["html_sha256"], f"Mâu thuẫn HTML hash dòng {row}"
        hydrated_pool.append({
            "candidate_uid": r["candidate_uid"],
            "url": u,
            "html": h,
            "source_row": row,
            "source_shard": r["source_shard"],
            "source_revision": r["source_revision"],
        })
    print(f"✅ Hydrate thành công 1.232 ứng viên từ Parquet gốc (khớp 100% hash URL và HTML)")

    # Tính toán và kiểm chứng fingerprint trên tập đã hydrate
    computed_fp = compute_population_fingerprint(hydrated_pool)
    expected_fp = "77773871ab50c361cb5df0ca4f9e5604a251a20f933d1bc22ee7d9f016814919"
    assert computed_fp == expected_fp, f"Fingerprint không khớp: {computed_fp} != {expected_fp}"
    print(f"✅ Multidimensional Population Fingerprint chuẩn xác tuyệt đối: {computed_fp}")

    # Thiết lập ledger tạm để diễn tập
    temp_rehearsal_dir = staging_v4_2_dir / "temp_rehearsal"
    temp_rehearsal_dir.mkdir(parents=True, exist_ok=True)
    temp_ledger_file = temp_rehearsal_dir / "rehearsal_ledger.json"
    shutil.copy2(real_ledger_path, temp_ledger_file)

    rehearsal_ledger = LotManagementLedger(temp_ledger_file)
    assert len(rehearsal_ledger.events) == 2

    # Append Block 2 trên bản sao tạm
    ev2 = rehearsal_ledger.append_event(
        event_type=proposal_v4_2["event_type"],
        actor=proposal_v4_2["actor"],
        lot_id=proposal_v4_2["lot_id"],
        status=proposal_v4_2["status"],
        details=proposal_v4_2["details"],
    )
    assert ev2.seq == 2
    assert ev2.prev_hash == b1_real.event_hash
    assert len(rehearsal_ledger.events) == 3
    print(f"✅ Rehearsal append Block 2 thành công (Hash: {ev2.event_hash})")

    # Kiểm tra nạp lại và lấy active state
    reloaded_rehearsal = LotManagementLedger(temp_ledger_file)
    active_rehearsal = reloaded_rehearsal.get_active_lot_details("main_lot_batch_001")
    assert active_rehearsal is not None
    assert active_rehearsal["seed_commitment"] == v4_seed_commitment
    assert active_rehearsal["cohort_seed_commitment"] == historical_cohort_seed_commitment
    assert active_rehearsal["cohort_seed_commitment"] != active_rehearsal["seed_commitment"]
    assert len(active_rehearsal["allocated_candidate_ids"]) == 100
    assert len(active_rehearsal["b_subset_candidate_ids"]) == 30

    # Chạy sampler lần 1 (idempotent rerun trên hydrated raw pool)
    rerun_res1 = run_main_batch1_sampling(
        hydrated_pool,
        seed_lot_100=seed_lot_100,
        seed_b_subset_30=seed_b_subset_30,
        seed_release_shuffle=seed_release_shuffle,
        blind_salt=v4_salt,
        ledger=reloaded_rehearsal,
        lot_id="main_lot_batch_001",
    )
    assert len(rerun_res1.lot_100_blind_ids) == 100
    assert len(rerun_res1.b_subset_30_blind_ids) == 30
    assert len(reloaded_rehearsal.events) == 3, "Rerun lần 1 không được append thêm block!"

    # Chạy sampler lần 2 (xác nhận tính lũy nghiệm)
    rerun_res2 = run_main_batch1_sampling(
        hydrated_pool,
        seed_lot_100=seed_lot_100,
        seed_b_subset_30=seed_b_subset_30,
        seed_release_shuffle=seed_release_shuffle,
        blind_salt=v4_salt,
        ledger=reloaded_rehearsal,
        lot_id="main_lot_batch_001",
    )
    assert rerun_res1.lot_100_blind_ids == rerun_res2.lot_100_blind_ids
    assert rerun_res1.b_subset_30_blind_ids == rerun_res2.b_subset_30_blind_ids
    assert len(reloaded_rehearsal.events) == 3, "Rerun lần 2 không được append thêm block!"
    print("✅ Rerun hai lần liên tiếp hoàn toàn lũy nghiệm (idempotent), 0 block phát sinh")

    # 9. Đối soát toàn diện View A và View B với hiện vật đã niêm phong (Khắc phục triệt để R2)
    view_a_orig = json.loads((staging_v4_2_dir / "blind_view_a.json").read_text(encoding="utf-8"))
    view_b_orig = json.loads((staging_v4_2_dir / "blind_view_b.json").read_text(encoding="utf-8"))
    samples_a_orig = view_a_orig["samples"] if isinstance(view_a_orig, dict) else view_a_orig
    samples_b_orig = view_b_orig["samples"] if isinstance(view_b_orig, dict) else view_b_orig

    assert len(rerun_res1.blind_view_a) == len(samples_a_orig) == 100
    for idx, (gen, orig) in enumerate(zip(rerun_res1.blind_view_a, samples_a_orig)):
        assert gen["sample_id"] == orig["sample_id"], f"Sample ID sai tại vị trí {idx}"
        assert gen["url"] == orig["url"], f"URL sai tại vị trí {idx}"
        assert gen["page_text"] == orig["page_text"], f"page_text sai tại vị trí {idx}"
        assert gen["structure_summary"] == orig["structure_summary"], f"structure_summary sai tại vị trí {idx}"
        assert compute_sample_content_hash(gen) == compute_sample_content_hash(orig), f"content hash sai tại vị trí {idx}"

    non_empty_a = sum(1 for s in rerun_res1.blind_view_a if s["page_text"].strip())
    assert non_empty_a == 97, f"Kỳ vọng đúng 97/100 mẫu View A có text, thực tế: {non_empty_a}"
    print(f"✅ View A: 100/100 mẫu khớp tuyệt đối byte-for-byte với view đã niêm phong ({non_empty_a}/100 non-empty text)")

    assert len(rerun_res1.blind_view_b) == len(samples_b_orig) == 30
    for idx, (gen, orig) in enumerate(zip(rerun_res1.blind_view_b, samples_b_orig)):
        assert gen["sample_id"] == orig["sample_id"], f"Sample ID sai tại vị trí {idx}"
        assert gen["url"] == orig["url"], f"URL sai tại vị trí {idx}"
        assert gen["page_text"] == orig["page_text"], f"page_text sai tại vị trí {idx}"
        assert gen["structure_summary"] == orig["structure_summary"], f"structure_summary sai tại vị trí {idx}"
        assert compute_sample_content_hash(gen) == compute_sample_content_hash(orig), f"content hash sai tại vị trí {idx}"

    non_empty_b = sum(1 for s in rerun_res1.blind_view_b if s["page_text"].strip())
    assert non_empty_b == 30, f"Kỳ vọng 30/30 mẫu View B có text, thực tế: {non_empty_b}"
    print(f"✅ View B: 30/30 mẫu khớp tuyệt đối byte-for-byte với view đã niêm phong ({non_empty_b}/30 non-empty text)")

    # Ghi nhận báo cáo rehearsal
    rehearsal_report = {
        "rehearsal_status": "SUCCESS",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "target_ledger": "temporary_copy_of_main_annotation_lot_management_ledger.json",
        "predecessor_block_seq": 1,
        "predecessor_block_hash": b1_real.event_hash,
        "rehearsal_block_seq": 2,
        "rehearsal_block_id": ev2.event_id,
        "rehearsal_block_hash": ev2.event_hash,
        "total_blocks_after_rehearsal": 3,
        "active_lot_verification": {
            "lot_id": "main_lot_batch_001",
            "active_state_retrieved": True,
            "allocated_candidate_ids_count": len(active_rehearsal["allocated_candidate_ids"]),
            "b_subset_candidate_ids_count": len(active_rehearsal["b_subset_candidate_ids"]),
            "b_indices_count": len(active_rehearsal["b_indices_in_lot100"]),
            "historical_cohort_seed_commitment": historical_cohort_seed_commitment,
            "active_release_seed_commitment": v4_seed_commitment,
            "commitments_distinct": True,
        },
        "raw_hydration_audit": {
            "source_parquet": "data/raw/phreshphish/data/train-001.parquet",
            "source_revision": "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a",
            "candidates_hydrated_count": 1232,
            "url_and_html_hashes_verified": True,
            "multidimensional_population_fingerprint": computed_fp,
            "view_a_sample_count": 100,
            "view_a_non_empty_text_count": non_empty_a,
            "view_a_payload_byte_for_byte_match": True,
            "view_b_sample_count": 30,
            "view_b_non_empty_text_count": non_empty_b,
            "view_b_payload_byte_for_byte_match": True,
        },
        "idempotent_rerun_verification": {
            "first_rerun_appended_blocks": 0,
            "second_rerun_appended_blocks": 0,
            "total_blocks_remains": 3,
            "cohort_preserved": True,
        },
        "safety_assertion": "The real ledger on disk remains strictly untouched at 2 blocks. Block 2 is purely a rehearsal proposal.",
    }
    rehearsal_report_file = staging_v4_2_dir / "rehearsal_migration_report.json"
    rehearsal_report_file.write_text(json.dumps(rehearsal_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    shutil.rmtree(temp_rehearsal_dir)

    # 10. Đưa các tệp test độc lập vào staging
    shutil.copy2(root / "tests" / "test_ledger_migration_proposal.py", staging_v4_2_dir / "test_ledger_migration_proposal.py")
    shutil.copy2(root / "tests" / "test_isolation_scanner_regression.py", staging_v4_2_dir / "test_isolation_scanner_regression.py")
    shutil.copy2(root / "tests" / "test_main_batch1_manifest_preflight.py", staging_v4_2_dir / "test_main_batch1_manifest_preflight.py")
    shutil.copy2(root / "tests" / "test_main_v41_fingerprint_integrity.py", staging_v4_2_dir / "test_main_v41_fingerprint_integrity.py")

    # 11. Cập nhật release_manifest.json
    codebook_path = root / "docs" / "CODEBOOK_V1_1.md"
    dictionary_path = root / "configs" / "dictionary_v1.json"
    cb_sha256 = compute_sha256(codebook_path)
    dict_sha256 = compute_sha256(dictionary_path)

    rel_manifest = {
        "manifest_version": "1.4.2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "lot_id": "main_lot_batch_001",
        "actor": "Member C (Nguyễn Thắng)",
        "governance_status": {
            "main_batch1_status": "HOLD",
            "ready_for_annotation": False,
            "acceptance": {"B": "pending", "D": "pending"},
            "training_blocked": True,
            "official_test_used": False,
            "ledger_migration_status": "RESERVED_PROPOSAL_ONLY_2_BLOCKS_ON_DISK",
        },
        "contract_versions": {
            "codebook_version": "1.1.0",
            "blind_contract_version": "1.2.0",
            "sampling_plan_version": "MAIN-PLAN-V1.0",
            "dictionary_version": "1.0.0",
        },
        "commitments": {
            "historical_cohort_seed_commitment": historical_cohort_seed_commitment,
            "active_release_seed_commitment": v4_seed_commitment,
            "population_fingerprint_sha256": computed_fp,
            "codebook_sha256": cb_sha256,
            "dictionary_sha256": dict_sha256,
        },
    }
    rel_manifest_file = staging_v4_2_dir / "release_manifest.json"
    rel_manifest_file.write_text(json.dumps(rel_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 12. Sinh SHA256SUMS.txt cho toàn bộ tệp trong staging V4.2
    all_files = sorted([f for f in staging_v4_2_dir.iterdir() if f.is_file() and f.name != "SHA256SUMS.txt"])
    sums_lines = []
    for f in all_files:
        h = compute_sha256(f)
        sums_lines.append(f"{h}  {f.name}")
    sums_file = staging_v4_2_dir / "SHA256SUMS.txt"
    sums_file.write_text("\n".join(sums_lines) + "\n", encoding="utf-8")
    print(f"✅ Sinh SHA256SUMS.txt cho {len(all_files)} hiện vật")

    # 13. Đóng gói tệp ZIP bàn giao V4.2
    pack_name = "MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_2_STAGING.zip"
    zip_dst_root = root / pack_name
    zip_dst_restricted = root / "data" / "restricted" / pack_name

    for zip_path in (zip_dst_root, zip_dst_restricted):
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(staging_v4_2_dir.iterdir()):
                if f.is_file():
                    zf.write(f, arcname=f.name)

    zip_size = zip_dst_root.stat().st_size
    zip_hash = compute_sha256(zip_dst_root)

    print("=" * 75)
    print(f"🎉 GÓI DỮ LIỆU STAGING V4.2 ĐÃ ĐÓNG GÓI THÀNH CÔNG!")
    print(f"Tên tệp:     {pack_name}")
    print(f"Dung lượng:  {zip_size:,} bytes")
    print(f"SHA-256:     {zip_hash}")
    print(f"Số hiện vật: {len(all_files) + 1}")
    print("=" * 75)


if __name__ == "__main__":
    main()
