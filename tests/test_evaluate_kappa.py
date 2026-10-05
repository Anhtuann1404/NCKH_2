"""Bộ kiểm thử cho CLI evaluate_kappa.py (Nghiệm thu Pass 1 & Cohen's Kappa)."""

import json
from pathlib import Path
import subprocess
import sys

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


def test_evaluate_kappa_excludes_dry_run_from_timing_and_disagreements(tmp_path):
    """Lead D probe: 2 mẫu thật 10s + 1 dry-run 10.000s -> mean phải là 10.0s, không phải 3.340s."""
    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"

    recs_a = [
        _make_sample_record("A", "S1", "phishing", seconds_spent=10.0),
        _make_sample_record("A", "S2", "phishing", seconds_spent=10.0),
        # Dry-run 10.000s
        _make_sample_record("A", "DRY-01", "benign", seconds_spent=10000.0, is_dry_run=True),
    ]
    recs_b = [
        _make_sample_record("B", "S1", "phishing", seconds_spent=12.0),
        _make_sample_record("B", "S2", "phishing", seconds_spent=12.0),
        _make_sample_record("B", "DRY-01", "phishing", seconds_spent=9000.0, is_dry_run=True),
    ]

    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    out_json = tmp_path / "dryrun_out.json"
    cmd = [
        sys.executable,
        str(EVAL_SCRIPT),
        "--rater-a", str(file_a),
        "--rater-b", str(file_b),
        "--json", str(out_json),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT)
    assert proc.returncode == 0, f"Lỗi: {proc.stderr}"

    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["paired_sample_count"] == 2  # DRY-01 bị loại
    assert data["rater_a"]["dry_run_excluded"] == 1
    assert data["rater_b"]["dry_run_excluded"] == 1

    # Mean thời gian phải là 10.0s (không bị đội lên 3340s bởi 10.000s dry-run!)
    stats_a = data["seconds_spent"]["rater_a"]
    assert stats_a["mean"] == 10.0
    assert stats_a["total"] == 20.0


def test_evaluate_kappa_timing_breakdown_phishing_vs_benign(tmp_path):
    """Báo riêng thời gian phishing và benign để phục vụ chốt cỡ mẫu PLAN-01."""
    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"

    recs_a = [
        _make_sample_record("A", "S1", "phishing", seconds_spent=150.0),
        _make_sample_record("A", "S2", "phishing", seconds_spent=180.0),
        _make_sample_record("A", "S3", "benign", seconds_spent=30.0),
        # Ca khó thật (difficult_case=True) không được loại khỏi thời gian!
        _make_sample_record("A", "S4", "phishing", seconds_spent=300.0, difficult_case=True),
    ]
    recs_b = [
        _make_sample_record("B", "S1", "phishing", seconds_spent=140.0),
        _make_sample_record("B", "S2", "phishing", seconds_spent=160.0),
        _make_sample_record("B", "S3", "benign", seconds_spent=25.0),
        _make_sample_record("B", "S4", "phishing", seconds_spent=280.0, difficult_case=True),
    ]

    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    out_json = tmp_path / "timing_breakdown.json"
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
    timing_a = data["seconds_spent"]["rater_a"]

    # Phishing: S1 (150s), S2 (180s), S4 (300s) -> mean = 210.0s
    assert timing_a["phishing"]["count"] == 3
    assert timing_a["phishing"]["mean"] == 210.0

    # Benign: S3 (30s) -> mean = 30.0s
    assert timing_a["benign"]["count"] == 1
    assert timing_a["benign"]["mean"] == 30.0


def test_evaluate_kappa_rejects_same_annotator_or_wrong_pass(tmp_path):
    """Từ chối khi cả 2 tệp đều của A hoặc có pass_id=2 trong phiên Pass 1."""
    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"

    # Cả 2 tệp đều có annotator_id="A"
    recs_a = [_make_sample_record("A", "S1")]
    recs_b = [_make_sample_record("A", "S1")]
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(EVAL_SCRIPT), "--rater-a", str(file_a), "--rater-b", str(file_b)],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert ("cùng annotator_id" in proc.stderr or "không khớp với annotator kỳ vọng" in proc.stderr)

    # Bản ghi có pass_id=2
    recs_b_pass2 = [_make_sample_record("B", "S1", pass_id=2)]
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b_pass2) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(EVAL_SCRIPT), "--rater-a", str(file_a), "--rater-b", str(file_b), "--pass-id", "1"],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "pass_id=2" in proc.stderr


def test_evaluate_kappa_pilot_32_validation(tmp_path):
    """Kiểm tra cờ --verify-pilot-32 xác thực đủ 32 mẫu từ PILOT-001 đến PILOT-032."""
    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"

    # Chỉ có 5 mẫu -> thất bại khi bật --verify-pilot-32
    recs_a = [_make_sample_record("A", f"PILOT-{i:03d}") for i in range(1, 6)]
    recs_b = [_make_sample_record("B", f"PILOT-{i:03d}") for i in range(1, 6)]
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(EVAL_SCRIPT), "--rater-a", str(file_a), "--rater-b", str(file_b), "--verify-pilot-32"],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "yêu cầu đủ 32 mẫu" in proc.stderr

    # Đủ 32 mẫu chuẩn từ PILOT-001 đến PILOT-032 -> thành công
    recs_a_32 = [_make_sample_record("A", f"PILOT-{i:03d}") for i in range(1, 33)]
    recs_b_32 = [_make_sample_record("B", f"PILOT-{i:03d}") for i in range(1, 33)]
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a_32) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b_32) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(EVAL_SCRIPT), "--rater-a", str(file_a), "--rater-b", str(file_b), "--verify-pilot-32"],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 0
