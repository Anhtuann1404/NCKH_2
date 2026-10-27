#!/usr/bin/env python3
"""Tạo gói rà soát hạn chế cho Lead D và gói kiểm định QA riêng biệt cho Member B.

Tuân thủ nghiêm ngặt ranh giới bảo vệ tính mù đôi (Double-Blind Boundary):
1. Gói D (GOI_RA_SOAT_HAN_CHE_CALIBRATION_CLEAN_32_V2.zip):
   - DÀNH RIÊNG CHO LEAD D: chứa candidates_restricted.json (định vị shard/row, group_id, vai trò dự phòng)
     và clean_calibration_git_leak_audit.json để Lead D đối soát trực tiếp nguồn raw Parquet.
   - Sửa mô tả trong MANIFEST_RESTRICTED.json: xác định rõ gói chỉ dành cho Lead D, nghiêm cấm gửi cho A/B.
2. Gói B (GOI_QA_MEMBER_B_CALIBRATION_CLEAN_32.zip):
   - DÀNH RIÊNG CHO MEMBER B (QA Lead kiêm Annotator B): chỉ gồm báo cáo tổng hợp, mã băm đối soát
     và công cụ kiểm tra tự động verify_member_b_qa.py.
   - TUYỆT ĐỐI KHÔNG chứa: candidates_restricted.json, git_leak_audit.json, shard/row locator, URL thô,
     nhãn nguồn hay danh sách định danh mẫu dự phòng.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.data.verify_member_b_qa import verify_member_b_package


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def create_lead_d_package() -> dict:
    """Tạo gói rà soát hạn chế dành riêng cho Lead D."""
    zip_name = "GOI_RA_SOAT_HAN_CHE_CALIBRATION_CLEAN_32_V2.zip"
    zip_path = ROOT / zip_name

    # Danh sách các tệp đưa vào gói rà soát của Lead D
    files_map = {
        "candidates_restricted.json": ROOT / "data/restricted/clean_calibration_candidates_v2_restricted.json",
        "clean_calibration_selection_inspection_report.json": ROOT / "data/source_audit/clean_calibration_selection_inspection_report.json",
        "clean_calibration_exclusion_audit_report.json": ROOT / "data/source_audit/clean_calibration_exclusion_audit_report.json",
        "clean_calibration_git_leak_audit.json": ROOT / "data/source_audit/clean_calibration_git_leak_audit.json",
        "calibration_clean_a_manifest.json": ROOT / "configs/calibration_clean_a_manifest.json",
    }

    manifest_entries = {}
    for arc_name, p in files_map.items():
        assert p.exists(), f"Thiếu tệp: {p}"
        manifest_entries[arc_name] = {
            "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p),
            "source_repo_path": str(p.relative_to(ROOT)),
        }

    pkg_manifest = {
        "package_id": "PKG-RESTRICTED-LEAD-D-CALIBRATION-CLEAN-32-V2",
        "created_at_utc": "2026-10-27T00:30:00Z",
        "recipient": "Lead D (Anh Tuấn)",
        "purpose": "Gói rà soát hạn chế ngoài Git DÀNH RIÊNG CHO LEAD D (kiểm tra nguồn raw Parquet và đối soát kỹ thuật). Tuyệt đối KHÔNG phân phối cho Annotator A hoặc Member B (Annotator B) nhằm bảo vệ tính mù tuyệt đối.",
        "access_boundary": "Strictly restricted to Lead D. Contains raw candidate locators and exclusion audit history. Distribution to Annotator A or Member B is strictly prohibited.",
        "governance": {
            "ready_for_annotation": False,
            "training_blocked": True,
            "blind_view_released_to_ab": False,
            "contains_raw_locators": True,
            "contains_reserve_list": True,
            "contains_source_class_ratios": True,
            "status": "pending_lead_d_review",
        },
        "contents": manifest_entries,
    }

    manifest_bytes = (json.dumps(pkg_manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for arc_name, p in files_map.items():
            zf.write(p, arcname=arc_name)
        zf.writestr("MANIFEST_RESTRICTED.json", manifest_bytes)

    zip_hash = sha256_file(zip_path)
    zip_size = zip_path.stat().st_size

    return {
        "zip_name": zip_name,
        "zip_path": zip_path,
        "zip_size": zip_size,
        "zip_sha256": zip_hash,
        "recipient": "Lead D (Anh Tuấn)",
        "contents": manifest_entries,
    }


def create_member_b_qa_package() -> dict:
    """Tạo gói QA riêng biệt dành cho Member B (chỉ gồm dữ liệu tổng hợp, hash và công cụ kiểm tra tự động)."""
    zip_name = "GOI_QA_MEMBER_B_CALIBRATION_CLEAN_32.zip"
    zip_path = ROOT / zip_name

    # Danh sách các tệp đưa vào gói QA của Member B: KHÔNG có locator hay thông tin truy ngược nguồn
    files_map = {
        "calibration_clean_a_manifest.json": ROOT / "configs/calibration_clean_a_manifest.json",
        "clean_calibration_selection_inspection_report.json": ROOT / "data/source_audit/clean_calibration_selection_inspection_report.json",
        "clean_calibration_exclusion_audit_report.json": ROOT / "data/source_audit/clean_calibration_exclusion_audit_report.json",
        "verify_member_b_qa.py": ROOT / "scripts/data/verify_member_b_qa.py",
    }

    manifest_entries = {}
    for arc_name, p in files_map.items():
        assert p.exists(), f"Thiếu tệp: {p}"
        manifest_entries[arc_name] = {
            "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p),
            "source_repo_path": str(p.relative_to(ROOT)),
        }

    pkg_manifest = {
        "package_id": "PKG-QA-MEMBER-B-CALIBRATION-CLEAN-32",
        "created_at_utc": "2026-10-27T00:30:00Z",
        "recipient": "Member B (QA Lead kiêm Annotator B)",
        "purpose": "Gói kiểm định QA độc lập dành riêng cho Member B (QA Lead kiêm Annotator B) trước khi kích hoạt quy trình gán nhãn mù. Gói chỉ gồm báo cáo tổng hợp, mã băm đối soát và công cụ kiểm định tự động không tiết lộ locator, nhãn nguồn hay danh sách dự phòng.",
        "access_boundary": "Dedicated for Member B QA validation. Zero raw locators, zero raw URLs, zero candidate labels, zero reserve identities.",
        "governance": {
            "ready_for_annotation": False,
            "training_blocked": True,
            "blind_view_released_to_ab": False,
            "contains_raw_locators": False,
            "contains_source_labels": False,
            "contains_reserve_candidate_list": False,
            "contains_source_class_ratios": False,
            "status": "pending_member_b_qa_review",
        },
        "contents": manifest_entries,
    }

    manifest_bytes = (json.dumps(pkg_manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for arc_name, p in files_map.items():
            zf.write(p, arcname=arc_name)
        zf.writestr("MANIFEST_QA_MEMBER_B.json", manifest_bytes)

    zip_hash = sha256_file(zip_path)
    zip_size = zip_path.stat().st_size

    return {
        "zip_name": zip_name,
        "zip_path": zip_path,
        "zip_size": zip_size,
        "zip_sha256": zip_hash,
        "recipient": "Member B (QA Lead kiêm Annotator B)",
        "contents": manifest_entries,
    }


def main():
    print("=" * 70)
    print("=== TIẾN HÀNH ĐÓNG GÓI RÀ SOÁT TÁCH BIỆT RANH GIỚI BẢO VỆ TÍNH MÙ ===")
    print("=" * 70)

    # 1. Đóng gói cho Lead D
    d_pkg = create_lead_d_package()
    print(f"\n[1] GÓI RÀ SOÁT HẠN CHẾ DÀNH CHO LEAD D (RAW VERIFICATION):")
    print(f"    Tên tệp: {d_pkg['zip_name']}")
    print(f"    Kích thước: {d_pkg['zip_size']} bytes")
    print(f"    SHA-256: {d_pkg['zip_sha256']}")
    print("    Danh sách tệp:")
    for arc_name, meta in d_pkg["contents"].items():
        print(f"      - {arc_name}: {meta['sha256']} ({meta['size_bytes']} bytes)")

    # 2. Đóng gói cho Member B
    b_pkg = create_member_b_qa_package()
    print(f"\n[2] GÓI KIỂM ĐỊNH QA DÀNH CHO MEMBER B (BLIND QA LEAD):")
    print(f"    Tên tệp: {b_pkg['zip_name']}")
    print(f"    Kích thước: {b_pkg['zip_size']} bytes")
    print(f"    SHA-256: {b_pkg['zip_sha256']}")
    print("    Danh sách tệp:")
    for arc_name, meta in b_pkg["contents"].items():
        print(f"      - {arc_name}: {meta['sha256']} ({meta['size_bytes']} bytes)")

    # 3. Chạy kiểm tra tự động trên Gói của Member B ngay lập tức để chứng minh Zero Leakage
    print("\n[3] CHẠY KIỂM ĐỊNH TỰ ĐỘNG CHỨNG MINH ZERO LEAK TRÊN GÓI MEMBER B:")
    qa_result = verify_member_b_package(b_pkg["zip_path"])
    assert qa_result["zero_leak_verified"] is True
    print("\n-> ĐÃ XÁC NHẬN: Gói QA của Member B đạt chuẩn mù tuyệt đối 100%!")


if __name__ == "__main__":
    main()
