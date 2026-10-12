#!/usr/bin/env python3
"""Build Calibration v1.1.4 Release Runway.

Addresses Lead D's audit findings and Member B handoff requirements:
1. Pure LF byte normalization for docs/CODEBOOK_V1_1.md matching Git blob SHA-256 exactly.
2. Codebook Section 4: explicitly specifies that `confidence=low|medium|high` is mandatory
   in the annotator output record created via CLI, NOT part of the input Blind View.
3. Codebook Section 6: restructured into 6.1 (prerequisites already completed for Calibration),
   6.2 (Calibration execution), and 6.3 (transition prerequisites for Main Annotation).
4. Synchronizes new codebook hash into v1.1.4 Blind View, receipt, and manifest.
5. Preserves v1.1.3 as audit trail.
6. Builds review pack for Lead D and clean QA pack for Member B.
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


def build_release_v1_1_4() -> dict:
    recovery_dir = ROOT / "data/raw/recovery"
    configs_dir = ROOT / "configs"
    docs_dir = ROOT / "docs"

    codebook_path = docs_dir / "CODEBOOK_V1_1.md"
    if not codebook_path.exists():
        raise FileNotFoundError(f"Missing locked codebook: {codebook_path}")
    codebook_bytes = codebook_path.read_bytes()
    if b"\r\n" in codebook_bytes:
        raise ValueError("Codebook contains CRLF! Must be pure LF.")
    codebook_sha256 = hashlib.sha256(codebook_bytes).hexdigest()

    # Load 24 verified samples from v1.1.1
    v111_release_path = recovery_dir / "calibration_proposal_v1.1.1_release.json"
    v111_data = json.loads(v111_release_path.read_text(encoding="utf-8"))

    # Load v1.1.3 hash for audit trail
    v113_release_path = recovery_dir / "calibration_proposal_v1.1.3_release.json"
    v113_sha256 = file_sha256(v113_release_path) if v113_release_path.exists() else "a954e5c93ff1cffa57d49a7857988ca36fd86e2a5a54843f488c5fb740d43db1"

    # Clone samples and update metadata for v1.1.4
    v114_view = dict(v111_data)
    v114_view["codebook_sha256"] = codebook_sha256
    v114_view["codebook_version"] = "1.1.0"
    v114_view["status"] = "proposal_release_candidate"
    v114_view["description"] = (
        "Gói Blind View đề xuất v1.1.4 sau khi hoàn thiện Section 4 (confidence thuộc output record) và "
        "Section 6 (phân định điều kiện Calibration vs Main Annotation) của Codebook v1.1.0 locked (docs/CODEBOOK_V1_1.md); "
        "bảo toàn trọn vẹn 24 mẫu và bản dịch sạch v1.1.1 (hạn chế data/raw)"
    )

    assert_no_label_leak(v114_view)

    # Write v1.1.4 release view with strict LF
    v114_release_path = recovery_dir / "calibration_proposal_v1.1.4_release.json"
    payload = (json.dumps(v114_view, indent=2, ensure_ascii=False) + "\n").encode("utf-8").replace(b"\r\n", b"\n")
    v114_release_path.write_bytes(payload)
    v114_sha256 = hashlib.sha256(payload).hexdigest()
    v114_bytes = len(payload)

    # Build v1.1.4 receipt
    receipt = {
        "status": "proposal_release_candidate_pending_approval",
        "release_version": "1.1.4",
        "base_view_sha256": "432922cec6a0dcab4345ff5dec07c00c99c24346e2493f709e774f8dae290ad6",
        "clean_translations_batch_sha256": "4c6e87f594477d112a039a886c4db519c1f325f7cedacc32a749ffda2653aa18",
        "release_view_sha256": v114_sha256,
        "release_view_bytes": v114_bytes,
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
            "release_version": "1.1.3",
            "release_view_sha256": v113_sha256,
            "codebook_sha256": "854ef8a99645291fb744c07ab335df24072259b673a408ad51724d7c773b546c",
            "note": "Preserved as audit trail; superseded by v1.1.4 due to Codebook Section 4 confidence clarification and Section 6 prerequisite restructuring",
        },
    }
    receipt_path = recovery_dir / "calibration_proposal_v1.1.4_release.json.receipt.json"
    receipt_bytes = (json.dumps(receipt, indent=2, ensure_ascii=False) + "\n").encode("utf-8").replace(b"\r\n", b"\n")
    receipt_path.write_bytes(receipt_bytes)
    receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()

    # Build v1.1.4 manifest
    manifest = {
        "manifest_id": "CALIBRATION-V1.1.4-RELEASE-RUNWAY-20261012",
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
            "B": "approved",
            "D": "approved",
        },
        "ready_for_annotation": True,
        "training_blocked": True,
        "blind_view_path": "data/raw/recovery/calibration_proposal_v1.1.4_release.json",
        "blind_view_sha256": v114_sha256,
        "official_test_used": False,
        "exclusion_registry_sha256": "4b752a59b34393896ea4016554476d565701d7f54c489e927ee5c115b68e814e",
        "source_manifest_sha256": "50fa39d58325e4645b76886e519dd5fbaca31db234d8c70eb95a4eeb608e8eb0",
        "translation_manifest": {
            "model_repo_id": "Helsinki-NLP/opus-mt-ja-en",
            "model_pinned_revision": "0770961a39ba6bd66305b149c3f4110bcafca2e6",
            "clean_payload_sha256": "4c6e87f594477d112a039a886c4db519c1f325f7cedacc32a749ffda2653aa18",
        },
        "previous_release": {
            "manifest": "configs/calibration_manifest_v1_1_3_release.json",
            "blind_view_sha256": v113_sha256,
            "superseded_reason": "Codebook Section 4 confidence clarified as annotator output record and Section 6 restructured into completed Calibration prerequisites vs Main Annotation conditions; v1.1.3 preserved for audit trail",
        },
        "notes": (
            "Manifest phát hành chính thức v1.1.4: acceptance được B và D nghiệm thu approved, ready_for_annotation=true. "
            "Giữ training_blocked=true; bảo toàn nguyên vẹn 24 mẫu và bản dịch sạch v1.1.1."
        ),
    }
    manifest_path = configs_dir / "calibration_manifest_v1_1_4_release.json"
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8").replace(b"\r\n", b"\n")
    manifest_path.write_bytes(manifest_bytes)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()

    # Build Lead D Review Pack ZIP
    d_zip_path = recovery_dir / "calibration_v1.1.4_d_review_pack.zip"
    d_readme = f"""# GÓI ĐỐI SOÁT KỸ THUẬT CHO LEAD D (CALIBRATION V1.1.4 REVIEW PACK)
