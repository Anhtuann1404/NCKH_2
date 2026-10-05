"""Regressions for L-B01..06 and real-pilot content/group exclusion."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from phishing.annotation import compute_cohens_kappa, export_blind_view, extract_safe_view_content
from phishing.data.exclusion import ExclusionRegistry

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("annotate_cli", ROOT / "scripts/annotate_cli.py")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


def test_pagination_advances_and_full_text(monkeypatch, capsys):
    replies = iter(["m", "m", "v"])
    monkeypatch.setattr("builtins.input", lambda _: next(replies))
    text = "A" * 600 + "B" * 600 + "C" * 600 + "D" * 50
    cli.display_sample_and_allow_reading({"sample_id": "S01", "page_text": text}, 1, 1)
    output = capsys.readouterr().out
    assert "B" * 600 in output and "C" * 600 in output and text in output


def test_resume_rejects_non_object_duplicate_and_wrong_mode(tmp_path):
    record = {"sample_id": "S01", "annotator_id": "A", "pass_id": 1, "is_dry_run": False}
    path = tmp_path / "labels.jsonl"
    for rows in ([[]], [record, record], [dict(record, annotator_id="simulated_A", is_dry_run=False)]):
        path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
        with pytest.raises(ValueError):
            cli.load_already_annotated_sample_ids(path, "simulated_A" if len(rows) == 1 and isinstance(rows[0], dict) else "A", 1, len(rows) == 1 and isinstance(rows[0], dict))


def test_cli_reads_metadata_and_rejects_string_boolean(tmp_path):
    input_path, output = tmp_path / "view.json", tmp_path / "out.jsonl"
    data = export_blind_view([{"sample_id": "S01", "url": "https://site.invalid/", "text": "Text", "random_subset": False, "codebook_version": "review-v2"}], input_path)
    cli.annotate_interactive_session("A", input_path, output, dry_run=True)
    record = json.loads((tmp_path / "out.dryrun.jsonl").read_text())
    assert record["codebook_version"] == "review-v2" and record["random_subset"] is False
    data["samples"][0]["random_subset"] = "false"
    input_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="boolean"):
        cli.annotate_interactive_session("A", input_path, tmp_path / "other.jsonl", dry_run=True)


def test_kappa_keeps_random_difficult_and_uses_requested_label():
    a = [{"class_label": "benign", "primary_org": "google", "random_subset": True, "difficult_case": True},
         {"class_label": "benign", "primary_org": "meta", "random_subset": False}]
    b = [dict(a[0], primary_org="microsoft"), dict(a[1])]
    result = compute_cohens_kappa(a, b, is_difficult=[True, False], label_field="primary_org", require_provenance=False)
    assert result.sample_count == 1 and result.observed_agreement == 0
    with pytest.raises(ValueError, match="random_subset"):
        compute_cohens_kappa(["x"], ["y"], is_difficult=[True], require_provenance=False)


def test_offline_html_limit_is_explicit():
    html = "<p>" + "x" * 1_000_001 + "</p><script>bad()</script>"
    with pytest.raises(ValueError, match="limit"):
        extract_safe_view_content(html, "https://site.invalid/")
    text, _ = extract_safe_view_content(html, "https://site.invalid/", max_html_characters=2_000_000)
    assert "bad()" not in text and len(text) == 1_000_001


def test_exclusion_hashes_and_domain_do_not_exclude_unrelated_records(tmp_path):
    digest = lambda s: hashlib.sha256(s.encode()).hexdigest()
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps({"exclusions": [{"samples": [{"url_sha256": digest("https://example.com/old"), "html_sha256": digest("copied"), "group_sha256": digest("example.com")}]}]}), encoding="utf-8")
    registry = ExclusionRegistry(registry_path)
    assert registry.is_excluded({"url": "https://example.com/new", "html": "different"})
    assert registry.is_excluded({"url": "https://example.net/", "html": "copied"})
    assert not registry.is_excluded({"url": "https://example.net/", "html": "other"})


def test_real_pilot_pending_review_cannot_create_human_labels(tmp_path):
    input_path = tmp_path / "pending.json"
    export_blind_view([], input_path, dataset_type="real_pilot_pending_review")
    output = tmp_path / "A.jsonl"
    with pytest.raises(ValueError, match="nghiệm thu"):
        cli.annotate_interactive_session("A", input_path, output)
    assert not output.exists()


def test_real_pilot_ready_allows_session_init(tmp_path, capsys):
    input_path = tmp_path / "ready.json"
    dataset_id = "REAL-PILOT-READY-01"
    sp_ver = "PILOT-PLAN-V1-FULL-OVERLAP"
    export_blind_view(
        [],
        input_path,
        dataset_id=dataset_id,
        dataset_type="real_pilot_ready",
        sampling_plan_version=sp_ver,
    )
    output = tmp_path / "A.jsonl"
    manifest_path = tmp_path / "mock_manifest.json"
    view_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
    cb_path = tmp_path / "MOCK_CB.md"
    cb_path.write_text(
        "# SỔ TAY QUY TẮC GÁN NHÃN\n\n"
        "**Phiên bản:** `v1.0.0`\n"
        "**Trạng thái:** `locked`\n"
        + "Quy tắc gán nhãn chuẩn hóa cho dự án NCKH_2. " * 10,
        encoding="utf-8",
    )
    dict_path = tmp_path / "mock_dict.json"
    dict_path.write_text(
        json.dumps({
            "dictionary_id": "org_dictionary_v1",
            "version": "1.0.0",
            "status": "locked",
            "organizations": [{"name": f"Org_{i}"} for i in range(14)],
        }),
        encoding="utf-8",
    )
    cb_hash = hashlib.sha256(cb_path.read_bytes()).hexdigest()
    dict_hash = hashlib.sha256(dict_path.read_bytes()).hexdigest()

    manifest_path.write_text(json.dumps({
        "dataset_id": dataset_id,
        "sample_count": 0,
        "sampling_plan_version": sp_ver,
        "codebook_version": "1.0.0",
        "codebook_status": "locked",
        "dictionary_version": "1.0.0",
        "dictionary_status": "locked",
        "acceptance": {"B": "approved", "D": "approved"},
        "ready_for_annotation": True,
        "blind_view_sha256": view_hash,
        "codebook_sha256": cb_hash,
        "dictionary_sha256": dict_hash,
    }), encoding="utf-8")

    # 1. Gói rỗng hoặc sample_count <= 0 bị từ chối
    with pytest.raises(ValueError, match="sample_count"):
        cli.annotate_interactive_session("A", input_path, output, manifest_path=manifest_path, dry_run=True, codebook_path=cb_path, dictionary_path=dict_path)

    # 2. Gói có mẫu hợp lệ và đã hoàn thành toàn bộ
    samples = [{"sample_id": "SMP-01", "url": "https://test.invalid/", "html": "<p>Content</p>"}]
    export_blind_view(
        samples,
        input_path,
        dataset_id=dataset_id,
        dataset_type="real_pilot_ready",
        sampling_plan_version=sp_ver,
    )
    view_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps({
        "dataset_id": dataset_id,
        "sample_count": 1,
        "sampling_plan_version": sp_ver,
        "codebook_version": "1.0.0",
        "codebook_status": "locked",
        "dictionary_version": "1.0.0",
        "dictionary_status": "locked",
        "acceptance": {"B": "approved", "D": "approved"},
        "ready_for_annotation": True,
        "blind_view_sha256": view_hash,
        "codebook_sha256": cb_hash,
        "dictionary_sha256": dict_hash,
    }), encoding="utf-8")

    from phishing.annotation.blind_view import compute_sample_content_hash
    content_hash = compute_sample_content_hash(json.loads(input_path.read_text(encoding="utf-8"))["samples"][0])
    output.write_text(json.dumps({
        "annotator_id": "A",
        "sample_id": "SMP-01",
        "pass_id": 1,
        "is_dry_run": False,
        "dataset_id": dataset_id,
        "dataset_hash": view_hash,
        "codebook_version": "1.0.0",
        "codebook_hash": cb_hash,
        "sampling_plan_version": sp_ver,
        "sample_content_hash": content_hash,
    }) + "\n", encoding="utf-8")

    cli.annotate_interactive_session("A", input_path, output, manifest_path=manifest_path, dry_run=False, codebook_path=cb_path, dictionary_path=dict_path)
    out = capsys.readouterr().out
    assert "hoàn thành toàn bộ các mẫu" in out


def test_real_pilot_builder_rejects_changed_original_bytes(tmp_path):
    spec = importlib.util.spec_from_file_location("build_real_pilot", ROOT / "scripts/data/build_real_pilot.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    technical = tmp_path / "changed.json"
    technical.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        builder.build(technical, tmp_path / "missing.parquet")
