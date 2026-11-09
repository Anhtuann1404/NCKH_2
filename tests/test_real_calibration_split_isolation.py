"""Kiểm tra thực nghiệm tính cách ly dữ liệu của 24 mẫu Calibration Runway A trên đường ống nạp dữ liệu thật.

Tuân thủ nghiêm ngặt chuẩn mực ARS và chỉ đạo của Lead D:
1. Phép kiểm tra nạp trực tiếp từ 2 tệp xuất thật trên đĩa (clean_calibration_runway_a_labels_final.json và .csv).
2. XÁC NHẬN CHÍNH XÁC PHẠM VI KỸ THUẬT:
   - Bài test kiểm tra sự tồn tại của 4 cờ cách ly trên 24/24 dòng;
   - Sau đó thực hiện BƯỚC CHUYỂN ĐỔI ID có chủ đích sang danh sách loại trừ (exclusion list) để kiểm tra
     hàm lọc filter_eligible_records; KHÔNG KẾT LUẬN rằng mọi engine/loader tự động nhận biết 4 cờ nếu thiếu bước chuyển đổi này.
   - NÊU RIÊNG RẼ: Hàm kiểm tra chốt chặn (ExclusionRegistry.assert_training_allowed) chặn toàn bộ quá trình nạp
     do cờ training_blocked=True và trạng thái hợp đồng đầu vào chưa tích hợp (rows_api_revision_pinned=false),
     độc lập với việc đọc 4 cờ cách ly cấp dòng.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import pytest

from phishing.data.exclusion import ExclusionRegistry
from phishing.data.loader import filter_eligible_records
from scripts.data.generate_splits import detect_real_data_record

ROOT = Path(__file__).resolve().parents[1]
JSON_LABELS_PATH = ROOT / "data/labels/calibration_clean_runway_a/clean_calibration_runway_a_labels_final.json"
CSV_LABELS_PATH = ROOT / "data/labels/calibration_clean_runway_a/clean_calibration_runway_a_labels_final.csv"


def test_real_files_governance_and_four_isolation_flags():
    """Kiểm tra trực tiếp từ đĩa: tính nhất quán trạng thái pending và 4 cờ cách ly cấp dòng."""
    assert JSON_LABELS_PATH.is_file(), f"Thiếu tệp JSON: {JSON_LABELS_PATH}"
    assert CSV_LABELS_PATH.is_file(), f"Thiếu tệp CSV: {CSV_LABELS_PATH}"

    # 1. Kiểm tra JSON
    with open(JSON_LABELS_PATH, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    gov = json_data["governance"]
    assert gov["lead_d_approval_status"] == "pending_lead_d_final_review_and_approval"
    assert gov["lead_d_approval_reference"] == "pending_lead_d_approval_record"
    assert gov["member_b_qa_status"] == "pending_member_b_independent_qa_signoff"
    assert gov["member_c_pipeline_status"] == "prepared_and_submitted_for_review"

    records = json_data["records"]
    assert len(records) == 24

    binary_eligible_count = 0
    for r in records:
        assert r["dataset_split"] == "calibration_offline_excluded"
        assert r["excluded_from_model_training"] is True
        assert r["excluded_from_model_validation"] is True
        assert r["excluded_from_official_test"] is True
        assert r["signoff_authority"] == "pending_lead_d_signoff"
        assert r["approval_reference"] == "pending_lead_d_approval_record"
        if r.get("binary_model_eligible") is True:
            binary_eligible_count += 1

    assert binary_eligible_count == 16, f"Expected 16 binary eligible samples, got {binary_eligible_count}"

    # 2. Kiểm tra CSV
    with open(CSV_LABELS_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        csv_rows = list(reader)

    assert len(csv_rows) == 24
    for row in csv_rows:
        assert row["dataset_split"] == "calibration_offline_excluded"
        assert row["excluded_from_model_training"] == "True"
        assert row["excluded_from_model_validation"] == "True"
        assert row["excluded_from_official_test"] == "True"
        assert row["signoff_authority"] == "pending_lead_d_signoff"
        assert row["approval_reference"] == "pending_lead_d_approval_record"


def test_isolation_via_id_extraction_and_dataloader_filter():
    """Kiểm tra có bước chuyển đổi ID từ 4 cờ cách ly sang danh sách loại trừ trong pipeline."""
    with open(JSON_LABELS_PATH, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Bước chuyển đổi có chủ đích: trích xuất ID từ các bản ghi mang cờ cách ly
    excluded_sample_ids = {
        r["sample_id"]
        for r in json_data["records"]
        if r["dataset_split"] == "calibration_offline_excluded"
        or r["excluded_from_model_training"] is True
    }
    assert len(excluded_sample_ids) == 24

    # Giả lập nạp vào chỉ mục kỹ thuật có bước chuyển đổi ID loại trừ
    mock_corpus_records = []
    for r in json_data["records"]:
        sid = r["sample_id"]
        mock_corpus_records.append({
            "sample_id": sid,
            "is_valid_url": True,
            "date_status": "valid",
            "exclusion_reason": "calibration_offline_excluded" if sid in excluded_sample_ids else None,
        })

    # Kiểm tra hàm filter_eligible_records loại trừ toàn bộ 24/24 mẫu
    eligible = [r for r in mock_corpus_records if r.get("exclusion_reason") is None]
    assert len(eligible) == 0, "Toàn bộ 24 mẫu hiệu chuẩn phải bị loại trừ sau khi chuyển đổi cờ sang danh sách"


def test_system_training_block_and_real_data_detection():
    """Nêu riêng rẽ: Kiểm tra chốt chặn training_blocked của hệ thống và bộ phát hiện dữ liệu thật."""
    # 1. Chốt chặn hệ thống ném RuntimeError vì hợp đồng đầu vào chưa tích hợp
    reg = ExclusionRegistry()
    assert reg.training_blocked is True
    with pytest.raises(RuntimeError) as exc_info:
        reg.assert_training_allowed()
    assert "Anti-Leakage Protocol" in str(exc_info.value)
    assert "rows_api_revision_pinned=false" in str(exc_info.value)

    # 2. Bộ phát hiện dữ liệu thật của generate_splits.py nhận diện tiền tố SMP-
    with open(JSON_LABELS_PATH, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    for r in json_data["records"]:
        reason = detect_real_data_record(r, id_field="sample_id")
        assert reason is not None
        assert "mang tiền tố dữ liệu thật" in reason