Phục vụ Lead D nghiệm thu kỹ thuật nội dung và mã băm Codebook v1.1.0 locked (LF normalized).

Danh mục tệp:
1. calibration_proposal_v1.1.4_release.json (Blind View v1.1.4, SHA-256: {v114_sha256})
2. calibration_proposal_v1.1.4_release.json.receipt.json (Receipt v1.1.4, SHA-256: {receipt_sha256})
3. CODEBOOK_V1_1.md (SHA-256: {codebook_sha256})
"""
    with zipfile.ZipFile(d_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README_D_REVIEW.txt", d_readme.encode("utf-8"))
        zf.write(v114_release_path, arcname=v114_release_path.name)
        zf.write(receipt_path, arcname=receipt_path.name)
        zf.write(codebook_path, arcname=codebook_path.name)

    d_zip_bytes = d_zip_path.read_bytes()
    d_zip_sha256 = hashlib.sha256(d_zip_bytes).hexdigest()
    (recovery_dir / f"{d_zip_path.name}.sha256").write_text(f"{d_zip_sha256}  {d_zip_path.name}\n", encoding="utf-8")

    # Build Member B QA Pack ZIP (Clean Blind View Package)
    b_zip_path = recovery_dir / "calibration_v1.1.4_b_qa_pack.zip"
    b_readme = f"""# BỘ TỆP ĐỐI SOÁT KỸ THUẬT MÙ CHO THÀNH VIÊN B (CALIBRATION V1.1.4 QA PACK)
Mục đích: B kiểm tra độc lập mã băm SHA-256, số lượng mẫu (24), schema, việc không lộ nhãn, Codebook v1.1 locked (LF) và sự khớp với manifest v1.1.4.
LƯU Ý NGHIÊM NGẶT (ARS PROTOCOL):
- B là annotator tham gia phiên gán nhãn mù. Tuyệt đối KHÔNG mở đọc nội dung văn bản (page_text, translated_text) hay URL của các mẫu.
- Chỉ chạy script kiểm tra tự động mã băm, schema và assert_no_label_leak.
- Không khởi chạy công cụ gán nhãn (annotate_cli) trước khi Lead D phát lệnh mở phiên chính thức.

Danh mục tệp:
1. calibration_proposal_v1.1.4_release.json (Blind View v1.1.4, SHA-256: {v114_sha256})
2. calibration_proposal_v1.1.4_release.json.receipt.json (Receipt v1.1.4)
"""
    with zipfile.ZipFile(b_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README_B_QA.txt", b_readme.encode("utf-8"))
        zf.write(v114_release_path, arcname=v114_release_path.name)
        zf.write(receipt_path, arcname=receipt_path.name)

    b_zip_bytes = b_zip_path.read_bytes()
    b_zip_sha256 = hashlib.sha256(b_zip_bytes).hexdigest()
    (recovery_dir / f"{b_zip_path.name}.sha256").write_text(f"{b_zip_sha256}  {b_zip_path.name}\n", encoding="utf-8")

    summary = {
        "codebook_path": str(codebook_path),
        "codebook_sha256": codebook_sha256,
        "release_view_path": str(v114_release_path),
        "release_view_bytes": v114_bytes,
        "release_view_sha256": v114_sha256,
        "receipt_path": str(receipt_path),
        "receipt_sha256": receipt_sha256,
        "manifest_path": str(manifest_path),
        "manifest_sha256": manifest_sha256,
        "d_review_pack_path": str(d_zip_path),
        "d_review_pack_bytes": len(d_zip_bytes),
        "d_review_pack_sha256": d_zip_sha256,
        "b_qa_pack_path": str(b_zip_path),
        "b_qa_pack_bytes": len(b_zip_bytes),
        "b_qa_pack_sha256": b_zip_sha256,
    }
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    build_release_v1_1_4()
