"""Unit test cho analyze_pass1_v2.py sử dụng synthetic fixtures."""

import json
from pathlib import Path
import pytest

from phishing.annotation.org_normalization import build_org_alias_mapping
from scripts.data.analyze_pass1_v2 import (
    generate_public_summary_matrix,
    generate_restricted_disagreement_table,
)


def _make_sample(sid, class_label, primary_org, note=""):
    return {
        "sample_id": sid,
        "class_label": class_label,
        "primary_org": primary_org,
        "evidence_note": note,
        "difficult_case": False,
        "is_dry_run": False,
    }


def test_generate_restricted_disagreement_table_synthetic():
    alias_mapping = build_org_alias_mapping()

    recs_a = [
        _make_sample("S1", "phishing", "microsoft"),
        _make_sample("S2", "benign", "google"),
        _make_sample("S3", "insufficient_evidence", "unknown"),
    ]
    recs_b = [
        _make_sample("S1", "phishing", "microsoft"),            # Đồng thuận cả lớp lẫn org
        _make_sample("S2", "phishing", "google"),                  # Lệch lớp (benign vs phishing)
        _make_sample("S3", "insufficient_evidence", "apple"),     # Lệch org (unknown vs apple)
    ]

    res = generate_restricted_disagreement_table(recs_a, recs_b, alias_mapping)

    assert res["total_samples"] == 3
    assert res["total_disagreements"] == 2
    assert res["class_disagreement_count"] == 1
    assert res["org_disagreement_count"] == 1
    assert res["overlap_both_count"] == 0

    # Kiểm tra S2 trong danh sách bất đồng
    s2_entry = next(r for r in res["disagreements"] if r["sample_id"] == "S2")
    assert s2_entry["class_disagreement"] is True
    assert s2_entry["org_disagreement"] is False
    assert s2_entry["adjudication_status"] == "pending_lead_review"


def test_generate_public_summary_matrix_synthetic():
    recs_a = [
        _make_sample("S1", "benign", "none"),
        _make_sample("S2", "benign", "none"),
        _make_sample("S3", "phishing", "none"),
    ]
    recs_b = [
        _make_sample("S1", "benign", "none"),
        _make_sample("S2", "phishing", "none"),
        _make_sample("S3", "phishing", "none"),
    ]

    summary = generate_public_summary_matrix(recs_a, recs_b)
    matrix = summary["confusion_matrix"]

    assert matrix["benign"]["benign"] == 1
    assert matrix["benign"]["phishing"] == 1
    assert matrix["phishing"]["phishing"] == 1
    assert summary["disagreement_patterns"] == {"A=benign / B=phishing": 1}


def test_canonical_json_bytes_identical_across_newline_modes(tmp_path):
    """Regression test: chứng minh to_canonical_json_bytes tạo byte và hash 100% giống nhau độc lập OS."""
    from scripts.data.analyze_pass1_v2 import to_canonical_json_bytes, write_canonical_json
    import hashlib

    sample_dict = {
        "dataset": "REAL-PILOT-32-V2",
        "sample_count": 32,
        "metrics": {"kappa": 0.3139, "agreement": 0.5625},
        "notes": "Kiểm tra dấu xuống dòng tiếng Việt\nvà định dạng đa nền tảng.",
    }

    b1 = to_canonical_json_bytes(sample_dict)
    # Không chứa ký tự carriage return \r (0x0D)
    assert b"\r" not in b1
    assert b1.endswith(b"\n")

    # Giả lập ghi trên Windows với CRLF
    fake_windows_path = tmp_path / "fake_windows.json"
    fake_windows_text = json.dumps(sample_dict, ensure_ascii=False, indent=2).replace("\n", "\r\n") + "\r\n"
    fake_windows_path.write_bytes(fake_windows_text.encode("utf-8"))
    assert b"\r\n" in fake_windows_path.read_bytes()

    # Sau khi qua write_canonical_json, byte LF được phục hồi cố định
    h_fixed = write_canonical_json(fake_windows_path, sample_dict)
    fixed_bytes = fake_windows_path.read_bytes()
    assert b"\r" not in fixed_bytes
    assert hashlib.sha256(b1).hexdigest() == h_fixed


def test_report_marks_org_kappa_provisional_on_consistency_anomalies():
    """Regression test: đánh dấu κ tổ chức tạm thời khi có mẫu identified + unknown/no_clear_target."""
    alias_mapping = build_org_alias_mapping()

    recs_a = [
        {"sample_id": "S1", "class_label": "phishing", "primary_org": "unknown",
         "primary_org_status": "identified", "evidence_note": "A ghi identified nhưng quên org",
         "difficult_case": False, "is_dry_run": False},
        {"sample_id": "S2", "class_label": "benign", "primary_org": "google",
         "primary_org_status": "identified", "evidence_note": "", "difficult_case": False, "is_dry_run": False},
    ]
    recs_b = [
        {"sample_id": "S1", "class_label": "phishing", "primary_org": "unknown",
         "primary_org_status": "unknown", "evidence_note": "", "difficult_case": False, "is_dry_run": False},
        {"sample_id": "S2", "class_label": "benign", "primary_org": "google",
         "primary_org_status": "identified", "evidence_note": "", "difficult_case": False, "is_dry_run": False},
    ]

    table_data = generate_restricted_disagreement_table(recs_a, recs_b, alias_mapping)
    assert table_data["consistency_anomalies_a_count"] == 1
    assert table_data["consistency_anomalies_b_count"] == 0

    s1_entry = next(r for r in table_data["disagreements"] if r["sample_id"] == "S1")
    assert s1_entry["consistency_anomaly_a"] == "identified_with_unknown"
    assert s1_entry["consistency_anomaly_b"] is None


