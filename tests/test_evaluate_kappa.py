"""Bộ kiểm thử cho CLI evaluate_kappa.py (Nghiệm thu Pass 1 & Cohen's Kappa)."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Optional

import pytest

from phishing.annotation import compute_sample_content_hash

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
        "dataset_id": "TEST-EVAL-V1",
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


def _create_pilot_fixture(target_dir: Path):
    """Tự sinh fixture 32 mẫu tự chứa, độc lập với dữ liệu bảo mật (Khắc phục Điểm 3 của Lead D)."""
    target_dir.mkdir(parents=True, exist_ok=True)
    samples = []
    for i in range(1, 33):
        samples.append({
            "sample_id": f"PILOT-{i:03d}",
            "url": f"https://fixture-{i}.example.com/login",
            "html": f"<html><body>Fixture {i}</body></html>",
            "random_subset": True,
        })
    blind_data = {
        "dataset_id": "REAL-PILOT-32-V1",
        "is_synthetic": False,
        "sample_count": 32,
        "sampling_plan_version": "PILOT-PLAN-V1-FULL-OVERLAP",
        "samples": samples,
    }
    bv_file = target_dir / "blind_view_pilot_real.json"
    bv_bytes = json.dumps(blind_data, ensure_ascii=False, indent=2).encode("utf-8")
    bv_file.write_bytes(bv_bytes)
    bv_sha = hashlib.sha256(bv_bytes).hexdigest()

    manifest = {
        "dataset_id": "REAL-PILOT-32-V1",
        "is_synthetic": False,
        "sample_count": 32,
        "ready_for_annotation": True,
        "codebook_version": "1.0.0",
        "codebook_sha256": "12de9c2f3b457938039b05c72c651d6650f403b620216516262134a3313a2ed1",
        "sampling_plan_version": "PILOT-PLAN-V1-FULL-OVERLAP",
        "blind_view_path": str(bv_file.as_posix()),
        "blind_view_sha256": bv_sha,
        "acceptance": {"D": "approved", "B": "approved"},
    }
    man_file = target_dir / "pilot_manifest.json"
    man_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return bv_file, man_file, blind_data, manifest


def _load_fixture_pilot_records(annotator_id: str, fixture_dir: Path) -> tuple[list[dict], Path]:
    bv_file, man_file, blind_data, manifest = _create_pilot_fixture(fixture_dir)
    recs = []
    for s in blind_data["samples"]:
        sid = s["sample_id"]
        content_hash = compute_sample_content_hash(s)
        rec = _make_sample_record(
            annotator_id,
            sid,
            class_label="phishing" if int(sid.split("-")[1]) <= 20 else "benign",
            primary_org="microsoft",
            dataset_id=manifest["dataset_id"],
            dataset_hash=manifest["blind_view_sha256"],
            codebook_version=manifest["codebook_version"],
            codebook_hash=manifest["codebook_sha256"],
            sampling_plan_version=manifest["sampling_plan_version"],
            sample_content_hash=content_hash,
            random_subset=s.get("random_subset", True),
        )
        recs.append(rec)
    return recs, man_file


def test_v2_kappa_selects_v2_manifest_and_rejects_wrong_package_or_hash(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location('fixture_evaluate_kappa', EVAL_SCRIPT)
    evaluator = importlib.util.module_from_spec(spec); spec.loader.exec_module(evaluator)
    monkeypatch.setattr(evaluator, 'PROJECT_ROOT', tmp_path)
    configs = tmp_path / 'configs'; configs.mkdir()
    view_path, _, view, manifest = _create_pilot_fixture(tmp_path / 'pilot_fixture')
    view['dataset_id'] = 'REAL-PILOT-32-V2'
    view['sampling_plan_version'] = 'PILOT-PLAN-V2-FULL-OVERLAP'
    view_path.write_text(json.dumps(view, ensure_ascii=False), encoding='utf-8')
    view_hash = hashlib.sha256(view_path.read_bytes()).hexdigest()
    manifest.update(dataset_id='REAL-PILOT-32-V2', status='approved',
        blind_view_sha256=view_hash, sampling_plan_version='PILOT-PLAN-V2-FULL-OVERLAP',
        source_verification_status='verified_pinned_train_rows',
        exposure_review={'A': 'approved', 'B': 'approved', 'D': 'approved'})
    v2_manifest = configs / 'pilot_manifest_v2.json'
    v2_manifest.write_text(json.dumps(manifest), encoding='utf-8')
    records = {}
    for annotator in ('A', 'B'):
        rows = [_make_sample_record(annotator, sample['sample_id'],
            dataset_id='REAL-PILOT-32-V2', dataset_hash=view_hash,
            codebook_hash=manifest['codebook_sha256'],
            sampling_plan_version=manifest['sampling_plan_version'],
            sample_content_hash=compute_sample_content_hash(sample)) for sample in view['samples']]
        path = tmp_path / f'{annotator}.jsonl'
        path.write_text('\n'.join(json.dumps(row) for row in rows) + '\n', encoding='utf-8')
        records[annotator] = (path, rows)
    a_path, a_rows = records['A']; b_path, b_rows = records['B']
    result = evaluator.evaluate(a_path, b_path)
    assert result['pilot_32_verified'] is True
    assert 'REAL-PILOT-32-V2' in evaluator.build_markdown(result)
    assert 'REAL-PILOT-32-V1' not in evaluator.build_markdown(result)
    wrong_manifest = configs / 'pilot_manifest.json'
    wrong_manifest.write_text(json.dumps(dict(manifest, dataset_id='REAL-PILOT-32-V1')))
    with pytest.raises(ValueError, match='nhầm manifest V1/V2'):
        evaluator.evaluate(a_path, b_path, pilot_manifest_path=wrong_manifest)
    b_rows[0]['dataset_hash'] = '0' * 64
    b_path.write_text('\n'.join(json.dumps(row) for row in b_rows) + '\n', encoding='utf-8')
    with pytest.raises(ValueError, match='dataset_hash'):
        evaluator.evaluate(a_path, b_path)
    b_rows[0]['dataset_hash'] = view_hash
    b_path.write_text('\n'.join(json.dumps(row) for row in b_rows) + '\n', encoding='utf-8')
    manifest['status'] = 'pending_lead_acceptance'
    v2_manifest.write_text(json.dumps(manifest), encoding='utf-8')
    with pytest.raises(ValueError, match='PILOT V2 BLOCKED'):
        evaluator.evaluate(a_path, b_path)


def test_evaluate_kappa_pilot_32_validation(tmp_path):
    """Kiểm tra cờ --verify-pilot-32 xác thực đủ 32 mẫu và đối chiếu gói chuẩn REAL-PILOT-32-V1."""
    fixture_dir = tmp_path / "pilot_fixture"
    recs_a, man_file = _load_fixture_pilot_records("A", fixture_dir)
    recs_b, _ = _load_fixture_pilot_records("B", fixture_dir)

    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"

    # Chỉ có 5 mẫu -> thất bại khi bật --verify-pilot-32
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a[:5]) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b[:5]) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable, str(EVAL_SCRIPT),
            "--rater-a", str(file_a),
            "--rater-b", str(file_b),
            "--verify-pilot-32",
            "--pilot-manifest", str(man_file),
        ],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "yêu cầu đủ 32 mẫu" in proc.stderr

    # Đủ 32 mẫu chuẩn từ PILOT-001 đến PILOT-032 khớp manifest đã duyệt -> thành công
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    out_json = tmp_path / "pilot_out.json"
    proc = subprocess.run(
        [
            sys.executable, str(EVAL_SCRIPT),
            "--rater-a", str(file_a),
            "--rater-b", str(file_b),
            "--verify-pilot-32",
            "--pilot-manifest", str(man_file),
            "--json", str(out_json),
        ],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 0, f"Lỗi CLI: {proc.stderr}"
    res = json.loads(out_json.read_text(encoding="utf-8"))
    assert res["pilot_32_verified"] is True
    assert res["paired_sample_count"] == 32


def test_evaluate_kappa_pilot_rejects_wrong_package(tmp_path):
    """Lead D probe: 32 ID nhưng mang dataset_id 'WRONG-PACKAGE' phải bị chặn."""
    fixture_dir = tmp_path / "pilot_fixture"
    recs_a, man_file = _load_fixture_pilot_records("A", fixture_dir)
    recs_b, _ = _load_fixture_pilot_records("B", fixture_dir)

    for r in recs_a:
        r["dataset_id"] = "WRONG-PACKAGE"

    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable, str(EVAL_SCRIPT),
            "--rater-a", str(file_a),
            "--rater-b", str(file_b),
            "--verify-pilot-32",
            "--pilot-manifest", str(man_file),
        ],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "dataset_id không khớp manifest đã duyệt" in proc.stderr


def test_evaluate_kappa_pilot_rejects_mismatched_hashes(tmp_path):
    """Lead D probe: dataset_hash, codebook_hash hoặc sample_content_hash sai lệch phải bị chặn."""
    fixture_dir = tmp_path / "pilot_fixture"
    recs_a, man_file = _load_fixture_pilot_records("A", fixture_dir)
    recs_b, _ = _load_fixture_pilot_records("B", fixture_dir)

    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"

    # 1. Sai dataset_hash
    recs_a[0]["dataset_hash"] = "tampered_dataset_hash"
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable, str(EVAL_SCRIPT),
            "--rater-a", str(file_a),
            "--rater-b", str(file_b),
            "--verify-pilot-32",
            "--pilot-manifest", str(man_file),
        ],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "dataset_hash không khớp manifest đã duyệt" in proc.stderr

    # 2. Sai codebook_hash
    recs_a, man_file = _load_fixture_pilot_records("A", fixture_dir)
    recs_a[0]["codebook_hash"] = "tampered_codebook_hash"
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable, str(EVAL_SCRIPT),
            "--rater-a", str(file_a),
            "--rater-b", str(file_b),
            "--verify-pilot-32",
            "--pilot-manifest", str(man_file),
        ],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "codebook_hash không khớp manifest đã duyệt" in proc.stderr

    # 3. Sai sample_content_hash (nội dung mẫu bị sửa đổi ngầm)
    recs_a, man_file = _load_fixture_pilot_records("A", fixture_dir)
    recs_a[0]["sample_content_hash"] = "tampered_content_hash"
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable, str(EVAL_SCRIPT),
            "--rater-a", str(file_a),
            "--rater-b", str(file_b),
            "--verify-pilot-32",
            "--pilot-manifest", str(man_file),
        ],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "sample_content_hash không khớp với blind view đã duyệt" in proc.stderr


def test_evaluate_kappa_pilot_manifest_existence_and_approval(tmp_path):
    """Lead D probe: manifest không tồn tại hoặc chưa approved phải bị chặn."""
    fixture_dir = tmp_path / "pilot_fixture"
    recs_a, man_file = _load_fixture_pilot_records("A", fixture_dir)
    recs_b, _ = _load_fixture_pilot_records("B", fixture_dir)

    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    # Đường dẫn manifest không tồn tại
    non_existent = tmp_path / "no_manifest.json"
    proc = subprocess.run(
        [
            sys.executable, str(EVAL_SCRIPT),
            "--rater-a", str(file_a),
            "--rater-b", str(file_b),
            "--pilot-manifest", str(non_existent),
        ],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "Không tìm thấy tệp manifest pilot" in proc.stderr

    # Manifest chưa được Lead D approved
    fake_manifest = tmp_path / "unapproved_manifest.json"
    manifest_data = json.loads(man_file.read_text(encoding="utf-8"))
    manifest_data["acceptance"]["D"] = "pending"
    fake_manifest.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable, str(EVAL_SCRIPT),
            "--rater-a", str(file_a),
            "--rater-b", str(file_b),
            "--pilot-manifest", str(fake_manifest),
        ],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "chưa được Lead D phê duyệt" in proc.stderr


def test_evaluate_kappa_pilot_cannot_bypass_blind_view(tmp_path):
    """Lead D probe 1: Bắt buộc blind view tồn tại và kiểm tra hash byte, không được bỏ qua."""
    fixture_dir = tmp_path / "pilot_fixture"
    recs_a, man_file = _load_fixture_pilot_records("A", fixture_dir)
    recs_b, _ = _load_fixture_pilot_records("B", fixture_dir)

    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    # Manifest trỏ tới blind view không tồn tại
    fake_manifest = tmp_path / "missing_view_manifest.json"
    manifest_data = json.loads(man_file.read_text(encoding="utf-8"))
    manifest_data["blind_view_path"] = "non_existent_blind_view.json"
    fake_manifest.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable, str(EVAL_SCRIPT),
            "--rater-a", str(file_a),
            "--rater-b", str(file_b),
            "--pilot-manifest", str(fake_manifest),
        ],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "Không tìm thấy tệp blind view chuẩn" in proc.stderr

    # Manifest có blind_view_sha256 bị sai lệch
    fake_manifest_sha = tmp_path / "wrong_sha_manifest.json"
    manifest_data2 = json.loads(man_file.read_text(encoding="utf-8"))
    manifest_data2["blind_view_sha256"] = "wrong_sha256_hash_value"
    fake_manifest_sha.write_text(json.dumps(manifest_data2, ensure_ascii=False, indent=2), encoding="utf-8")

    proc2 = subprocess.run(
        [
            sys.executable, str(EVAL_SCRIPT),
            "--rater-a", str(file_a),
            "--rater-b", str(file_b),
            "--pilot-manifest", str(fake_manifest_sha),
        ],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc2.returncode == 2
    assert "LỖI TOÀN VẸN BLIND VIEW" in proc2.stderr


def test_evaluate_kappa_pilot_rejects_altered_random_subset(tmp_path):
    """Lead D probe 2: Thay đổi random_subset=false ở 1 mẫu làm giảm cỡ mẫu 31/32 phải bị chặn."""
    fixture_dir = tmp_path / "pilot_fixture"
    recs_a, man_file = _load_fixture_pilot_records("A", fixture_dir)
    recs_b, _ = _load_fixture_pilot_records("B", fixture_dir)

    # Đổi random_subset=False ở mẫu đầu tiên của cả A và B
    recs_a[0]["random_subset"] = False
    recs_b[0]["random_subset"] = False

    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable, str(EVAL_SCRIPT),
            "--rater-a", str(file_a),
            "--rater-b", str(file_b),
            "--verify-pilot-32",
            "--pilot-manifest", str(man_file),
        ],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "cờ 'random_subset' không khớp kế hoạch pilot đã khóa" in proc.stderr or "LỖI TẬP MẪU KAPPA" in proc.stderr


@pytest.mark.integration
@pytest.mark.skipif(
    not (PROJECT_ROOT / "data" / "annotations" / "blind_view_pilot_real.json").is_file(),
    reason="Chỉ chạy khi có dữ liệu thật blind_view_pilot_real.json trên môi trường tích hợp",
)
def test_evaluate_kappa_real_default_manifest(tmp_path):
    """Xác nhận khi không truyền --pilot-manifest trên môi trường có đủ tệp thật, CLI nạp đúng configs/pilot_manifest.json."""
    blind_path = PROJECT_ROOT / "data" / "annotations" / "blind_view_pilot_real.json"
    manifest_path = PROJECT_ROOT / "configs" / "pilot_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    blind_data = json.loads(blind_path.read_text(encoding="utf-8"))

    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"

    recs_a = []
    recs_b = []
    for s in blind_data["samples"]:
        sid = s["sample_id"]
        c_hash = compute_sample_content_hash(s)
        base_kwargs = {
            "dataset_id": manifest["dataset_id"],
            "dataset_hash": manifest["blind_view_sha256"],
            "codebook_version": manifest["codebook_version"],
            "codebook_hash": manifest["codebook_sha256"],
            "sampling_plan_version": manifest["sampling_plan_version"],
            "sample_content_hash": c_hash,
            "random_subset": s.get("random_subset", True),
        }
        recs_a.append(_make_sample_record("A", sid, **base_kwargs))
        recs_b.append(_make_sample_record("B", sid, **base_kwargs))

    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(EVAL_SCRIPT), "--rater-a", str(file_a), "--rater-b", str(file_b), "--verify-pilot-32"],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    if not manifest.get("ready_for_annotation"):
        assert proc.returncode != 0
        assert "ready_for_annotation != true" in proc.stderr or "Manifest pilot chưa ở trạng thái sẵn sàng" in proc.stderr
    else:
        assert proc.returncode == 0, f"Lỗi CLI với manifest mặc định: {proc.stderr}"


def test_evaluate_kappa_strict_annotator_validation(tmp_path):
    """Lead D probe 3: annotator_id thiếu, rỗng, sai annotator, hoặc lẫn lộn annotator."""
    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"

    # 1. Thiếu annotator_id
    recs_a = [_make_sample_record("A", "S1")]
    del recs_a[0]["annotator_id"]
    recs_b = [_make_sample_record("B", "S1")]
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(EVAL_SCRIPT), "--rater-a", str(file_a), "--rater-b", str(file_b)],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "thiếu trường bắt buộc 'annotator_id'" in proc.stderr

    # 2. annotator_id rỗng hoặc whitespace
    recs_a = [_make_sample_record("   ", "S1")]
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(EVAL_SCRIPT), "--rater-a", str(file_a), "--rater-b", str(file_b)],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "'annotator_id' không hợp lệ" in proc.stderr

    # 3. annotator_id không khớp expected ("C" thay vì "A")
    recs_a = [_make_sample_record("C", "S1")]
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(EVAL_SCRIPT), "--rater-a", str(file_a), "--rater-b", str(file_b)],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "không khớp với annotator kỳ vọng 'A'" in proc.stderr

    # 4. Lẫn lộn 2 annotator trong cùng một tệp A (S1 là A, S2 là B)
    recs_a = [
        _make_sample_record("A", "S1"),
        _make_sample_record("B", "S2"),
    ]
    recs_b = [
        _make_sample_record("B", "S1"),
        _make_sample_record("B", "S2"),
    ]
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(EVAL_SCRIPT), "--rater-a", str(file_a), "--rater-b", str(file_b)],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert ("không khớp với annotator kỳ vọng 'A'" in proc.stderr or "nhiều annotator_id khác nhau" in proc.stderr)


def test_evaluate_kappa_strict_pass_id_validation(tmp_path):
    """Lead D probe 3: pass_id thiếu, kiểu bool, kiểu str, kiểu float, hoặc sai lượt."""
    file_a = tmp_path / "rater_a.jsonl"
    file_b = tmp_path / "rater_b.jsonl"
    recs_b = [_make_sample_record("B", "S1")]
    file_b.write_text("\n".join(json.dumps(r) for r in recs_b) + "\n", encoding="utf-8")

    # 1. Thiếu pass_id
    recs_a = [_make_sample_record("A", "S1")]
    del recs_a[0]["pass_id"]
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(EVAL_SCRIPT), "--rater-a", str(file_a), "--rater-b", str(file_b)],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "thiếu trường bắt buộc 'pass_id'" in proc.stderr

    # 2. pass_id là bool (True)
    recs_a = [_make_sample_record("A", "S1", pass_id=True)]
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(EVAL_SCRIPT), "--rater-a", str(file_a), "--rater-b", str(file_b)],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "sai kiểu dữ liệu (bool: True)" in proc.stderr

    # 3. pass_id là string ("1")
    recs_a = [_make_sample_record("A", "S1", pass_id="1")]
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(EVAL_SCRIPT), "--rater-a", str(file_a), "--rater-b", str(file_b)],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "sai kiểu dữ liệu (str: '1')" in proc.stderr

    # 4. pass_id là float (1.0)
    recs_a = [_make_sample_record("A", "S1", pass_id=1.0)]
    file_a.write_text("\n".join(json.dumps(r) for r in recs_a) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(EVAL_SCRIPT), "--rater-a", str(file_a), "--rater-b", str(file_b)],
        capture_output=True, text=True, encoding="utf-8", cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 2
    assert "sai kiểu dữ liệu (float: 1.0)" in proc.stderr
