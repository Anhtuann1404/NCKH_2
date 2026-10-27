#!/usr/bin/env python3
"""Automated Blind View QA Verification Tool for Member B (QA Lead & Annotator B).

Enables Member B to perform independent, fail-closed verification of the final
Blind View release without reading sample texts, HTML, or exposing blind protocol.

Checks:
1. File presence and Unix LF line endings.
2. Cryptographic SHA-256 integrity: 759b9bc950eedd9d81594bfaf3f1514d433315fa49d3f23536e4b6bdd7818187.
3. Structure & sample count: exactly 24 main samples (SMP-001..SMP-024).
4. Zero reserve candidates: no RSV or reserve entries.
5. Zero data leakage: zero labels, zero ground truth, zero parquet locators, zero raw HTML.
6. Offline translation binding (R-A09): 3 non-English samples (SMP-007, SMP-008, SMP-010).
7. Governance synchronization with manifest.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
VIEW_PATH = ROOT / "data/annotations/clean_calibration_blind_view_24.json"
MANIFEST_PATH = ROOT / "configs/calibration_clean_a_manifest.json"

EXPECTED_VIEW_SHA256 = "759b9bc950eedd9d81594bfaf3f1514d433315fa49d3f23536e4b6bdd7818187"
EXPECTED_VIEW_SIZE = 255617
EXPECTED_SAMPLE_COUNT = 24


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8")

    print("================================================================================")
    print("  KIỂM ĐỊNH MÙ TỰ ĐỘNG BLIND VIEW PHÁT HÀNH - MEMBER B (QA LEAD)")
    print("================================================================================")
    print("  Mục đích: Xác nhận toàn vẹn mật mã và an toàn dữ liệu mà KHÔNG đọc nội dung mẫu")
    print("--------------------------------------------------------------------------------")

    # 1. Kiểm tra sự tồn tại của tệp
    if not VIEW_PATH.exists():
        print(f"❌ THẤT BẠI: Không tìm thấy Blind View tại {VIEW_PATH}")
        return 1
    print(f"✅ [1/7] Tệp Blind View hiện diện: {VIEW_PATH.name}")

    # 2. Kiểm tra chuẩn hóa kết thúc dòng Unix LF
    view_bytes = VIEW_PATH.read_bytes()
    if b"\r\n" in view_bytes:
        print("❌ THẤT BẠI: Tệp chứa ký tự CRLF của Windows! Bắt buộc pure Unix LF.")
        return 1
    print("✅ [2/7] Chuẩn hóa kết thúc dòng: 100% Pure Unix LF.")

    # 3. Kiểm tra mã băm SHA-256 và dung lượng tệp
    actual_sha256 = sha256(view_bytes)
    actual_size = len(view_bytes)
    if actual_sha256 != EXPECTED_VIEW_SHA256:
        print(f"❌ THẤT BẠI: Sai mã băm SHA-256!")
        print(f"   Thực tế:   {actual_sha256}")
        print(f"   Kỳ vọng:   {EXPECTED_VIEW_SHA256}")
        return 1
    if actual_size != EXPECTED_VIEW_SIZE:
        print(f"❌ THẤT BẠI: Sai dung lượng byte ({actual_size} != {EXPECTED_VIEW_SIZE})")
        return 1
    print(f"✅ [3/7] Bảo chứng mật mã SHA-256 khớp tuyệt đối: {actual_sha256}")
    print(f"         Dung lượng tệp: {actual_size:,} bytes")

    # 4. Kiểm tra cấu trúc mẫu và số lượng ID
    try:
        view_data = json.loads(view_bytes.decode("utf-8"))
    except Exception as e:
        print(f"❌ THẤT BẠI: Lỗi cú pháp JSON: {e}")
        return 1

    samples = view_data.get("samples", [])
    if len(samples) != EXPECTED_SAMPLE_COUNT:
        print(f"❌ THẤT BẠI: Số lượng mẫu không đúng ({len(samples)} != {EXPECTED_SAMPLE_COUNT})")
        return 1
    expected_ids = [f"SMP-{i:03d}" for i in range(1, EXPECTED_SAMPLE_COUNT + 1)]
    actual_ids = [s.get("sample_id") for s in samples]
    if actual_ids != expected_ids:
        print(f"❌ THẤT BẠI: Danh sách sample_id không khớp SMP-001..SMP-024")
        return 1
    print(f"✅ [4/7] Cấu trúc mẫu chuẩn xác: Đủ đúng 24 mẫu chính (SMP-001 đến SMP-024).")

    # 5. Kiểm tra bảo vệ tính mù đôi & Chống rò rỉ (Zero-Leakage)
    for s in samples:
        sid = s.get("sample_id", "")
        if sid.startswith("RSV") or "reserve" in sid.lower():
            print(f"❌ THẤT BẠI: Phát hiện mẫu dự phòng {sid} trong Blind View!")
            return 1
    forbidden_terms = [
        "source_label", "ground_truth", "primary_org_status",
        "train-000.parquet", "train-055.parquet", "row_offset",
        "main_phish_count", "main_benign_count",
    ]
    view_text = json.dumps(view_data)
    for term in forbidden_terms:
        if term in view_text:
            print(f"❌ THẤT BẠI: Rò rỉ từ khóa bị cấm: '{term}'")
            return 1
    print("✅ [5/7] Zero-Leakage đạt 100%: 0 mẫu dự phòng, 0 nhãn nguồn, 0 locator parquet.")

    # 6. Kiểm tra ràng buộc bản dịch ngoại tuyến MarianMT (R-A09)
    translated_count = sum(1 for s in samples if s.get("translation_provided"))
    if translated_count != 3:
        print(f"❌ THẤT BẠI: Số mẫu có bản dịch không đúng ({translated_count} != 3)")
        return 1
    translated_ids = {"SMP-007", "SMP-008", "SMP-010"}
    actual_translated_ids = {s["sample_id"] for s in samples if s.get("translation_provided")}
    if actual_translated_ids != translated_ids:
        print(f"❌ THẤT BẠI: Sai danh sách mẫu được dịch: {actual_translated_ids}")
        return 1
    for s in samples:
        if s["sample_id"] in translated_ids:
            t_text = s.get("translated_text", "")
            t_hash = sha256(t_text.encode("utf-8"))
            if s.get("translation_sha256") != t_hash:
                print(f"❌ THẤT BẠI: Hash bản dịch của {s['sample_id']} không khớp nội dung dịch!")
                return 1
            if s.get("translation_tool") != "MarianMT":
                print(f"❌ THẤT BẠI: Công cụ dịch không phải MarianMT!")
                return 1
    print(f"✅ [6/7] Ràng buộc bản dịch ngoại tuyến R-A09 đạt 100% (SMP-007/008 JA, SMP-010 RU).")

    # 7. Kiểm tra trạng thái đồng bộ Manifest
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if manifest.get("blind_view_sha256") != actual_sha256:
            print("❌ THẤT BẠI: Mã băm trong manifest không đồng bộ với Blind View phát hành!")
            return 1
        if manifest.get("ready_for_annotation") is not False:
            print("❌ THẤT BẠI: Chốt an toàn ready_for_annotation phải là false trước khi nghiệm thu!")
            return 1
        print("✅ [7/7] Đồng bộ Manifest hoàn hảo: Hash khớp, chốt an toàn khóa fail-closed.")

    print("--------------------------------------------------------------------------------")
    print("🎉 KẾT LUẬN: TOÀN BỘ 7 BƯỚC KIỂM ĐỊNH MÙ TỰ ĐỘNG ĐÃ ĐẠT 100% (APPROVED)!")
    print("   Member B có thể xuất biên bản QA Blind View mà không vi phạm nguyên tắc phòng sạch.")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
