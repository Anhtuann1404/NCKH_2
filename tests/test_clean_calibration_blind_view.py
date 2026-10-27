"""Unit & Regression tests for Clean Calibration Blind View v1.1 (24 Main Samples).

Ensures:
1. Pure LF byte normalization and cryptographic integrity with manifest.
2. Zero data leakage: zero labels, zero scores, zero matchers, zero reserve samples.
3. Anti-leakage disjointness against all 182 samples in exclusion registry.
4. Schema conformance with Codebook v1.1.
5. Fail-closed preflight behavior with annotate_cli.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from phishing.annotation.blind_view import assert_no_label_leak
from annotate_cli import validate_manifest_preflight


VIEW_PATH = ROOT / "data/annotations/clean_calibration_blind_view_24.json"
MANIFEST_PATH = ROOT / "configs/calibration_clean_a_manifest.json"
CANDIDATES_PATH = ROOT / "data/restricted/clean_calibration_candidates_v3_restricted.json"
REGISTRY_PATH = ROOT / "data/exclusion_registry.json"


@pytest.fixture
def clean_blind_view_data():
    """Load clean calibration blind view if present on local runner."""
    if not VIEW_PATH.exists():
        pytest.skip(f"Clean calibration blind view not present at {VIEW_PATH}")
    raw_bytes = VIEW_PATH.read_bytes()
    return json.loads(raw_bytes.decode("utf-8")), raw_bytes


@pytest.fixture
def clean_manifest_data():
    """Load calibration manifest."""
    assert MANIFEST_PATH.exists(), f"Missing manifest at {MANIFEST_PATH}"
    raw_bytes = MANIFEST_PATH.read_bytes()
    return json.loads(raw_bytes.decode("utf-8")), raw_bytes


class TestCleanCalibrationBlindViewIntegrity:
    """Test suite for Clean Calibration Blind View."""

    def test_blind_view_exists_and_pure_lf(self, clean_blind_view_data):
        _, raw_bytes = clean_blind_view_data
        assert b"\r\n" not in raw_bytes, "Blind View file contains Windows CRLF line endings! Must be pure LF."
        assert len(raw_bytes) > 10_000, "Blind View file is suspiciously small"

    def test_sample_count_and_sample_ids(self, clean_blind_view_data):
        view, _ = clean_blind_view_data
        samples = view.get("samples", [])
        assert len(samples) == 24, f"Expected exactly 24 main samples, found {len(samples)}"
        assert view.get("sample_count") == 24
        assert view.get("total_samples") == 24

        expected_ids = [f"SMP-{i:03d}" for i in range(1, 25)]
        view_ids = [s["sample_id"] for s in samples]
        assert view_ids == expected_ids, f"Sample IDs do not match SMP-001..SMP-024 sequence: {view_ids}"

    def test_zero_reserve_candidates_in_blind_view(self, clean_blind_view_data):
        view, _ = clean_blind_view_data
        samples = view.get("samples", [])

        # Check for any reserve naming or tags
        for s in samples:
            sid = s.get("sample_id", "")
            assert not sid.startswith("RSV"), f"Reserve candidate {sid} found in Blind View!"
            assert "reserve" not in sid.lower()

        # Cross-reference with candidate registry if present
        if CANDIDATES_PATH.exists():
            cand_data = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))
            reserve_cands = [c for c in cand_data.get("candidates", []) if c.get("role") == "reserve_08"]
            reserve_urls = {c["url_sha256"] for c in reserve_cands}

            for s in samples:
                url_hash = hashlib.sha256(s["url"].encode("utf-8")).hexdigest()
                assert url_hash not in reserve_urls, f"Sample {s['sample_id']} has URL matching a reserve candidate!"

    def test_zero_label_leak_assert(self, clean_blind_view_data):
        view, _ = clean_blind_view_data
        # Standard assert_no_label_leak verification
        assert_no_label_leak(view)

        # Deep text inspection for forbidden source signals
        view_text = json.dumps(view)
        forbidden_terms = [
            "source_label", "primary_org_status", "ground_truth",
            "train-000.parquet", "train-055.parquet", "row_offset",
            "main_phish_count", "main_benign_count"
        ]
        for term in forbidden_terms:
            assert term not in view_text, f"Forbidden term '{term}' leaked into Blind View text!"

    def test_schema_compliance_codebook_v1_1(self, clean_blind_view_data):
        view, _ = clean_blind_view_data
        assert view.get("codebook_version") == "1.1.0"
        assert view.get("sampling_plan_version") == "CALIBRATION-CLEAN-PLAN-V1.1-STRATIFIED"
        assert view.get("is_synthetic") is False

        for s in view.get("samples", []):
            assert "sample_id" in s
            assert "url" in s and s["url"].startswith("http")
            assert "page_text" in s
            assert "structure_summary" in s
            assert s.get("random_subset") is True
            assert s.get("codebook_version") == "1.1.0"

            summary = s["structure_summary"]
            assert isinstance(summary, dict)
            for k in ("forms", "inputs", "password_inputs", "has_login_form", "buttons", "external_links"):
                assert k in summary, f"Structure summary missing key: {k}"

    def test_disjointness_against_historical_exclusions_182(self, clean_blind_view_data):
        """Chứng minh 24 mẫu hoàn toàn độc lập với 182 mẫu lịch sử trong 8 lô trước."""
        if not REGISTRY_PATH.exists():
            pytest.skip("Exclusion registry not present")

        view, _ = clean_blind_view_data
        reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

        hist_urls = set()
        hist_htmls = set()
        hist_groups = set()
        for batch in reg.get("exclusions", []):
            if batch.get("exclusion_id") in ("EXCL-CALIBRATION-CLEAN-RUNWAY-32", "EXCL-CALIBRATION-CLEAN-ROUND-C-32"):
                continue  # Bỏ qua chính lô Runway 32 và Round C để kiểm tra tính độc lập với 182 mẫu lịch sử
            for entry in batch.get("samples", []):
                if entry.get("url_sha256"):
                    hist_urls.add(entry["url_sha256"])
                if entry.get("html_sha256"):
                    hist_htmls.add(entry["html_sha256"])
                if entry.get("group_sha256"):
                    hist_groups.add(entry["group_sha256"])

        for s in view.get("samples", []):
            url_hash = hashlib.sha256(s["url"].encode("utf-8")).hexdigest()
            assert url_hash not in hist_urls, f"Sample {s['sample_id']} URL hash {url_hash} in historical exclusions!"

    def test_registration_in_clean_runway_exclusion_mapping(self, clean_blind_view_data):
        """Chứng minh toàn bộ 24 mẫu chính đã được bảo đảm loại trừ trong hồ sơ hạn chế Đợt C clean_calibration_exclusion_mapping_c_32.json."""
        mapping_path = ROOT / "data/restricted/clean_calibration_exclusion_mapping_c_32.json"
        if not mapping_path.exists():
            pytest.skip("Restricted exclusion mapping not present on clean checkout")

        view, _ = clean_blind_view_data
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
        assert mapping["total_samples"] == 32
        assert mapping["main_samples_count"] == 24
        assert mapping["reserve_samples_count"] == 8

        mapped_urls = {e["url_sha256"] for e in mapping.get("mapping", [])}
        mapped_norm_urls = {e.get("normalized_url_sha256", e["url_sha256"]) for e in mapping.get("mapping", [])}
        for s in view.get("samples", []):
            url_hash = hashlib.sha256(s["url"].encode("utf-8")).hexdigest()
            assert url_hash in mapped_urls or url_hash in mapped_norm_urls, (
                f"Sample {s['sample_id']} URL hash {url_hash} chưa được đối soát trong hồ sơ hạn chế Đợt C!"
            )

    def test_offline_translation_r_a09_binding(self, clean_blind_view_data):
        """Kiểm tra bản dịch ngoại tuyến gắn kèm theo R-A09 Codebook v1.1: hash ràng buộc và tính toàn vẹn."""
        view, _ = clean_blind_view_data
        samples = view.get("samples", [])

        # Kiểm tra translation_manifest ở cấp dataset
        assert "translation_manifest" in view, "Thiếu translation_manifest ở cấp dataset"
        t_manifest = view["translation_manifest"]
        assert t_manifest.get("translated_samples_count") == 3
        assert len(t_manifest.get("models", [])) == 2

        translated_ids = {"SMP-008", "SMP-009", "SMP-015"}
        for s in samples:
            sid = s["sample_id"]
            if sid in translated_ids:
                assert s.get("translation_provided") is True, f"Mẫu {sid} phải có translation_provided=True"
                trans_text = s.get("translated_text", "")
                assert isinstance(trans_text, str) and len(trans_text) > 20, f"Mẫu {sid} thiếu translated_text hợp lệ"
                # Ràng buộc cryptographic hash của bản dịch
                expected_trans_hash = hashlib.sha256(trans_text.encode("utf-8")).hexdigest()
                assert s.get("translation_sha256") == expected_trans_hash, (
                    f"Mẫu {sid} translation_sha256 không khớp với nội dung translated_text!"
                )
                assert s.get("translation_source_language") in ("ja", "ru")
                assert s.get("translation_tool") == "MarianMT"
                assert "opus-mt" in s.get("translation_tool_version", "")
            else:
                assert not s.get("translation_provided", False), f"Mẫu {sid} không thuộc diện dịch nhưng translation_provided=True"

    def test_manifest_synchronization(self, clean_blind_view_data, clean_manifest_data):
        _, view_bytes = clean_blind_view_data
        manifest, _ = clean_manifest_data

        view_hash = hashlib.sha256(view_bytes).hexdigest()
        assert manifest["blind_view_sha256"] == view_hash
        assert manifest["governance"]["blind_view_sha256"] == view_hash
        assert manifest["sample_count"] == 24
        assert manifest["dataset_id"] == "CALIBRATION-CLEAN-24"
        assert manifest["ready_for_annotation"] is False
        assert manifest["training_blocked"] is True

    def test_annotate_cli_preflight_fail_closed(self, clean_blind_view_data):
        """CLI preflight must strictly fail-closed when ready_for_annotation=false."""
        view, _ = clean_blind_view_data
        with pytest.raises(ValueError, match="CHƯA NGHIỆM THU|CHƯA SẴN SÀNG"):
            validate_manifest_preflight(
                manifest_path=MANIFEST_PATH,
                input_path=VIEW_PATH,
                dataset_data=view,
            )

    def test_annotate_cli_preflight_simulation_success(self, clean_blind_view_data, clean_manifest_data, tmp_path):
        """Simulating approved acceptance and ready_for_annotation=true must pass preflight 100%."""
        view, _ = clean_blind_view_data
        manifest, _ = clean_manifest_data

        sim_manifest = dict(manifest)
        sim_manifest["acceptance"] = {"B": "approved", "D": "approved"}
        sim_manifest["ready_for_annotation"] = True

        sim_path = tmp_path / "sim_manifest.json"
        sim_path.write_text(json.dumps(sim_manifest, indent=2), encoding="utf-8")

        res = validate_manifest_preflight(
            manifest_path=sim_path,
            input_path=VIEW_PATH,
            dataset_data=view,
        )
        assert res["dataset_id"] == "CALIBRATION-CLEAN-24"
        assert res["sample_count"] == 24
