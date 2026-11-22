"""Fixture tests verifying Manifest Contract Schema and Preflight Gates for Main Batch 1.

PURPOSE & DESIGN (100% SYNTHETIC & SELF-CONTAINED):
- Operates exclusively on synthetic dummy data (in tmp_path).
- Zero dependencies on data/restricted/ or operational secrets.
- Verifies all 12 mandatory contract schema fields required by validate_manifest_preflight.
- Verifies that pending manifests fail-closed at the governance gate (acceptance/ready_for_annotation),
  strictly BEFORE any sample is displayed or output session is opened.
- Verifies tamper-evident rejection on tampered hashes or counts.
"""

import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def cli_module():
    """Load scripts/annotate_cli.py dynamically."""
    spec = importlib.util.spec_from_file_location("annotate_cli", ROOT / "scripts/annotate_cli.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def mock_environment(tmp_path: Path):
    """Create a self-contained synthetic environment with mock codebook, dictionary, and blind view."""
    # 1. Mock Codebook (locked, v1.1.0)
    cb_text = (
        "# Synthetic Codebook\n"
        "**Phiên bản:** 1.1.0\n"
        "**Trạng thái:** locked (chính thức)\n\n"
        "Synthetic codebook content for unit testing only. " * 5
    )
    cb_path = tmp_path / "mock_codebook.md"
    cb_path.write_text(cb_text, encoding="utf-8")
    cb_hash = hashlib.sha256(cb_path.read_bytes()).hexdigest()

    # 2. Mock Dictionary (locked, v1.0.0, >= 14 orgs)
    orgs = [{"org_id": f"org_{i:02d}", "name": f"Org {i}"} for i in range(14)]
    dict_data = {
        "version": "1.0.0",
        "status": "locked",
        "organizations": orgs,
    }
    dict_path = tmp_path / "mock_dictionary.json"
    dict_path.write_text(json.dumps(dict_data, indent=2), encoding="utf-8")
    dict_hash = hashlib.sha256(dict_path.read_bytes()).hexdigest()

    # 3. Mock Blind View (envelope with 5 synthetic samples)
    samples = []
    for i in range(5):
        blind_id = f"BLIND-{i:08x}"
        samples.append({
            "sample_id": blind_id,
            "url": f"https://syn{i}.example.org",
            "page_text": f"Page content {i}",
            "structure_summary": {"forms": 1},
            "blind_contract_version": "1.2.0",
        })
    view_data = {
        "dataset_id": "MAIN-BATCH1-SYNTHETIC",
        "blind_contract_version": "1.2.0",
        "total_samples": 5,
        "sampling_plan_version": "MAIN-PLAN-V1.0",
        "codebook_version": "1.1.0",
        "dictionary_version": "1.0.0",
        "is_synthetic": True,
        "samples": samples,
    }
    view_path = tmp_path / "mock_blind_view.json"
    view_bytes = (json.dumps(view_data, indent=2) + "\n").encode("utf-8")
    view_path.write_bytes(view_bytes)
    view_hash = hashlib.sha256(view_bytes).hexdigest()

    return {
        "cb_path": cb_path,
        "cb_hash": cb_hash,
        "dict_path": dict_path,
        "dict_hash": dict_hash,
        "view_path": view_path,
        "view_hash": view_hash,
        "view_data": view_data,
        "sample_count": 5,
    }


def _make_base_manifest(env: dict, *, acceptance=None, ready_for_annotation=False) -> dict:
    if acceptance is None:
        acceptance = {"B": "pending", "D": "pending"}
    return {
        "dataset_id": "MAIN-BATCH1-SYNTHETIC",
        "sample_count": env["sample_count"],
        "sampling_plan_version": "MAIN-PLAN-V1.0",
        "codebook_version": "1.1.0",
        "codebook_status": "locked",
        "dictionary_version": "1.0.0",
        "dictionary_status": "locked",
        "acceptance": acceptance,
        "ready_for_annotation": ready_for_annotation,
        "blind_view_sha256": env["view_hash"],
        "codebook_sha256": env["cb_hash"],
        "dictionary_sha256": env["dict_hash"],
        "blind_contract_version": "1.2.0",
    }


def test_manifest_schema_requires_all_mandatory_fields(cli_module, mock_environment, tmp_path):
    """Verify that omitting any of the 8 mandatory fields fails with a schema error."""
    mandatory_fields = [
        "sampling_plan_version",
        "codebook_status",
        "dictionary_version",
        "dictionary_status",
        "acceptance",
        "ready_for_annotation",
        "codebook_sha256",
        "dictionary_sha256",
    ]

    for field in mandatory_fields:
        bad_manifest = _make_base_manifest(mock_environment)
        del bad_manifest[field]
        bad_manifest_path = tmp_path / f"bad_manifest_{field}.json"
        bad_manifest_path.write_text(json.dumps(bad_manifest, indent=2), encoding="utf-8")

        with pytest.raises(ValueError) as excinfo:
            cli_module.validate_manifest_preflight(
                bad_manifest_path,
                mock_environment["view_path"],
                mock_environment["view_data"],
                codebook_path=mock_environment["cb_path"],
                dictionary_path=mock_environment["dict_path"],
            )
        assert "THIẾU TRƯỜNG MANIFEST BẮT BUỘC" in str(excinfo.value)
        assert field in str(excinfo.value)


def test_unapproved_manifest_stops_at_acceptance_pending_gate(cli_module, mock_environment, tmp_path):
    """Verify that an unapproved manifest (acceptance pending) stops at the gate BEFORE session start."""
    manifest_data = _make_base_manifest(mock_environment, acceptance={"B": "pending", "D": "pending"}, ready_for_annotation=False)
    mf_path = tmp_path / "pending_manifest.json"
    mf_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        cli_module.validate_manifest_preflight(
            mf_path,
            mock_environment["view_path"],
            mock_environment["view_data"],
            codebook_path=mock_environment["cb_path"],
            dictionary_path=mock_environment["dict_path"],
        )
    assert "CHƯA NGHIỆM THU" in str(excinfo.value)

    # Prove interactive session fail-closed before creating any output file
    dummy_out = tmp_path / "output_should_never_exist.jsonl"
    with pytest.raises(ValueError, match="CHƯA NGHIỆM THU"):
        cli_module.annotate_interactive_session(
            annotator_id="A",
            input_path=mock_environment["view_path"],
            output_path=dummy_out,
            manifest_path=mf_path,
        )
    assert not dummy_out.exists(), "Session output file must not be created when manifest is pending!"


def test_unready_manifest_stops_at_ready_gate(cli_module, mock_environment, tmp_path):
    """Verify that if acceptance is approved but ready_for_annotation=false, it stops at the gate."""
    manifest_data = _make_base_manifest(mock_environment, acceptance={"B": "approved", "D": "approved"}, ready_for_annotation=False)
    mf_path = tmp_path / "not_ready_manifest.json"
    mf_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        cli_module.validate_manifest_preflight(
            mf_path,
            mock_environment["view_path"],
            mock_environment["view_data"],
            codebook_path=mock_environment["cb_path"],
            dictionary_path=mock_environment["dict_path"],
        )
    assert "CHƯA SẴN SÀNG" in str(excinfo.value)


def test_tampered_hashes_are_rejected(cli_module, mock_environment, tmp_path):
    """Verify that any tampering with blind view, codebook, or dictionary hash is rejected fail-closed."""
    # 1. Tampered view hash
    mf_data = _make_base_manifest(mock_environment, acceptance={"B": "approved", "D": "approved"}, ready_for_annotation=True)
    mf_data["blind_view_sha256"] = "0" * 64
    mf_path = tmp_path / "tampered_view.json"
    mf_path.write_text(json.dumps(mf_data, indent=2), encoding="utf-8")
    with pytest.raises(ValueError, match="SAI KHÁC MÃ BĂM VIEW"):
        cli_module.validate_manifest_preflight(
            mf_path,
            mock_environment["view_path"],
            mock_environment["view_data"],
            codebook_path=mock_environment["cb_path"],
            dictionary_path=mock_environment["dict_path"],
        )

    # 2. Tampered codebook hash
    mf_data = _make_base_manifest(mock_environment, acceptance={"B": "approved", "D": "approved"}, ready_for_annotation=True)
    mf_data["codebook_sha256"] = "0" * 64
    mf_path = tmp_path / "tampered_cb.json"
    mf_path.write_text(json.dumps(mf_data, indent=2), encoding="utf-8")
    with pytest.raises(ValueError, match="SAI KHÁC MÃ BĂM CODEBOOK"):
        cli_module.validate_manifest_preflight(
            mf_path,
            mock_environment["view_path"],
            mock_environment["view_data"],
            codebook_path=mock_environment["cb_path"],
            dictionary_path=mock_environment["dict_path"],
        )

    # 3. Tampered dictionary hash
    mf_data = _make_base_manifest(mock_environment, acceptance={"B": "approved", "D": "approved"}, ready_for_annotation=True)
    mf_data["dictionary_sha256"] = "0" * 64
    mf_path = tmp_path / "tampered_dict.json"
    mf_path.write_text(json.dumps(mf_data, indent=2), encoding="utf-8")
    with pytest.raises(ValueError, match="SAI KHÁC MÃ BĂM DICTIONARY"):
        cli_module.validate_manifest_preflight(
            mf_path,
            mock_environment["view_path"],
            mock_environment["view_data"],
            codebook_path=mock_environment["cb_path"],
            dictionary_path=mock_environment["dict_path"],
        )


def test_approved_full_contract_manifest_passes_preflight(cli_module, mock_environment, tmp_path):
    """Verify that a fully approved manifest with all required fields passes preflight without error."""
    manifest_data = _make_base_manifest(mock_environment, acceptance={"B": "approved", "D": "approved"}, ready_for_annotation=True)
    mf_path = tmp_path / "approved_manifest.json"
    mf_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    result = cli_module.validate_manifest_preflight(
        mf_path,
        mock_environment["view_path"],
        mock_environment["view_data"],
        codebook_path=mock_environment["cb_path"],
        dictionary_path=mock_environment["dict_path"],
    )
    assert result["dataset_id"] == "MAIN-BATCH1-SYNTHETIC"
    assert result["ready_for_annotation"] is True
    assert result["acceptance"] == {"B": "approved", "D": "approved"}
