#!/usr/bin/env python3
"""Build Calibration v1.1.2 Release Runway (Final Locked Codebook Package).

Synchronizes locked Codebook v1.1.0 (docs/CODEBOOK_V1_1.md) SHA-256 into:
- data/raw/recovery/calibration_proposal_v1.1.2_release.json
- data/raw/recovery/calibration_proposal_v1.1.2_release.json.receipt.json
- configs/calibration_manifest_v1_1_2_release.json
- data/raw/recovery/calibration_v1.1.2_b_qa_pack.zip

Preserves legacy v1.1 and v1.1.1 packages intact as audit trails.
Guarantees zero label leakage and maintains strict fail-closed safety flags:
  ready_for_annotation=false, training_blocked=true, acceptance.B=pending, acceptance.D=pending.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phishing.annotation.blind_view import assert_no_label_leak


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_release_v1_1_2() -> dict:
    recovery_dir = ROOT / "data/raw/recovery"
    configs_dir = ROOT / "configs"
    docs_dir = ROOT / "docs"

    codebook_path = docs_dir / "CODEBOOK_V1_1.md"
    if not codebook_path.exists():
        raise FileNotFoundError(f"Missing locked codebook: {codebook_path}")
    codebook_sha256 = file_sha256(codebook_path)

    v111_release_path = recovery_dir / "calibration_proposal_v1.1.1_release.json"
    if not v111_release_path.exists():
        raise FileNotFoundError(f"Missing v1.1.1 release view: {v111_release_path}")
    v111_data = json.loads(v111_release_path.read_text(encoding="utf-8"))
    v111_sha256 = file_sha256(v111_release_path)

    # Clone v1.1.1 view and update codebook hash in top-level metadata
    v112_view = dict(v111_data)
    v112_view["codebook_sha256"] = codebook_sha256
    v112_view["codebook_version"] = "1.1.0"
    v112_view["status"] = "proposal_release_candidate"
    v112_view["description"] = (
        "Gói Blind View đề xuất v1.1.2 sau khi khóa Codebook v1.1.0 (docs/CODEBOOK_V1_1.md); "
        "bảo toàn trọn vẹn 24 mẫu và bản dịch sạch v1.1.1 (hạn chế data/raw)"
    )

    # Ensure zero label leak on entire view and all samples
    assert_no_label_leak(v112_view)

    # Write v1.1.2 release view
    v112_release_path = recovery_dir / "calibration_proposal_v1.1.2_release.json"
    payload = (json.dumps(v112_view, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    v112_release_path.write_bytes(payload)
    v112_sha256 = hashlib.sha256(payload).hexdigest()
    v112_bytes = len(payload)

    # Build v1.1.2 receipt
    receipt = {
        "status": "proposal_release_candidate_pending_approval",
        "release_version": "1.1.2",
        "base_view_sha256": "432922cec6a0dcab4345ff5dec07c00c99c24346e2493f709e774f8dae290ad6",
        "clean_translations_batch_sha256": "4c6e87f594477d112a039a886c4db519c1f325f7cedacc32a749ffda2653aa18",
        "release_view_sha256": v112_sha256,
        "release_view_bytes": v112_bytes,
        "codebook_version": "1.1.0",
        "codebook_sha256": codebook_sha256,
        "codebook_file": "docs/CODEBOOK_V1_1.md",
        "tool": "MarianMT",
        "tool_version": "5.19.0",
        "tool_artifact_sha256": "ed649116c143fc2d7aea690246f4b2b7caa814e9e00a8d5bbe047822b18de022",
        "translated_count": 4,
        "total_samples": 24,
        "sampling_plan_version": "CALIBRATION-PLAN-V1.1-STRATIFIED",
        "previous_release": {
            "release_version": "1.1.1",
            "release_view_sha256": v111_sha256,
            "codebook_sha256": "20b4c181ca1da195c8cd86848ce084035e202ca22b56673cc1aa2e6a911c2b3b",
            "note": "Legacy artifact preserved for audit trail; superseded by v1.1.2 due to Codebook lock",
        },
    }
    receipt_path = recovery_dir / "calibration_proposal_v1.1.2_release.json.receipt.json"
    receipt_bytes = (json.dumps(receipt, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    receipt_path.write_bytes(receipt_bytes)
    receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()

    # Build v1.1.2 manifest
    manifest = {
        "manifest_id": "CALIBRATION-V1.1.2-RELEASE-RUNWAY-20261012",
        "dataset_id": "CALIBRATION-V1.1-24",
        "sample_count": 24,
        "sampling_plan_version": "CALIBRATION-PLAN-V1.1-STRATIFIED",
        "codebook_version": "1.1.0",
        "codebook_file": "docs/CODEBOOK_V1_1.md",
        "codebook_status": "locked",
        "codebook_sha256": codebook_sha256,
        "dictionary_version": "1.0.0",
        "dictionary_status": "locked",
        "dictionary_sha256": "7aa83b68fdb4bb288460c00523e38e0779e8cbeb81ae879e7a5d27e771fcd3b3",
        "acceptance": {
            "B": "pending",
            "D": "pending",
        },
        "ready_for_annotation": False,
        "training_blocked": True,
        "blind_view_path": "data/raw/recovery/calibration_proposal_v1.1.2_release.json",
        "blind_view_sha256": v112_sha256,
        "official_test_used": False,
        "exclusion_registry_sha256": "4b752a59b34393896ea4016554476d565701d7f54c489e927ee5c115b68e814e",
        "source_manifest_sha256": "50fa39d58325e4645b76886e519dd5fbaca31db234d8c70eb95a4eeb608e8eb0",
        "translation_manifest": {
            "model_repo_id": "Helsinki-NLP/opus-mt-ja-en",
            "model_pinned_revision": "0770961a39ba6bd66305b149c3f4110bcafca2e6",
            "clean_payload_sha256": "4c6e87f594477d112a039a886c4db519c1f325f7cedacc32a749ffda2653aa18",
        },
        "previous_release": {
            "manifest": "configs/calibration_manifest_v1_1_1_release.json",
            "blind_view_sha256": v111_sha256,
            "superseded_reason": "Codebook locked to v1.1.0 official artifact (docs/CODEBOOK_V1_1.md); synchronized codebook_sha256 into final release runway",
        },
        "notes": (
            "Manifest đường chạy phát hành cuối v1.1.2 sau khi Codebook v1.1.0 được khóa chính thức; "
            "giữ trạng thái pending, ready_for_annotation=false, training_blocked=true. Chờ B hoàn tất QA kỹ thuật mù và D ký duyệt mở phiên."
        ),
    }
    manifest_path = configs_dir / "calibration_manifest_v1_1_2_release.json"
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()

    # Build Member B QA Pack ZIP (Clean Blind View Package)
    qa_zip_path = recovery_dir / "calibration_v1.1.2_b_qa_pack.zip"
    readme_content = f"""# BỘ TỆP ĐỐI SOÁT KỸ THUẬT MÙ CHO THÀNH VIÊN B (CALIBRATION V1.1.2 QA PACK)
