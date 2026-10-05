"""Bộ kiểm thử cho CLI evaluate_kappa.py (Nghiệm thu Pass 1 & Cohen's Kappa)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_SCRIPT = PROJECT_ROOT / "scripts" / "evaluate_kappa.py"


def _make_sample_record(
    annotator_id: str,
    sample_id: str,
    class_label: str = "phishing",
    primary_org: str = "microsoft",
    seconds_spent: float = 60.0,
    evidence_note: str = "test note",
    **kwargs,
) -> dict:
    base = {
        "annotator_id": annotator_id,
        "sample_id": sample_id,
        "pass_id": 1,
        "class_label": class_label,
        "primary_org_status": "identified",
        "catalog_status": "in_catalog",
        "observed_service": "Office 365",
        "org_targets": [primary_org],
        "primary_org": primary_org,
        "identity_role": "identity_claim",
        "domain_role": "unverified",
        "evidence_note": evidence_note,
        "seconds_spent": seconds_spent,
        "random_subset": True,
        "difficult_case": False,
        "is_dry_run": False,
        "dataset_id": "REAL-PILOT-32-V1",
        "dataset_hash": "pkg_hash_abc123",
        "codebook_version": "1.0.0",
        "codebook_hash": "cb_hash_def456",
        "sampling_plan_version": "PILOT-PLAN-V1-FULL-OVERLAP",
        "sample_content_hash": f"content_hash_{sample_id}",
    }
    base.update(kwargs)
    return base


def test_evaluate_kappa_perfect_agreement(tmp_path):
    """Hai rater hoàn toàn trùng khớp nhãn và tổ chức -> Kappa = 1.0, 0 bất đồng thuận."""
    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"

    recs_a = [
        _make_sample_record("A", "S1", "phishing", "microsoft", seconds_spent=50.0),
        _make_sample_record("A", "S2", "benign", "google", seconds_spent=70.0),
        _make_sample_record("A", "S3", "phishing", "apple", seconds_spent=90.0),
    ]
    recs_b = [
        _make_sample_record("B", "S1", "phishing", "microsoft", seconds_spent=40.0),
        _make_sample_record("B", "S2", "benign", "google", seconds_spent=60.0),
        _make_sample_record("B", "S3", "phishing", "apple", seconds_spent=80.0),
    ]

    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    out_md = tmp_path / "report.md"
    out_json = tmp_path / "report.json"

    cmd = [
        sys.executable,
        str(EVAL_SCRIPT),
        "--rater-a", str(file_a),
        "--rater-b", str(file_b),
        "--output", str(out_md),
        "--json", str(out_json),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT)
    assert proc.returncode == 0, f"Lỗi CLI: {proc.stderr}"

    assert out_md.exists()
    assert out_json.exists()

    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["paired_sample_count"] == 3
    assert data["disagreement_count"] == 0
    assert data["kappa"]["class_label"]["kappa"] == 1.0
    assert data["kappa"]["primary_org"]["kappa"] == 1.0

    # Kiểm tra thống kê thời gian
    stats_a = data["seconds_spent"]["rater_a"]
    assert stats_a["count"] == 3
    assert stats_a["mean"] == 70.0
    assert stats_a["min"] == 50.0
    assert stats_a["max"] == 90.0
    assert stats_a["total"] == 210.0


def test_evaluate_kappa_detects_disagreements(tmp_path):
    """Phát hiện chính xác các ca bất đồng thuận và liệt kê chi tiết."""
    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"

    recs_a = [
        _make_sample_record("A", "S1", "phishing", "microsoft", evidence_note="fake login form"),
        _make_sample_record("A", "S2", "benign", "google", evidence_note="official portal"),
    ]
    recs_b = [
        # S1 lệch class_label (A: phish, B: benign)
        _make_sample_record("B", "S1", "benign", "microsoft", evidence_note="internal tool"),
        # S2 lệch primary_org (A: google, B: apple)
        _make_sample_record("B", "S2", "benign", "apple", evidence_note="apple id page"),
    ]

    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    out_json = tmp_path / "disagreements.json"
    cmd = [
        sys.executable,
        str(EVAL_SCRIPT),
        "--rater-a", str(file_a),
        "--rater-b", str(file_b),
        "--json", str(out_json),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT)
    assert proc.returncode == 0

    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["paired_sample_count"] == 2
    assert data["disagreement_count"] == 2

    disagreements = {d["sample_id"]: d for d in data["disagreements"]}
    assert "S1" in disagreements
    assert "class_label" in disagreements["S1"]["disagreement_fields"]
    assert disagreements["S1"]["evidence_note_a"] == "fake login form"
    assert disagreements["S1"]["evidence_note_b"] == "internal tool"

    assert "S2" in disagreements
    assert "primary_org" in disagreements["S2"]["disagreement_fields"]


def test_evaluate_kappa_rejects_missing_sample_id_or_different_sets(tmp_path):
    """CLI từ chối chạy khi tập sample_id giữa hai rater bị lệch nhau."""
    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"

    recs_a = [_make_sample_record("A", "S1")]
    recs_b = [_make_sample_record("B", "S2")]

    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    cmd = [
        sys.executable,
        str(EVAL_SCRIPT),
        "--rater-a", str(file_a),
        "--rater-b", str(file_b),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT)
    assert proc.returncode == 2
    assert "LỖI" in proc.stderr
