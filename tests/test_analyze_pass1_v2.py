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