def test_public_summary_forbids_sample_ids_and_pilot_tokens():
    """Quy tắc ARS: Báo cáo công khai tuyệt đối không chứa khóa sample_id hoặc chuỗi PILOT-xxx."""
    import re
    from scripts.data.analyze_pass1_v2 import build_public_summary_report, generate_restricted_disagreement_table

    alias_mapping = build_org_alias_mapping()
    recs_a = [
        {"sample_id": "PILOT-001", "class_label": "benign", "primary_org": "microsoft",
         "primary_org_status": "identified", "evidence_note": "A note", "difficult_case": False, "is_dry_run": False},
        {"sample_id": "PILOT-002", "class_label": "phishing", "primary_org": "google",
         "primary_org_status": "identified", "evidence_note": "A note 2", "difficult_case": False, "is_dry_run": False},
    ]
    recs_b = [
        {"sample_id": "PILOT-001", "class_label": "phishing", "primary_org": "microsoft",
         "primary_org_status": "identified", "evidence_note": "B note", "difficult_case": False, "is_dry_run": False},
        {"sample_id": "PILOT-002", "class_label": "phishing", "primary_org": "google",
         "primary_org_status": "identified", "evidence_note": "B note 2", "difficult_case": False, "is_dry_run": False},
    ]

    restricted = generate_restricted_disagreement_table(recs_a, recs_b, alias_mapping)
    org_comp = {
        "raw_agreement_count": 2, "raw_kappa": 1.0, "normalized_agreement_count": 2,
        "normalized_kappa": 1.0, "resolved_by_normalization_count": 0,
    }

    summary = build_public_summary_report(recs_a, recs_b, restricted, org_comp)
    raw_json = json.dumps(summary, ensure_ascii=False)

    # 1. Không rò rỉ mã mẫu dạng PILOT-xxx
    assert re.search(r"PILOT-\d+", raw_json, re.IGNORECASE) is None
    # 2. Không rò rỉ khóa sample_id
    assert "sample_id" not in summary
    assert "sample_id" not in summary.get("confusion_matrix", {})
    assert "sample_id" not in summary.get("disagreement_counts_reconciliation", {})


def test_reconciliation_counts_computed_dynamically_from_inputs():
    """Kiểm tra các trường đối chiếu được tính toán động từ input, không bị ghi cứng."""
    from scripts.data.analyze_pass1_v2 import build_public_summary_report, generate_restricted_disagreement_table

    alias_mapping = build_org_alias_mapping()

    # Trường hợp 1: 3 mẫu, 1 lệch class, 1 lệch org
    recs_a1 = [
        {"sample_id": "S1", "class_label": "benign", "primary_org": "microsoft",
         "primary_org_status": "identified", "difficult_case": False, "is_dry_run": False},
        {"sample_id": "S2", "class_label": "phishing", "primary_org": "google",
         "primary_org_status": "identified", "difficult_case": False, "is_dry_run": False},
        {"sample_id": "S3", "class_label": "phishing", "primary_org": "apple",
         "primary_org_status": "identified", "difficult_case": False, "is_dry_run": False},
    ]
    recs_b1 = [
        {"sample_id": "S1", "class_label": "phishing", "primary_org": "microsoft",  # Lệch class
         "primary_org_status": "identified", "difficult_case": False, "is_dry_run": False},
        {"sample_id": "S2", "class_label": "phishing", "primary_org": "meta",       # Lệch org
         "primary_org_status": "identified", "difficult_case": False, "is_dry_run": False},
        {"sample_id": "S3", "class_label": "phishing", "primary_org": "apple",      # Trùng
         "primary_org_status": "identified", "difficult_case": False, "is_dry_run": False},
    ]

    res1 = generate_restricted_disagreement_table(recs_a1, recs_b1, alias_mapping)
    org_comp1 = {
        "raw_agreement_count": 2, "raw_kappa": 0.5, "normalized_agreement_count": 2,
        "normalized_kappa": 0.5, "resolved_by_normalization_count": 0,
    }
    s1 = build_public_summary_report(recs_a1, recs_b1, res1, org_comp1)
    reconcil1 = s1["disagreement_counts_reconciliation"]

    # Động tính: S1 (lệch class) và S2 (lệch org) -> raw_disagreements_count = 2
    assert reconcil1["raw_disagreements_count"] == 2
    assert reconcil1["class_disagreements"] == 1
    assert reconcil1["normalized_org_disagreements"] == 1
    assert reconcil1["adjudication_table_cases_count"] == 2

    # Trường hợp 2: Đồng thuận hoàn toàn cả 3 mẫu
    recs_b2 = [
        {"sample_id": "S1", "class_label": "benign", "primary_org": "microsoft",
         "primary_org_status": "identified", "difficult_case": False, "is_dry_run": False},
        {"sample_id": "S2", "class_label": "phishing", "primary_org": "google",
         "primary_org_status": "identified", "difficult_case": False, "is_dry_run": False},
        {"sample_id": "S3", "class_label": "phishing", "primary_org": "apple",
         "primary_org_status": "identified", "difficult_case": False, "is_dry_run": False},
    ]
    res2 = generate_restricted_disagreement_table(recs_a1, recs_b2, alias_mapping)
    org_comp2 = {
        "raw_agreement_count": 3, "raw_kappa": 1.0, "normalized_agreement_count": 3,
        "normalized_kappa": 1.0, "resolved_by_normalization_count": 0,
    }
    s2 = build_public_summary_report(recs_a1, recs_b2, res2, org_comp2)
    reconcil2 = s2["disagreement_counts_reconciliation"]

    assert reconcil2["raw_disagreements_count"] == 0
    assert reconcil2["class_disagreements"] == 0
    assert reconcil2["normalized_org_disagreements"] == 0
    assert reconcil2["adjudication_table_cases_count"] == 0