Mục đích: B kiểm tra độc lập mã băm SHA-256, số lượng mẫu (24), schema, việc không lộ nhãn, Codebook v1.1 locked và sự khớp với manifest v1.1.2.
LƯU Ý NGHIÊM NGẶT (ARS PROTOCOL):
- B là annotator tham gia phiên gán nhãn mù. Tuyệt đối KHÔNG mở đọc nội dung văn bản (page_text, translated_text) hay URL của các mẫu.
- Chỉ chạy script kiểm tra tự động mã băm, schema và assert_no_label_leak.
- Không khởi chạy công cụ gán nhãn (annotate_cli) trước khi Lead D phát lệnh mở phiên chính thức.

Danh mục tệp:
1. calibration_proposal_v1.1.2_release.json (Blind View v1.1.2, SHA-256: {v112_sha256})
2. calibration_proposal_v1.1.2_release.json.receipt.json (Receipt liên kết provenance và codebook locked)
"""
    with zipfile.ZipFile(qa_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README_B_QA.txt", readme_content.encode("utf-8"))
        zf.write(v112_release_path, arcname=v112_release_path.name)
        zf.write(receipt_path, arcname=receipt_path.name)

    qa_zip_bytes = qa_zip_path.read_bytes()
    qa_zip_sha256 = hashlib.sha256(qa_zip_bytes).hexdigest()
    (recovery_dir / f"{qa_zip_path.name}.sha256").write_text(f"{qa_zip_sha256}  {qa_zip_path.name}\n", encoding="utf-8")

    summary = {
        "codebook_path": str(codebook_path),
        "codebook_sha256": codebook_sha256,
        "release_view_path": str(v112_release_path),
        "release_view_bytes": v112_bytes,
        "release_view_sha256": v112_sha256,
        "receipt_path": str(receipt_path),
        "receipt_sha256": receipt_sha256,
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest_sha256,
        "qa_zip_path": str(qa_zip_path),
        "qa_zip_bytes": len(qa_zip_bytes),
        "qa_zip_sha256": qa_zip_sha256,
    }
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    build_release_v1_1_2()
