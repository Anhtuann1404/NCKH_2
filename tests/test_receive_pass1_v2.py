"""Intake keeps original bytes and rejects a wrong or simulated Pass 1 file."""

import hashlib
import json

from scripts.data import receive_pass1_v2 as intake
from phishing.annotation.blind_view import compute_sample_content_hash


def _fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(intake, "ROOT", tmp_path)
    monkeypatch.setattr(intake, "REGISTRY", tmp_path / "registry.json")
    samples = [
        {"sample_id": f"PILOT-{i:03d}", "url": f"https://example{i}.test/",
         "page_text": "sample", "structure_summary": {}, "random_subset": True,
         "codebook_version": "1.0.0"}
        for i in range(1, 33)
    ]
    view = {"dataset_id": "REAL-PILOT-32-V2", "is_synthetic": False, "samples": samples}
    (tmp_path / "view.json").write_text(json.dumps(view), encoding="utf-8")
    (tmp_path / "registry.json").write_text('{"training_blocked": true}', encoding="utf-8")
    manifest = {
        "dataset_id": "REAL-PILOT-32-V2", "status": "approved", "sample_count": 32,
        "source_verification_status": "verified_pinned_train_rows",
        "exposure_review": {"A": "approved", "B": "approved", "D": "approved"},
        "ready_for_annotation": True, "acceptance": {"B": "approved", "D": "approved"},
        "blind_view_path": "view.json", "blind_view_sha256": intake.sha256(tmp_path / "view.json"),
        "codebook_version": "1.0.0", "codebook_sha256": "codebook-hash",
        "sampling_plan_version": "PILOT-PLAN-V2-FULL-OVERLAP",
        "exclusion_registry_sha256": intake.sha256(tmp_path / "registry.json"),
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    records = []
    for sample in samples:
        records.append({
            "annotator_id": "A", "sample_id": sample["sample_id"], "pass_id": 1,
            "class_label": "phishing", "primary_org_status": "identified",
            "catalog_status": "in_catalog", "observed_service": "Office 365",
            "org_targets": ["microsoft"], "primary_org": "microsoft",
            "identity_role": "identity_claim", "domain_role": "unverified",
            "evidence_note": "test", "seconds_spent": 30.0, "random_subset": True,
            "difficult_case": False, "is_dry_run": False, "is_synthetic": False,
            "dataset_id": manifest["dataset_id"], "dataset_hash": manifest["blind_view_sha256"],
            "codebook_version": manifest["codebook_version"],
            "codebook_hash": manifest["codebook_sha256"],
            "sampling_plan_version": manifest["sampling_plan_version"],
            "sample_content_hash": compute_sample_content_hash(sample),
        })
    return manifest_path, records


def test_receive_accepts_one_file_and_preserves_bytes(tmp_path, monkeypatch):
    manifest, records = _fixture(tmp_path, monkeypatch)
    source = tmp_path / "A.jsonl"
    raw = ("\n".join(json.dumps(r) for r in records) + "\n").encode()
    source.write_bytes(raw)
    receipt = intake.receive(source, "A", tmp_path / "inbox", manifest)
    assert receipt["status"] == "accepted"
    assert receipt["file_sha256"] == hashlib.sha256(raw).hexdigest()
    assert (tmp_path / "inbox/A" / f"{receipt['file_sha256']}.jsonl").read_bytes() == raw
    assert intake.receive(source, "A", tmp_path / "inbox", manifest)["status"] == "accepted"


def test_receive_preserves_rejected_file_without_replacing_accepted(tmp_path, monkeypatch):
    manifest, records = _fixture(tmp_path, monkeypatch)
    source = tmp_path / "A.jsonl"
    source.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    accepted = intake.receive(source, "A", tmp_path / "inbox", manifest)
    records[0]["is_dry_run"] = True
    source.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    rejected = intake.receive(source, "A", tmp_path / "inbox", manifest)
    assert rejected["status"] == "rejected"
    assert "dry-run" in rejected["reason"]
    assert rejected["file_sha256"] != accepted["file_sha256"]
    assert (tmp_path / "inbox/A" / f"{accepted['file_sha256']}.jsonl").is_file()
    assert (tmp_path / "inbox/A" / f"{rejected['file_sha256']}.jsonl").is_file()


def test_receive_replacement_rater_keeps_distinct_identity(tmp_path, monkeypatch):
    manifest, records = _fixture(tmp_path, monkeypatch)
    for annotator in ("D", "E"):
        for record in records:
            record["annotator_id"] = annotator
        source = tmp_path / f"{annotator}.jsonl"
        source.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        receipt = intake.receive(source, annotator, tmp_path / "inbox", manifest)
        assert receipt["status"] == "accepted"
        assert (tmp_path / "inbox" / annotator / f"{receipt['file_sha256']}.jsonl").is_file()
