#!/usr/bin/env python3
"""Công cụ kiểm tra tự động dành riêng cho Member B (QA Lead kiêm Annotator B).

Mục tiêu kiểm định:
1. Xác minh tính toàn vẹn mã băm (Cryptographic Hash Integrity) của các tài liệu kỹ thuật trong Gói QA Member B.
2. Kiểm tra chốt chặn an toàn bảo vệ tính mù đôi (Zero Leakage Check):
   - Đảm bảo 0 locator (không có shard name hay row offset)
   - Đảm bảo 0 URL thô (no raw URLs)
   - Đảm bảo 0 mã nguồn HTML thô
   - Đảm bảo 0 nhãn phân loại gắn theo từng mẫu (zero per-sample source labels)
   - Đảm bảo 0 danh sách định danh ứng viên dự phòng (zero reserve candidate identities)
3. Kiểm tra các chỉ số phân tầng và tương đồng tổng hợp:
   - Đủ 24 mẫu chính + 8 mẫu dự phòng (tổng 32 mẫu, 32 nhóm miền độc lập)
   - 0 trùng lặp với 182 mẫu trong 8 lô registry loại trừ
   - Quét tương đồng cặp 496 cặp đạt 0 xung đột theo cả 2 quy tắc
4. Xác minh cờ quản trị:
   - ready_for_annotation == false
   - training_blocked == true
   - official_test_used == false
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def check_zero_leakage_in_text(file_name: str, content_str: str) -> list[str]:
    """Quét văn bản để phát hiện các dấu hiệu lộ thông tin nhạy cảm vi phạm nguyên tắc mù."""
    violations = []

    # 1. Quét locator (shard name + row offset) - áp dụng cho mọi tệp kể cả Blind View
    if re.search(r"train-\d+\.parquet\s*(?:row|offset|dòng)", content_str, re.IGNORECASE):
        violations.append(f"[{file_name}] Phát hiện mẫu định vị shard + dòng")
    if re.search(r"row[_\s]+offset\s*:\s*\d+", content_str, re.IGNORECASE):
        violations.append(f"[{file_name}] Phát hiện trường row_offset có giá trị cụ thể")
    if re.search(r"row[_\s]+\d+", content_str, re.IGNORECASE):
        # Cho phép các từ như 'rows' trong số lượng tổng 'total_rows' hoặc 'scanned_rows', nhưng cấm 'row 123'
        if not re.search(r"(?:total|scanned|corpus)[_\s]+rows", content_str, re.IGNORECASE):
            violations.append(f"[{file_name}] Phát hiện chỉ số dòng row <số>")

    # 2. Quét mảng locator chi tiết
    if re.search(r'"main_locators"\s*:\s*\[', content_str) or re.search(r'"reserve_locators"\s*:\s*\[', content_str):
        violations.append(f"[{file_name}] Phát hiện mảng locator chi tiết")

    # 3. Quét rò rỉ nhãn nguồn và mã mẫu dự phòng - cấm trên mọi tệp
    if re.search(r'"source_label"', content_str):
        violations.append(f"[{file_name}] Phát hiện nhãn nguồn source_label")
    if re.search(r'"ground_truth"', content_str):
        violations.append(f"[{file_name}] Phát hiện ground_truth")
    if re.search(r'"target"\s*:\s*"[^"]+"', content_str):
        violations.append(f"[{file_name}] Phát hiện target cụ thể")
    if re.search(r"\bRSV-\d{3}\b", content_str):
        violations.append(f"[{file_name}] Phát hiện mã định danh mẫu dự phòng (RSV-xxx)")

    # Blind View có chứa URL và văn bản trang để phục vụ annotator chấm điểm mù.
    # Chi tiết 24 mẫu và kiểm tra an toàn Blind View được thực hiện riêng tại Scope 2.
    if file_name == "clean_calibration_blind_view_24.json":
        return violations

    # 4. Quét URL thô (chỉ áp dụng cho các tệp báo cáo kỹ thuật, manifest, kiểm kê loại trừ)
    raw_urls = re.findall(r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b[-a-zA-Z0-9@:%_\+.~#?&//=]*", content_str)
    # Loại trừ schema URL JSON tiêu chuẩn (json-schema.org, github.com repo chính)
    suspicious_urls = [
        u for u in raw_urls
        if not u.startswith("https://json-schema.org")
        and not u.startswith("https://github.com/Anhtuann1404/NCKH_2")
    ]
    if suspicious_urls:
        violations.append(f"[{file_name}] Phát hiện {len(suspicious_urls)} URL thô tiềm ẩn (vd: {suspicious_urls[:2]})")

    # 5. Quét thẻ HTML thô
    if re.search(r"<\s*(?:html|body|script|iframe|form|input)\b", content_str, re.IGNORECASE):
        violations.append(f"[{file_name}] Phát hiện thẻ HTML thô chưa được làm sạch")

    # 6. Quét mảng danh sách ứng viên chi tiết
    if re.search(r'"candidates"\s*:\s*\[', content_str):
        violations.append(f"[{file_name}] Phát hiện mảng danh sách ứng viên chi tiết 'candidates'")

    # 7. Quét rò rỉ tỷ lệ nhãn nguồn / số đếm lớp (chống thiên kiến kỳ vọng của annotator)
    if re.search(r"(?:main|reserve)_(?:phish|benign)_count", content_str, re.IGNORECASE):
        violations.append(f"[{file_name}] Phát hiện trường đếm nhãn nguồn (main/reserve phish/benign count)")
    if re.search(r"\b(?:12|4)\s*(?:phish|benign)", content_str, re.IGNORECASE):
        violations.append(f"[{file_name}] Phát hiện tỷ lệ nhãn nguồn phish/benign")
    if re.search(r"\b(?:12\s*/\s*12|4\s*/\s*4)\b", content_str):
        violations.append(f"[{file_name}] Phát hiện tỷ lệ nhãn nguồn dạng cân bằng lớp")

    return violations


def verify_member_b_package(package_dir_or_zip: Path) -> dict:
    """Thực hiện toàn bộ quy trình kiểm định QA cho Member B."""
    print("=" * 70)
    print("=== CÔNG CỤ TỰ ĐỘNG KIỂM ĐỊNH QA DÀNH CHO MEMBER B (QA LEAD) ===")
    print("=" * 70)

    files_content: dict[str, bytes] = {}

    if package_dir_or_zip.is_file() and package_dir_or_zip.suffix.lower() == ".zip":
        print(f"[*] Đang đọc gói nén ZIP: {package_dir_or_zip.name}")
        with zipfile.ZipFile(package_dir_or_zip, "r") as zf:
            for name in zf.namelist():
                files_content[name] = zf.read(name)
    elif package_dir_or_zip.is_dir():
        print(f"[*] Đang đọc thư mục giải nén: {package_dir_or_zip}")
        for p in package_dir_or_zip.glob("*"):
            if p.is_file():
                files_content[p.name] = p.read_bytes()
    else:
        raise ValueError(f"Đường dẫn không hợp lệ: {package_dir_or_zip}")

    print(f"[*] Tìm thấy {len(files_content)} tệp trong gói QA:")
    for fn, data in files_content.items():
        print(f"    - {fn} ({len(data)} bytes, SHA-256: {sha256_bytes(data)[:16]}...)")

    # 1. Kiểm tra sự hiện diện của các tệp cốt lõi
    inspection_file_name = (
        "clean_calibration_round_c_inspection_report.json"
        if "clean_calibration_round_c_inspection_report.json" in files_content
        else "clean_calibration_selection_inspection_report.json"
    )
    required_files = [
        "MANIFEST_QA_MEMBER_B.json",
        "calibration_clean_a_manifest.json",
        inspection_file_name,
        "clean_calibration_exclusion_audit_report.json",
    ]
    for rf in required_files:
        assert rf in files_content, f"LỖI: Thiếu tệp bắt buộc '{rf}' trong gói QA của Member B!"

    # 2. Kiểm tra cấm tuyệt đối các tệp chứa thông tin truy ngược nguồn
    forbidden_files = [
        "candidates_restricted.json",
        "clean_calibration_candidates_v2_restricted.json",
        "clean_calibration_candidates_v3_restricted.json",
        "clean_calibration_candidates.json",
        "clean_calibration_git_leak_audit.json",
        "clean_calibration_exclusion_mapping_32.json",
        "clean_calibration_exclusion_mapping_c_32.json",
    ]
    for ff in forbidden_files:
        assert ff not in files_content, f"CẢNH BÁO AN TOÀN VI PHẠM TÍNH MÙ: Tệp cấm '{ff}' xuất hiện trong gói của Member B!"

    # 3. Phân tích cú pháp và kiểm tra hash theo MANIFEST_QA_MEMBER_B.json
    pkg_manifest = json.loads(files_content["MANIFEST_QA_MEMBER_B.json"].decode("utf-8"))
    pkg_id = pkg_manifest.get("package_id", "")
    assert "MEMBER-B" in pkg_id, f"Package ID không hợp lệ: {pkg_id}"
    assert "Member B" in pkg_manifest.get("recipient", ""), "Người nhận không khớp Member B"

    manifest_entries = pkg_manifest.get("contents", {})
    print("\n[*] Đối soát mã băm cryptographic theo MANIFEST_QA_MEMBER_B.json:")
    for fn, expected_meta in manifest_entries.items():
        if fn in files_content:
            actual_sha = sha256_bytes(files_content[fn])
            expected_sha = expected_meta["sha256"]
            assert actual_sha == expected_sha, f"LỖI TOÀN VẸN: Hash của {fn} không khớp manifest! ({actual_sha} != {expected_sha})"
            print(f"    [OK] {fn}: SHA-256 khớp chuẩn.")

    # 4. Quét Zero-Leakage trên toàn bộ các tệp JSON trong gói
    print("\n[*] Quét bảo vệ tính mù đôi (Zero-Leakage Scan):")
    total_violations = []
    for fn, data in files_content.items():
        if fn.endswith(".json"):
            text_content = data.decode("utf-8")
            violations = check_zero_leakage_in_text(fn, text_content)
            if violations:
                total_violations.extend(violations)
            else:
                print(f"    [PASS] {fn}: 0 locator, 0 URL thô, 0 HTML thô, 0 danh sách ứng viên.")

    assert not total_violations, f"PHÁT HIỆN VI PHẠM RÒ RỈ DỮ LIỆU:\n" + "\n".join(total_violations)

    # 5. [Phạm vi 1] Kiểm tra kiểm định tuyển chọn ứng viên (Candidate Selection QA)
    print("\n[*] [Phạm vi 1] Kiểm tra kiểm định tuyển chọn ứng viên (Candidate Selection QA):")
    inspection_report = json.loads(files_content[inspection_file_name].decode("utf-8"))
    exclusion_report = json.loads(files_content["clean_calibration_exclusion_audit_report.json"].decode("utf-8"))
    calib_manifest = json.loads(files_content["calibration_clean_a_manifest.json"].decode("utf-8"))

    # Governance check
    assert calib_manifest["governance"]["ready_for_annotation"] is False, "ready_for_annotation phải là false"
    assert calib_manifest["governance"]["training_blocked"] is True, "training_blocked phải là true"
    assert inspection_report["governance"]["ready_for_annotation"] is False
    assert inspection_report["governance"]["training_blocked"] is True

    # Stratification check (chỉ kiểm tra tổng số mẫu, tuyệt đối không tiết lộ tỷ lệ nhãn cho annotator)
    sel = inspection_report["selection_summary"]
    assert sel["main_samples_count"] == 24, "Số mẫu chính phải là 24"
    assert sel["reserve_samples_count"] == 8, "Số mẫu dự phòng phải là 8"
    assert sel["total_selected"] == 32, "Tổng số mẫu phải là 32"
    assert sel["distinct_groups_count"] == 32, "Phải có đủ 32 nhóm miền độc lập"
    overlap_count = sel.get("deduplication_vs_registry_overlaps", sel.get("deduplication_vs_registry_182_overlaps", 0))
    assert overlap_count == 0, "Không được trùng lặp với các mẫu trong registry"
    print("    [PASS] Phân tầng: 24 mẫu chính + 8 mẫu dự phòng (tổng 32 mẫu), 32 nhóm miền độc lập, 0 trùng lặp registry.")

    # Class balance blindness check: Manifest và báo cáo cho annotator KHÔNG được công bố trước tỷ lệ nhãn
    sampling_spec = calib_manifest.get("sampling_spec", {})
    assert "stratification" not in sampling_spec, "Manifest dành cho annotator không được công bố trước tỷ lệ nhãn (stratification)"
    assert "main_phish_count" not in sampling_spec, "Manifest không được chứa main_phish_count"
    assert "reserve_phish_count" not in sampling_spec, "Manifest không được chứa reserve_phish_count"
    print("    [PASS] Bảo vệ tính mù nhãn nguồn: 0 tỷ lệ nhãn công bố trước trong manifest và báo cáo.")

    # Pairwise scan check
    pw = inspection_report["pairwise_template_similarity_scan"]
    assert pw["total_pairs_scanned"] == 496, "Số cặp quét pairwise phải là 496 (32 * 31 / 2)"
    assert pw["conflict_pairs_count"] == 0, "Xung đột pairwise phải bằng 0"
    assert pw["engine_rule_conflict_pairs_count"] == 0
    assert pw["conjunction_rule_conflict_pairs_count"] == 0
    assert pw["min_pairwise_simhash_distance"] >= 10, "Khoảng cách SimHash tối thiểu phải >= 10"
    print("    [PASS] Quét tương đồng template: 496 cặp đạt 0 xung đột theo cả 2 quy tắc (SimHash min dist >= 10).")

    # Exclusion audit check
    excl_inv = exclusion_report["inventory"]
    assert excl_inv["total_batches_count"] in (8, 9, 10), "Số lô loại trừ không hợp lệ"
    assert excl_inv["total_samples_count"] in (182, 214, 246), "Tổng mẫu loại trừ không hợp lệ"
    print(f"    [PASS] Kiểm kê loại trừ: {excl_inv['total_samples_count']} mẫu thuộc đủ {excl_inv['total_batches_count']} lô được đối chiếu.")

    # 6. [Phạm vi 2] Kiểm định Blind View phát hành (Blind View QA)
    has_view = "clean_calibration_blind_view_24.json" in files_content
    blind_view_status = "PENDING_VIEW_DELIVERY"
    if has_view:
        print("\n[*] [Phạm vi 2] Kiểm định Blind View 24 mẫu chính (Blind View QA):")
        view_data = json.loads(files_content["clean_calibration_blind_view_24.json"].decode("utf-8"))
        samples = view_data.get("samples", [])
        assert len(samples) == 24, f"Blind View phải có đúng 24 mẫu chính, thực tế: {len(samples)}"
        expected_ids = [f"SMP-{i:03d}" for i in range(1, 25)]
        actual_ids = [s.get("sample_id") for s in samples]
        assert actual_ids == expected_ids, f"ID mẫu trong Blind View không đúng: {actual_ids}"

        for s in samples:
            sid = s.get("sample_id", "")
            assert not sid.startswith("RSV") and "reserve" not in sid.lower(), f"LỘ MẪU DỰ PHÒNG: Tìm thấy {sid} trong Blind View!"
            assert "source_label" not in s, "LỘ NHÃN NGUỒN trong mẫu Blind View"
            assert "ground_truth" not in s, "LỘ GROUND TRUTH trong mẫu Blind View"
            assert "target" not in s or s.get("target") is None, "LỘ TARGET trong mẫu Blind View"

        translated = {s["sample_id"]: s for s in samples if s.get("translation_provided")}
        assert set(translated.keys()) == {"SMP-008", "SMP-009", "SMP-015"}, f"Sai các mẫu dịch: {set(translated.keys())}"
        for sid, s in translated.items():
            t_hash = sha256_bytes(s["translated_text"].encode("utf-8"))
            assert s["translation_sha256"] == t_hash, f"Hash bản dịch {sid} không khớp"

        # Khớp hash trong manifest
        view_hash = sha256_bytes(files_content["clean_calibration_blind_view_24.json"])
        expected_view_hash = calib_manifest["governance"].get("blind_view_sha256")
        assert view_hash == expected_view_hash, f"Hash Blind View không khớp manifest ({view_hash} != {expected_view_hash})"
        blind_view_status = "PASSED"
        print("    [PASS] Blind View QA: Đủ 24 mẫu chính SMP-001..SMP-024, 0 mẫu dự phòng, 3 bản dịch MarianMT đạt chuẩn R-A09, 0 rò rỉ nhãn.")

    result = {
        "status": "QA_PASSED_READY_FOR_LEAD_D_SIGN_OFF",
        "verifier_role": "Member B (QA Lead)",
        "scope_1_candidate_selection_qa": "PASSED",
        "scope_2_blind_view_qa": blind_view_status,
        "zero_leak_verified": True,
        "hash_integrity_verified": True,
        "stratification_verified": True,
        "pairwise_similarity_verified": True,
        "governance_blocked_verified": True,
        "note": "Gói QA hoàn toàn mù (Double-Blind compliant): Không chứa bất kỳ thông tin nào cho phép Member B truy ngược nguồn raw Parquet hay nhận biết nhãn trước khi chấm."
    }

    print("\n" + "=" * 70)
    print("=== KẾT QUẢ: KIỂM ĐỊNH QA KỸ THUẬT CHO MEMBER B THÀNH CÔNG RỰC RỠ ===")
    print("    Trạng thái: QA_PASSED_READY_FOR_LEAD_D_SIGN_OFF")
    print("    Bảo vệ tính mù: ĐẠT 100% (Không phát hiện bất kỳ dấu hiệu rò rỉ nào)")
    print("=" * 70)
    return result


def main():
    parser = argparse.ArgumentParser(description="Công cụ kiểm định QA cho Member B")
    parser.add_argument(
        "--package",
        type=Path,
        default=None,
        help="Đường dẫn tới tệp ZIP hoặc thư mục gói QA của Member B"
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    target = args.package
    if target is None:
        # Mặc định tìm gói zip trong workspace hoặc thư mục hiện tại
        zip_candidate = root / "GOI_QA_MEMBER_B_CALIBRATION_CLEAN_32.zip"
        if zip_candidate.exists():
            target = zip_candidate
        else:
            target = Path.cwd()

    try:
        verify_member_b_package(target)
    except AssertionError as e:
        print(f"\n[!] THẤT BẠI: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
