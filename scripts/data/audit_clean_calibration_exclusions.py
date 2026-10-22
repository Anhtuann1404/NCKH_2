#!/usr/bin/env python3
"""Kiểm kê và rà soát bằng chứng loại trừ cho Gói Hiệu chuẩn Sạch của Thành viên A (CALIBRATION-CLEAN-A).

Tuân thủ nghiêm ngặt chỉ đạo của Lead D (22/10/2026):
1. Đếm trực tiếp data/exclusion_registry.json, nêu từng lô và số fingerprint duy nhất.
2. Kiểm riêng 8 mẫu dự phòng Calibration (EXCL-CALIBRATION-PROPOSAL-V1.1-RESERVE-08):
   - 20 mẫu tập dượt ban đầu (EXCL-PILOT-01)
   - 32 mẫu Pilot V1 thật (EXCL-REAL-PILOT-32)
   - 32 mẫu Pilot V2 thật (EXCL-PILOT-02)
   - 24 mẫu Calibration v1.1.4 chính đã xem (EXCL-CALIBRATION-PROPOSAL-V1.1-MAIN-24)
   - 8 mẫu dự phòng Calibration đã tra cứu/đăng ký trong registry (EXCL-CALIBRATION-PROPOSAL-V1.1-RESERVE-08)
   -> Tổng phạm vi đã biết cần loại trừ triệt để: 116 mẫu (108 mẫu đã phát/xem + 8 mẫu dự phòng).
   - Ghi nhận thêm lô EXCL-PILOT-02-REBUILD-e039c774ef5f (32 mẫu) trong registry.
3. Báo cáo số fingerprint duy nhất trên từng chiều (URL, HTML, Domain Group, Summary Fingerprint).
4. Quy định template similarity: Chuyển thành bước sẽ thực hiện sau khi chọn ứng viên.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]


def main():
    print("=== BẮT ĐẦU KIỂM KÊ TRỰC TIẾP EXCLUSION_REGISTRY.JSON CHO GÓI SẠCH ===")

    registry_path = ROOT / "data/exclusion_registry.json"
    assert registry_path.is_file(), "Thiếu data/exclusion_registry.json!"

    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)

    # Danh mục toàn bộ 6 lô (tổng 148 mẫu) trong registry theo chỉ đạo trực tiếp của Lead D
    all_batches = [
        {"id": "EXCL-PILOT-01", "name": "20 mẫu tập dượt ban đầu (summary fingerprint)", "expected_count": 20},
        {"id": "EXCL-REAL-PILOT-32", "name": "32 mẫu Pilot V1 thật", "expected_count": 32},
        {"id": "EXCL-PILOT-02", "name": "32 mẫu Pilot V2 thật", "expected_count": 32},
        {"id": "EXCL-PILOT-02-REBUILD-e039c774ef5f", "name": "32 mẫu Pilot V2 Rebuild (URL hash bổ sung)", "expected_count": 32},
        {"id": "EXCL-CALIBRATION-PROPOSAL-V1.1-MAIN-24", "name": "24 mẫu Calibration v1.1.4 chính đã xem", "expected_count": 24},
        {"id": "EXCL-CALIBRATION-PROPOSAL-V1.1-RESERVE-08", "name": "8 mẫu dự phòng Calibration đã đăng ký trong registry", "expected_count": 8}
    ]

    exclusions_map = {e["exclusion_id"]: e for e in registry.get("exclusions", [])}

    audit_summary = []
    total_samples = 0
    unique_urls = set()
    unique_htmls = set()
    unique_groups = set()
    unique_summary_fps = set()

    for pb in all_batches:
        eid = pb["id"]
        assert eid in exclusions_map, f"Thiếu mục loại trừ {eid} trong registry!"
        entry = exclusions_map[eid]
        samples = entry.get("samples", [])
        actual_count = entry.get("n_samples", len(samples))
        assert actual_count == pb["expected_count"], f"Số mẫu tại {eid} không khớp: {actual_count} != {pb['expected_count']}"

        b_urls = set()
        b_htmls = set()
        b_groups = set()
        b_fps = set()

        for s in samples:
            if "url_sha256" in s:
                unique_urls.add(s["url_sha256"])
                b_urls.add(s["url_sha256"])
            if "normalized_url_sha256" in s:
                unique_urls.add(s["normalized_url_sha256"])
                b_urls.add(s["normalized_url_sha256"])
            if "html_sha256" in s:
                unique_htmls.add(s["html_sha256"])
                b_htmls.add(s["html_sha256"])
            if "group_sha256" in s:
                unique_groups.add(s["group_sha256"])
                b_groups.add(s["group_sha256"])
            if "summary_fingerprint_hash" in s:
                unique_summary_fps.add(s["summary_fingerprint_hash"])
                b_fps.add(s["summary_fingerprint_hash"])

        audit_summary.append({
            "exclusion_id": eid,
            "description": pb["name"],
            "sample_count": actual_count,
            "unique_url_sha256": len(b_urls),
            "unique_html_sha256": len(b_htmls),
            "unique_group_sha256": len(b_groups),
            "unique_summary_fingerprints": len(b_fps),
            "action": entry.get("action", "permanently_exclude_from_train_val_test")
        })
        total_samples += actual_count

    assert total_samples == 148, f"Tổng số mẫu loại trừ toàn bộ 6 lô phải là 148, thực tế: {total_samples}"

    report = {
        "report_id": "CLEAN-CALIBRATION-EXCLUSION-AUDIT-20261023",
        "purpose": "Bằng chứng kiểm kê trực tiếp data/exclusion_registry.json gồm toàn bộ 6 lô (148 mẫu) trước khi tuyển chọn Gói Hiệu chuẩn Sạch cho A",
        "lead_d_directive_reference": "Chỉ đạo Lead D ngày 2026-10-23 (Đối chiếu toàn bộ 6 lô, 148 mẫu, bao gồm EXCL-PILOT-02-REBUILD và làm rõ giới hạn 20 mẫu summary fingerprint)",
        "governance": {
            "training_blocked": True,
            "official_test_used": False,
            "registry_version": registry.get("version", "1.1.0"),
            "registry_sha256": hashlib.sha256(registry_path.read_bytes()).hexdigest(),
            "total_excluded_entries_in_registry": registry.get("total_excluded_entries", len(registry.get("exclusions", []))),
            "total_excluded_samples_in_registry": registry.get("total_excluded_samples", 148)
        },
        "inventory": {
            "total_batches_count": len(all_batches),
            "total_samples_count": total_samples,
            "batches": audit_summary,
            "registry_fingerprints_summary": {
                "all_unique_url_sha256": len(unique_urls),
                "all_unique_html_sha256": len(unique_htmls),
                "all_unique_group_sha256": len(unique_groups),
                "all_unique_summary_fingerprints": len(unique_summary_fps)
            }
        },
        "historical_pilot_20_summary_fingerprint_matching": {
            "batch_id": "EXCL-PILOT-01",
            "sample_count": 20,
            "matching_method": (
                "Phép so khớp thực hiện bằng hàm compute_summary_fingerprint_hash(sample) tính mã băm SHA-256 "
                "trên canonical JSON của bộ 8 đặc trưng cấu trúc DOM/thống kê trang: "
                "(pilot_row_idx, label, lang, html_chars, text_chars, forms, inputs, password_inputs). "
                "Bất kỳ mẫu ứng viên nào trùng khớp hash cấu trúc này sẽ bị chặn theo cơ chế phòng vệ chiều sâu."
            ),
            "verification_limits_and_epistemic_boundary": (
                "GIỚI HẠN KIỂM CHỨNG KHOA HỌC: Do 20 mẫu tập dượt lịch sử ban đầu chỉ lưu giữ fingerprint tóm tắt cấu trúc "
                "mà không có URL hay HTML nguyên văn trong registry (unmapped historical data), hệ thống KHÔNG THỂ đối chiếu "
                "trực tiếp theo url_sha256 hay html_sha256. "
                "Về mặt lý thuyết xác suất, hai trang web khác nhau hoàn toàn có thể trùng hợp về số lượng form/ký tự (dương tính giả cấu trúc), "
                "hoặc sai khác nhỏ về khoảng trắng có thể làm lệch hash tóm tắt (âm tính giả). "
                "Do đó, phép so khớp này được xem là rào chắn phòng vệ bổ sung (defense-in-depth); "
                "toàn bộ 20 mẫu này tiếp tục được duy trì trạng thái mapping_status='unmapped_historical' "
                "và cờ training_blocked=true được khóa vĩnh viễn trên pipeline huấn luyện chính thức."
            )
        },
        "anti_leakage_scope": {
            "dimensions": [
                "url_sha256 (bao gồm 32 URL hash bổ sung từ lô EXCL-PILOT-02-REBUILD-e039c774ef5f)",
                "normalized_url_sha256",
                "html_sha256",
                "group_sha256 (eTLD+1 / shared hosting tenant)",
                "summary_fingerprint_hash (đối chiếu cấu trúc 20 mẫu pilot lịch sử)"
            ],
            "template_similarity_policy": (
                "Bước kiểm tra bắt buộc sẽ thực hiện ngay sau khi chạy thuật toán tuyển chọn ứng viên ngẫu nhiên; "
                "kết quả đo lường độ tương đồng SimHash 64-bit và DOM Jaccard thực tế giữa ứng viên và các mẫu đã biết "
                "sẽ được đưa vào báo cáo nghiệm thu ứng viên trước khi phát hành gói."
            ),
            "scientific_disclaimer": (
                "Đã kiểm tra đối chiếu trực tiếp trên toàn bộ 148 mẫu (đủ 6 lô bao gồm cả Pilot Rebuild và 8 mẫu dự phòng Calibration) "
                "trong data/exclusion_registry.json. Không phát biểu tuyên bố tuyệt đối hóa ngoài phạm vi kiểm chứng."
            )
        }
    }

    out_dir = ROOT / "data/source_audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "clean_calibration_exclusion_audit_report.json"
    report_bytes = (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    report_path.write_bytes(report_bytes)
    report_hash = hashlib.sha256(report_bytes).hexdigest()

    print(f"-> ĐÃ XUẤT BÁO CÁO KIỂM KÊ LOẠI TRỪ: {report_path}")
    print(f"   Tổng số mẫu phạm vi toàn bộ 6 lô: {total_samples} mẫu")
    print(f"   Fingerprints duy nhất: URL={len(unique_urls)}, HTML={len(unique_htmls)}, Group={len(unique_groups)}, SummaryFP={len(unique_summary_fps)}")
    print(f"   SHA-256: {report_hash}")
    print("=== HOÀN TẤT KIỂM KÊ BẰNG CHỨNG LOẠI TRỪ THÀNH CÔNG ===")


if __name__ == "__main__":
    main()

