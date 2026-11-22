"""Script chuẩn bị Gói Kế nhiệm V4.1 (Successor Staging Pack for Lead D).

Khép đúng 2 nội dung kỹ thuật mà Lead D giao (Mục 1 & Mục 2):
1. Khôi phục đầy đủ hợp đồng manifest A/B (12 trường bắt buộc, trạng thái pending/ready_for_annotation=false,
   hash codebook/dictionary đối chiếu trực tiếp từ file thật trên đĩa).
2. Tách rõ ràng cohort_seed_commitment (cam kết lịch sử của Block 1) khỏi seed_commitment (cam kết phát hành hiện hành với salt mới).
3. Bảo lưu nguyên trạng gói V4 đã bàn giao (MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_STAGING.zip);
   giữ nguyên 100% cohort A100/B30, UIDs, Blind IDs, nội dung, thứ tự và salt V4.
4. Sổ cái thật trên đĩa tiếp tục giữ nguyên 2 block lịch sử (chưa áp dụng proposal).
"""

import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
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
    staging_v4_1_dir = root / "data" / "restricted" / "main_batch1_staging_v4_1"

    print("=" * 75)
    print("CHUẨN BỊ GÓI KẾ NHIỆM STAGING V4.1 CHO LEAD D (MANIFEST CONTRACT & COHORT COMMITMENT)")
    print("=" * 75)

    # 1. Kiểm tra hiện vật V4 đã bàn giao bảo đảm nguyên vẹn
    v4_zip = root / "MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_STAGING.zip"
    assert v4_zip.exists(), f"Không tìm thấy {v4_zip}"
    v4_zip_hash = compute_sha256(v4_zip)
    expected_v4_hash = "f2bb7b5423cf88cf0cd29db5a4016ab94694409344f92fc599b2101def3ad81f"
    assert v4_zip_hash == expected_v4_hash, f"V4 ZIP hash sai lệch: {v4_zip_hash}"
    print(f"✅ V4 ZIP gốc được bảo lưu nguyên trạng: {v4_zip.stat().st_size} bytes | {v4_zip_hash}")

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

    # 4. Thiết lập thư mục staging V4.1 và sao chép toàn bộ hiện vật gốc V4
    if staging_v4_1_dir.exists():
        shutil.rmtree(staging_v4_1_dir)
    staging_v4_1_dir.mkdir(parents=True, exist_ok=True)

    # Danh sách hiện vật chuyển tiếp nguyên byte từ V4
    passthrough_files = [
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
    for fn in passthrough_files:
        src_f = v4_dir / fn
        dst_f = staging_v4_1_dir / fn
        shutil.copy2(src_f, dst_f)

    # 5. Khôi phục đầy đủ hợp đồng manifest A/B (Mục 1)
    view_a_path = staging_v4_1_dir / "blind_view_a.json"
    view_b_path = staging_v4_1_dir / "blind_view_b.json"
    view_a_hash = compute_sha256(view_a_path)
    view_b_hash = compute_sha256(view_b_path)

    codebook_path = root / "docs" / "CODEBOOK_V1_1.md"
    dictionary_path = root / "configs" / "dictionary_v1.json"
    assert codebook_path.exists(), f"Không tìm thấy {codebook_path}"
    assert dictionary_path.exists(), f"Không tìm thấy {dictionary_path}"
    cb_sha256 = compute_sha256(codebook_path)
    dict_sha256 = compute_sha256(dictionary_path)

    manifest_a = {
        "dataset_id": "MAIN-BATCH1-A",
        "sample_count": 100,
        "sampling_plan_version": "MAIN-PLAN-V1.0",
        "codebook_version": "1.1.0",
        "codebook_status": "locked",
        "dictionary_version": "1.0.0",
        "dictionary_status": "locked",
        "acceptance": {"B": "pending", "D": "pending"},
        "ready_for_annotation": False,
        "blind_view_sha256": view_a_hash,
        "codebook_sha256": cb_sha256,
        "dictionary_sha256": dict_sha256,
        "blind_contract_version": BLIND_CONTRACT_VERSION_V1_2_0,
    }
    manifest_b = {
        "dataset_id": "MAIN-BATCH1-B",
        "sample_count": 30,
        "sampling_plan_version": "MAIN-PLAN-V1.0",
        "codebook_version": "1.1.0",
        "codebook_status": "locked",
        "dictionary_version": "1.0.0",
        "dictionary_status": "locked",
        "acceptance": {"B": "pending", "D": "pending"},
        "ready_for_annotation": False,
        "blind_view_sha256": view_b_hash,
        "codebook_sha256": cb_sha256,
        "dictionary_sha256": dict_sha256,
        "blind_contract_version": BLIND_CONTRACT_VERSION_V1_2_0,
    }

    manifest_a_file = staging_v4_1_dir / "manifest_a.json"
    manifest_b_file = staging_v4_1_dir / "manifest_b.json"
    manifest_a_file.write_text(json.dumps(manifest_a, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest_b_file.write_text(json.dumps(manifest_b, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✅ Khôi phục đầy đủ hợp đồng manifest_a.json (12 trường): {manifest_a_file.stat().st_size} bytes")
    print(f"✅ Khôi phục đầy đủ hợp đồng manifest_b.json (12 trường): {manifest_b_file.stat().st_size} bytes")

    # 6. Kiểm định manifest preflight bằng CLI thật trước khi đóng gói
    cli_spec = importlib.util.spec_from_file_location("annotate_cli", root / "scripts" / "annotate_cli.py")
    cli_mod = importlib.util.module_from_spec(cli_spec)
    cli_spec.loader.exec_module(cli_mod)

    view_a_data = json.loads(view_a_path.read_text(encoding="utf-8"))
    view_b_data = json.loads(view_b_path.read_text(encoding="utf-8"))

    # Kiểm tra manifest_a dừng đúng ở cổng pending (CHƯA NGHIỆM THU), không dừng vì thiếu schema
    try:
        cli_mod.validate_manifest_preflight(manifest_a_file, view_a_path, view_a_data, codebook_path, dictionary_path)
        raise RuntimeError("FAIL: manifest_a đang ở trạng thái pending nhưng không bị chặn!")
    except ValueError as exc:
        assert "CHƯA NGHIỆM THU" in str(exc), f"Dừng sai nguyên nhân: {exc}"
        print(f"✅ manifest_a tiền kiểm dừng đúng ở cổng pending: {exc}")

    # Kiểm tra manifest_b dừng đúng ở cổng pending (CHƯA NGHIỆM THU)
    try:
        cli_mod.validate_manifest_preflight(manifest_b_file, view_b_path, view_b_data, codebook_path, dictionary_path)
        raise RuntimeError("FAIL: manifest_b đang ở trạng thái pending nhưng không bị chặn!")
    except ValueError as exc:
        assert "CHƯA NGHIỆM THU" in str(exc), f"Dừng sai nguyên nhân: {exc}"
        print(f"✅ manifest_b tiền kiểm dừng đúng ở cổng pending: {exc}")

    # 7. Cập nhật seed_salt_specification_restricted.json cho V4.1
    salt_spec_v4_1 = {
        "lot_id": "main_lot_batch_001",
        "status": "STAGING_SUPERSEDE_V4_1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "superseded_reason": "Salt rotation due to test fixture literal exposure in commit 38998ca; locked V4 salt and Lineage enriched with separated historical cohort commitment",
        "sampling_seeds": {
            "seed_population": seeds["seed_population"],
            "seed_lot_100": seed_lot_100,
            "seed_b_subset_30": seed_b_subset_30,
            "seed_release_shuffle": seed_release_shuffle,
        },
        "salt_specification": {
            "blind_salt": v4_salt,
            "salt_formula": "lot100:{seed_lot_100}|b30:{seed_b_subset_30}|shuffle:{seed_release_shuffle}|salt:{salt}",
            "seed_commitment_sha256": v4_seed_commitment,
            "cohort_seed_commitment_sha256": historical_cohort_seed_commitment,
            "prior_seed_commitment_sha256": historical_cohort_seed_commitment,
        },
        "governance_note": "Managed exclusively in restricted staging environment. Explicit separation between historical cohort commitment (Block 1) and active release configuration commitment (Block 2).",
    }
    salt_spec_v4_1_file = staging_v4_1_dir / "seed_salt_specification_restricted.json"
    salt_spec_v4_1_file.write_text(json.dumps(salt_spec_v4_1, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✅ Cập nhật seed_salt_specification_restricted.json tách bạch cohort commitment")

    # 8. Cập nhật main_batch1_salt_rotation_lineage.json cho V4.1
    lineage_v4_file = v4_dir / "main_batch1_salt_rotation_lineage.json"
    lineage_v4 = json.loads(lineage_v4_file.read_text(encoding="utf-8"))
    lineage_v4_1 = copy.deepcopy(lineage_v4)
    lineage_v4_1["lineage_report_type"] = "MAIN_BATCH1_SALT_ROTATION_LINEAGE_REPORT_V4_1"
    lineage_v4_1["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    lineage_v4_1["cryptographic_commitments"]["historical_cohort_seed_commitment"] = historical_cohort_seed_commitment
    lineage_v4_1["cryptographic_commitments"]["active_release_seed_commitment"] = v4_seed_commitment
    lineage_v4_1["governance_lineage_note"] = (
        "Strict cryptographic separation: historical cohort commitment (Block 1) "
        "locks original sample draw; active release commitment (Block 2) locks rotated salt configuration."
    )
    lineage_v4_1_file = staging_v4_1_dir / "main_batch1_salt_rotation_lineage.json"
    lineage_v4_1_file.write_text(json.dumps(lineage_v4_1, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lineage_hash = compute_sha256(lineage_v4_1_file)
    print(f"✅ Cập nhật main_batch1_salt_rotation_lineage.json (SHA-256: {lineage_hash})")

    # 9. Cập nhật Proposal Block 2 Snapshot (Mục 2)
    proposal_v4 = json.loads((v4_dir / "proposal_block2_active_state_snapshot.json").read_text(encoding="utf-8"))
    proposal_v4_1 = copy.deepcopy(proposal_v4)
    proposal_v4_1["details"]["seed_commitment"] = v4_seed_commitment
    proposal_v4_1["details"]["cohort_seed_commitment"] = historical_cohort_seed_commitment
    proposal_v4_1["details"]["prior_seed_commitment"] = historical_cohort_seed_commitment
    proposal_v4_1["details"]["lineage_audit_hash"] = lineage_hash
    proposal_v4_1["details"]["migration_reason"] = (
        "Supersede salt due to test fixture literal exposure (commit 38998ca); "
        "enrich active state snapshot with distinct historical cohort commitment (Block 1), "
        "active release seed commitment (Block 2), B30 indices, and multidimensional population fingerprint"
    )
    proposal_v4_1_file = staging_v4_1_dir / "proposal_block2_active_state_snapshot.json"
    proposal_v4_1_file.write_text(json.dumps(proposal_v4_1, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✅ Cập nhật proposal_block2_active_state_snapshot.json (tách rõ cohort_seed_commitment)")

    # 10. Chạy Rehearsal độc lập trên bản sao tạm của Sổ cái
    temp_rehearsal_dir = staging_v4_1_dir / "temp_rehearsal"
    temp_rehearsal_dir.mkdir(parents=True, exist_ok=True)
    temp_ledger_file = temp_rehearsal_dir / "rehearsal_ledger.json"
    shutil.copy2(real_ledger_path, temp_ledger_file)

    rehearsal_ledger = LotManagementLedger(temp_ledger_file)
    assert len(rehearsal_ledger.events) == 2

    # Append Block 2 trên bản sao tạm
    ev2 = rehearsal_ledger.append_event(
        event_type=proposal_v4_1["event_type"],
        actor=proposal_v4_1["actor"],
        lot_id=proposal_v4_1["lot_id"],
        status=proposal_v4_1["status"],
        details=proposal_v4_1["details"],
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

    # Kiểm tra chạy lại sampler (idempotent rerun) trên bản sao tạm
    canonical_recs_file = staging_v4_1_dir / "population_1232_canonical_records_v1.json"
    canonical_data = json.loads(canonical_recs_file.read_text(encoding="utf-8"))
    canonical_recs = canonical_data["records"] if isinstance(canonical_data, dict) else canonical_data
    candidates_pool = [
        {
            "candidate_uid": r["candidate_uid"],
            "url": r["url_raw"],
            "url_raw": r["url_raw"],
            "url_normalized": r["url_normalized"],
            "url_sha256": r["url_sha256"],
            "html_sha256": r["html_sha256"],
            "source_shard": r["source_shard"],
            "source_row": r["source_row"],
            "source_revision": r["source_revision"],
        }
        for r in canonical_recs
    ]

    rerun_res1 = run_main_batch1_sampling(
        candidates_pool,
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

    rerun_res2 = run_main_batch1_sampling(
        candidates_pool,
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
        "idempotent_rerun_verification": {
            "first_rerun_appended_blocks": 0,
            "second_rerun_appended_blocks": 0,
            "total_blocks_remains": 3,
            "cohort_preserved": True,
        },
        "safety_assertion": "The real ledger on disk remains strictly untouched at 2 blocks. Block 2 is purely a rehearsal proposal.",
    }
    rehearsal_report_file = staging_v4_1_dir / "rehearsal_migration_report.json"
    rehearsal_report_file.write_text(json.dumps(rehearsal_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    shutil.rmtree(temp_rehearsal_dir)

    # 11. Cập nhật các tệp test độc lập vào staging
    shutil.copy2(root / "tests" / "test_ledger_migration_proposal.py", staging_v4_1_dir / "test_ledger_migration_proposal.py")
    shutil.copy2(root / "tests" / "test_isolation_scanner_regression.py", staging_v4_1_dir / "test_isolation_scanner_regression.py")
    shutil.copy2(root / "tests" / "test_main_batch1_manifest_preflight.py", staging_v4_1_dir / "test_main_batch1_manifest_preflight.py")

    # 12. Cập nhật release_manifest.json
    rel_manifest = {
        "manifest_version": "1.4.1",
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
            "population_fingerprint_sha256": lineage_v4_1["cryptographic_commitments"]["population_fingerprint_sha256"],
            "codebook_sha256": cb_sha256,
            "dictionary_sha256": dict_sha256,
        },
    }
    rel_manifest_file = staging_v4_1_dir / "release_manifest.json"
    rel_manifest_file.write_text(json.dumps(rel_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 13. Sinh SHA256SUMS.txt cho toàn bộ tệp trong staging V4.1
    all_files = sorted([f for f in staging_v4_1_dir.iterdir() if f.is_file() and f.name != "SHA256SUMS.txt"])
    sums_lines = []
    for f in all_files:
        h = compute_sha256(f)
        sums_lines.append(f"{h}  {f.name}")
    sums_file = staging_v4_1_dir / "SHA256SUMS.txt"
    sums_file.write_text("\n".join(sums_lines) + "\n", encoding="utf-8")
    print(f"✅ Sinh SHA256SUMS.txt cho {len(all_files)} hiện vật")

    # 14. Đóng gói tệp ZIP bàn giao V4.1
    pack_name = "MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V4_1_STAGING.zip"
    zip_dst_root = root / pack_name
    zip_dst_restricted = root / "data" / "restricted" / pack_name

    for zip_path in (zip_dst_root, zip_dst_restricted):
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(staging_v4_1_dir.iterdir()):
                if f.is_file():
                    zf.write(f, arcname=f.name)

    zip_size = zip_dst_root.stat().st_size
    zip_hash = compute_sha256(zip_dst_root)

    print("=" * 75)
    print(f"🎉 GÓI DỮ LIỆU STAGING V4.1 ĐÃ ĐÓNG GÓI THÀNH CÔNG!")
    print(f"Tên tệp:    {pack_name}")
    print(f"Dung lượng: {zip_size:,} bytes")
    print(f"SHA-256:    {zip_hash}")
    print(f"Số hiện vật:{len(all_files) + 1}")
    print("=" * 75)


if __name__ == "__main__":
    main()
