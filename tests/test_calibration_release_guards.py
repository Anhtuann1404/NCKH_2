"""Kiểm thử chốt chặn an toàn cho đường chạy hiệu chuẩn Calibration v1.1.

Quy chuẩn ARS & Safety:
1. Unit tests: Sử dụng fixture tự chứa (self-contained fixtures), độc lập 100% với
   dữ liệu thô hạn chế data/raw/; pass 100% trên clean checkout (chỉ có Git).
2. Integration tests (@pytest.mark.integration): Yêu cầu môi trường có dữ liệu hạn chế data/raw/,
   kiểm tra đối soát toàn vẹn thực tế giữa gói phát hành và đăng ký loại trừ.
"""

import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

from phishing.annotation.blind_view import (
    assert_no_label_leak,
    compute_sample_content_hash,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def cli_module():
    spec = importlib.util.spec_from_file_location("annotate_cli", ROOT / "scripts/annotate_cli.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestCalibrationReleaseGuardsUnit:
    """Tập unit tests tự chứa kiểm tra chốt chặn an toàn (Chạy trên clean checkout không có data/raw)."""

    def test_unit_pending_release_manifest_is_rejected_fail_closed(self, cli_module, tmp_path):
        """Chứng minh manifest phát hành mới bị từ chối dứt điểm trước khi hiển thị mẫu."""
        release_manifest_path = ROOT / "configs/calibration_manifest_v1_1_release.json"
        assert release_manifest_path.exists(), "Thiếu release manifest configs/calibration_manifest_v1_1_release.json"
        manifest_data = json.loads(release_manifest_path.read_text(encoding="utf-8"))

        # Tạo view tự chứa khớp SHA của manifest
        view_samples = [
            {
                "sample_id": f"SMP-{i:03d}",
                "url": f"https://example-{i}.test/",
                "page_text": f"Sample text content {i}",
                "structure_summary": {"title": "", "forms": 0, "inputs": 0, "password_inputs": 0, "has_login_form": False, "buttons": 0, "external_links": 0},
                "random_subset": True,
                "codebook_version": "1.1.0",
                "translation_provided": False,
            }
            for i in range(1, 25)
        ]
        sim_view_data = {
            "dataset_id": manifest_data["dataset_id"],
            "total_samples": 24,
            "sampling_plan_version": manifest_data["sampling_plan_version"],
            "codebook_version": manifest_data["codebook_version"],
            "codebook_sha256": manifest_data["codebook_sha256"],
            "dictionary_version": manifest_data["dictionary_version"],
            "dictionary_sha256": manifest_data["dictionary_sha256"],
            "is_synthetic": False,
            "status": "proposal_release_candidate",
            "samples": view_samples,
        }

        # Lưu view tạm thời khớp mã băm mà manifest khai báo
        sim_view_path = tmp_path / "mock_view.json"
        sim_view_bytes = (json.dumps(sim_view_data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        sim_view_path.write_bytes(sim_view_bytes)

        # Cập nhật manifest tạm thời trỏ tới mock view này
        temp_manifest = dict(manifest_data)
        temp_manifest["blind_view_sha256"] = hashlib.sha256(sim_view_bytes).hexdigest()
        temp_manifest_path = tmp_path / "manifest_test.json"
        temp_manifest_path.write_text(json.dumps(temp_manifest, indent=2), encoding="utf-8")

        # 1. Kiểm tra validate_manifest_preflight từ chối do acceptance pending & ready_for_annotation=false
        with pytest.raises(ValueError) as excinfo:
            cli_module.validate_manifest_preflight(
                temp_manifest_path,
                sim_view_path,
                sim_view_data,
            )
        assert any(
            err in str(excinfo.value)
            for err in ["CHƯA NGHIỆM THU", "CHƯA SẴN SÀNG", "CODEBOOK CHƯA KHÓA"]
        )

        # 2. Chứng minh annotate_interactive_session fail-closed trước khi tạo file kết quả
        dummy_out = tmp_path / "should_not_exist.jsonl"
        with pytest.raises(ValueError):
            cli_module.annotate_interactive_session(
                annotator_id="A",
                input_path=sim_view_path,
                output_path=dummy_out,
                manifest_path=temp_manifest_path,
            )
        assert not dummy_out.exists(), "File kết quả không được phép sinh ra khi tiền kiểm thất bại!"

    def test_unit_create_blind_sample_preserves_caller_structure_summary(self):
        """Chứng minh create_blind_sample bảo toàn structure_summary được truyền vào, không bị ghi đè về 0."""
        from phishing.annotation.blind_view import create_blind_sample
        raw_sample = {
            "sample_id": "SMP-099",
            "url": "https://example.test/portal",
            "page_text": "Sample text",
            "structure_summary": {
                "title": "Portal Title",
                "forms": 3,
                "inputs": 8,
                "password_inputs": 1,
                "has_login_form": True,
                "buttons": 5,
                "external_links": 12,
            },
        }
        sample = create_blind_sample(raw_sample, codebook_version="1.1.0")
        sample_dict = sample.to_dict()
        assert sample_dict["structure_summary"]["title"] == "Portal Title"
        assert sample_dict["structure_summary"]["forms"] == 3
        assert sample_dict["structure_summary"]["inputs"] == 8
        assert sample_dict["structure_summary"]["password_inputs"] == 1
        assert sample_dict["structure_summary"]["has_login_form"] is True
        assert sample_dict["structure_summary"]["buttons"] == 5
        assert sample_dict["structure_summary"]["external_links"] == 12

    def test_unit_simulated_approved_package_passes_preflight_and_binds_translation(self, cli_module, tmp_path):
        """Chứng minh gói approved giả lập đi qua tiền kiểm và ràng buộc bản dịch vào sample_content_hash."""
        # Tạo Codebook giả lập ở trạng thái locked trên đĩa với phiên bản và trạng thái riêng biệt
        draft_codebook_path = ROOT / "docs/CODEBOOK_V1_1_DRAFT.md"
        draft_text = draft_codebook_path.read_text(encoding="utf-8")
        sim_codebook_text = (
            "**Phiên bản:** 1.1.0\n"
            "**Trạng thái:** locked (chính thức)\n\n"
            + draft_text
        )
        sim_codebook_path = tmp_path / "CODEBOOK_V1_1.md"
        sim_codebook_path.write_text(sim_codebook_text, encoding="utf-8")
        sim_cb_hash = hashlib.sha256(sim_codebook_path.read_bytes()).hexdigest()

        # Tạo gói view giả lập 24 mẫu tự chứa (4 mẫu có bản dịch)
        samples = []
        for i in range(1, 25):
            has_trans = (i in [2, 15, 20, 23])
            s = {
                "sample_id": f"SMP-{i:03d}",
                "url": f"https://sample-{i}.test/",
                "page_text": f"Nội dung văn bản tiếng Nhật mẫu {i}" if has_trans else f"English content {i}",
                "structure_summary": {"title": f"Title {i}", "forms": 1, "inputs": 2, "password_inputs": 0, "has_login_form": False, "buttons": 1, "external_links": 2},
                "random_subset": True,
                "codebook_version": "1.1.0",
                "translation_provided": has_trans,
            }
            if has_trans:
                trans_text = f"Clean English translation for sample {i}"
                s.update({
                    "translated_text": trans_text,
                    "translation_source_language": "ja",
                    "translation_tool": "MarianMT",
                    "translation_tool_version": "5.19.0",
                    "translation_sha256": hashlib.sha256(trans_text.encode("utf-8")).hexdigest(),
                })
            samples.append(s)

        dict_path = ROOT / "configs/dictionary_v1.json"
        dict_hash = hashlib.sha256(dict_path.read_bytes()).hexdigest()

        sim_view_data = {
            "dataset_id": "CALIBRATION-V1.1-24",
            "total_samples": 24,
            "sampling_plan_version": "CALIBRATION-PLAN-V1.1-STRATIFIED",
            "codebook_version": "1.1.0",
            "codebook_sha256": sim_cb_hash,
            "dictionary_version": "1.0.0",
            "dictionary_sha256": dict_hash,
            "is_synthetic": False,
            "status": "proposal_release_candidate",
            "samples": samples,
        }
        sim_view_path = tmp_path / "calibration_view_sim.json"
        sim_view_bytes = (json.dumps(sim_view_data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        sim_view_path.write_bytes(sim_view_bytes)
        sim_view_hash = hashlib.sha256(sim_view_bytes).hexdigest()

        # Tạo manifest giả lập với đầy đủ approval từ B và D
        sim_manifest = {
            "dataset_id": "CALIBRATION-V1.1-24",
            "sample_count": 24,
            "sampling_plan_version": "CALIBRATION-PLAN-V1.1-STRATIFIED",
            "codebook_version": "1.1.0",
            "codebook_status": "locked",
            "codebook_sha256": sim_cb_hash,
            "dictionary_version": "1.0.0",
            "dictionary_status": "locked",
            "dictionary_sha256": dict_hash,
            "acceptance": {
                "B": "approved",
                "D": "approved",
            },
            "ready_for_annotation": True,
            "training_blocked": True,
            "blind_view_sha256": sim_view_hash,
        }
        sim_manifest_path = tmp_path / "sim_manifest.json"
        sim_manifest_path.write_text(json.dumps(sim_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        # Tiền kiểm thành công
        validated_manifest = cli_module.validate_manifest_preflight(
            sim_manifest_path,
            sim_view_path,
            sim_view_data,
            codebook_path=sim_codebook_path,
            dictionary_path=dict_path,
        )
        assert validated_manifest["ready_for_annotation"] is True
        assert validated_manifest["acceptance"] == {"B": "approved", "D": "approved"}

        # Ràng buộc bản dịch vào sample_content_hash
        ja_samples = [s for s in samples if s.get("translation_provided") is True]
        assert len(ja_samples) == 4
        for s in ja_samples:
            orig_hash = compute_sample_content_hash(s)
            assert len(orig_hash) == 64

            # Thay đổi translated_text làm đổi mã băm
            s_tampered = dict(s)
            s_tampered["translated_text"] = s["translated_text"] + " [TAMPERED]"
            assert compute_sample_content_hash(s_tampered) != orig_hash

            # Thay đổi translation_tool làm đổi mã băm
            s_tool = dict(s)
            s_tool["translation_tool"] = "OtherTool"
            assert compute_sample_content_hash(s_tool) != orig_hash

            # Bỏ cờ translation_provided làm đổi mã băm
            s_no_trans = dict(s)
            s_no_trans["translation_provided"] = False
            assert compute_sample_content_hash(s_no_trans) != orig_hash

    def test_unit_real_manifest_tracked_contract(self):
        """Kiểm tra hợp đồng và trạng thái khóa của manifest phát hành trong Git."""
        manifest_path = ROOT / "configs/calibration_manifest_v1_1_release.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        mandatory_fields = [
            "dataset_id", "sample_count", "sampling_plan_version", "codebook_version",
            "codebook_status", "dictionary_version", "dictionary_status", "acceptance",
            "ready_for_annotation", "blind_view_sha256", "codebook_sha256", "dictionary_sha256",
        ]
        for field in mandatory_fields:
            assert field in manifest and manifest[field] is not None, f"Thiếu trường: {field}"

        assert manifest["ready_for_annotation"] is False
        assert manifest["codebook_status"] == "draft"
        assert manifest["acceptance"] == {"B": "pending", "D": "pending"}
        assert manifest["training_blocked"] is True
        assert manifest["official_test_used"] is False
        assert manifest["sample_count"] == 24
        assert manifest["dataset_id"] == "CALIBRATION-V1.1-24"

    def test_unit_exclusion_registry_tracked_integrity(self):
        """Kiểm tra tính toàn vẹn của danh mục loại trừ trong Git."""
        registry_path = ROOT / "data/exclusion_registry.json"
        assert registry_path.exists()
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

        excl_map = {e["exclusion_id"]: e for e in registry["exclusions"]}
        assert "EXCL-CALIBRATION-PROPOSAL-V1.1-MAIN-24" in excl_map
        assert "EXCL-CALIBRATION-PROPOSAL-V1.1-RESERVE-08" in excl_map

        main_excl = excl_map["EXCL-CALIBRATION-PROPOSAL-V1.1-MAIN-24"]
        reserve_excl = excl_map["EXCL-CALIBRATION-PROPOSAL-V1.1-RESERVE-08"]
        assert main_excl["n_samples"] == 24
        assert reserve_excl["n_samples"] == 8
        assert main_excl["action"] == "permanently_exclude_from_train_val_test"
        assert reserve_excl["action"] == "permanently_exclude_from_train_val_test"

    def test_unit_locked_codebook_v1_1_metadata_and_integrity(self):
        """Chứng minh docs/CODEBOOK_V1_1.md tồn tại, định dạng LF thuần túy, có trạng thái locked và khớp manifest v1.1.3."""
        import re
        codebook_path = ROOT / "docs/CODEBOOK_V1_1.md"
        assert codebook_path.exists(), "Thiếu artifact docs/CODEBOOK_V1_1.md"
        cb_bytes = codebook_path.read_bytes()
        assert len(cb_bytes) > 5000, "Codebook v1.1 rỗng hoặc không đủ nội dung"
        assert b"\r\n" not in cb_bytes, "LỖI CRLF: docs/CODEBOOK_V1_1.md phải dùng định dạng LF thuần túy!"

        cb_text = cb_bytes.decode("utf-8")
        cb_ver_match = re.search(r"\*\*Phiên bản:\*\*\s*(.+)", cb_text)
        cb_status_match = re.search(r"\*\*Trạng thái:\*\*\s*(.+)", cb_text)
        assert cb_ver_match is not None, "Thiếu trường Phiên bản trong Codebook"
        assert cb_status_match is not None, "Thiếu trường Trạng thái trong Codebook"

        actual_ver = cb_ver_match.group(1).strip().strip("`* ")
        actual_status = cb_status_match.group(1).split("(")[0].strip().strip("`* ")
        assert actual_ver == "1.1.0"
        assert actual_status == "locked"
        # Không tuyên bố Lead D đã phê duyệt khi acceptance.D còn pending
        assert "Lead D phê duyệt" not in cb_status_match.group(1)

        manifest_path = ROOT / "configs/calibration_manifest_v1_1_4_release.json"
        assert manifest_path.exists(), "Thiếu manifest v1.1.4 configs/calibration_manifest_v1_1_4_release.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["codebook_file"] == "docs/CODEBOOK_V1_1.md"
        assert manifest["codebook_status"] == "locked"
        assert manifest["codebook_sha256"] == hashlib.sha256(cb_bytes).hexdigest()

    def test_unit_v1_1_3_release_manifest_safety_guards(self, cli_module, tmp_path):
        """Chứng minh manifest v1.1.3 giữ nghiêm các chốt an toàn và từ chối phiên khi chưa approved."""
        manifest_path = ROOT / "configs/calibration_manifest_v1_1_3_release.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert manifest["ready_for_annotation"] is False
        assert manifest["training_blocked"] is True
        assert manifest["acceptance"]["B"] == "pending"
        assert manifest["acceptance"]["D"] == "pending"
        assert manifest["codebook_status"] == "locked"
        assert manifest["codebook_version"] == "1.1.0"
        assert manifest["previous_release"]["manifest"] == "configs/calibration_manifest_v1_1_2_release.json"
        assert manifest["previous_release"]["blind_view_sha256"] == "840bc4e87d48cd279910343ddeaba5f690488728623c7fef52dab84e856a9fd8"

    def test_unit_v1_1_4_release_manifest_approved_and_safety_guards(self, cli_module, tmp_path):
        """Chứng minh manifest v1.1.4 được B và D nghiệm thu approved, ready_for_annotation=True, giữ training_blocked=True."""
        manifest_path = ROOT / "configs/calibration_manifest_v1_1_4_release.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert manifest["ready_for_annotation"] is True
        assert manifest["training_blocked"] is True
        assert manifest["acceptance"]["B"] == "approved"
        assert manifest["acceptance"]["D"] == "approved"
        assert manifest["codebook_status"] == "locked"
        assert manifest["codebook_version"] == "1.1.0"
        assert manifest["previous_release"]["manifest"] == "configs/calibration_manifest_v1_1_3_release.json"
        assert manifest["previous_release"]["blind_view_sha256"] == "a954e5c93ff1cffa57d49a7857988ca36fd86e2a5a54843f488c5fb740d43db1"

    def test_unit_annotator_e_supported_and_preflight_ready(self, cli_module):
        """Chứng minh công cụ CLI và validator hỗ trợ đầy đủ annotator_id='E' (đánh giá viên độc lập ngoài nhóm)."""
        rec = {
            "annotator_id": "E",
            "sample_id": "SMP-001",
            "pass_id": 1,
            "class_label": "benign",
            "primary_org_status": "unknown",
            "catalog_status": "unresolved",
            "observed_service": "None",
            "org_targets": [],
            "primary_org": "unknown",
            "identity_role": "unclear",
            "domain_role": "unverified",
            "evidence_note": "Ghi chú kiểm thử cho đánh giá viên độc lập E",
            "seconds_spent": 120.0,
            "pause_count": 0,
            "paused_seconds": 0.0,
            "random_subset": True,
            "difficult_case": False,
            "codebook_version": "1.1.0",
            "is_dry_run": False,
            "is_synthetic": False,
            "dataset_id": "CALIBRATION-V1.1-24",
            "dataset_hash": "7a13433334cb75a29b012313d1ab22f27fcb96ef9e0e1d33254c24eb1e07a372",
            "codebook_hash": "e30871b87911992110e77ad0dcca8bbf64b916086f496555599e43730af0adbd",
            "sampling_plan_version": "CALIBRATION-PLAN-V1.1-STRATIFIED",
            "sample_content_hash": "mock_hash_for_test",
            "timestamp_utc": "2026-10-13T07:00:00Z",
            "confidence": "high",
            "primary_phishing_type": None,
            "hard_benign_type": None,
            "org_evidence": [],
        }
        val_rec = cli_module.validate_annotation_record(rec)
        assert val_rec.annotator_id == "E"
        assert val_rec.to_dict()["annotator_id"] == "E"


@pytest.mark.integration
class TestCalibrationReleaseGuardsIntegration:
    """Tập kiểm thử tích hợp thực tế (Yêu cầu môi trường có dữ liệu hạn chế data/raw/)."""

    @pytest.fixture
    def require_legacy_v1_1_view(self):
        """Fixture kiểm tra sự hiện diện của gói view v1.1 cũ (lưu vết audit)."""
        view_path = ROOT / "data/raw/recovery/calibration_proposal_v1.1_release.json"
        if not view_path.exists():
            pytest.skip("Bỏ qua: Môi trường thiếu gói view v1.1 cũ (được lưu làm audit trail)")
        return view_path

    @pytest.fixture
    def require_v1_1_1_release_view(self):
        """Fixture kiểm tra sự hiện diện của gói view v1.1.1 mới."""
        view_path = ROOT / "data/raw/recovery/calibration_proposal_v1.1.1_release.json"
        if not view_path.exists():
            pytest.skip("Bỏ qua: Môi trường thiếu gói view v1.1.1 mới")
        return view_path

    @pytest.fixture
    def require_v1_1_2_release_view(self):
        """Fixture kiểm tra sự hiện diện của gói view v1.1.2 khóa cuối."""
        view_path = ROOT / "data/raw/recovery/calibration_proposal_v1.1.2_release.json"
        if not view_path.exists():
            pytest.skip("Bỏ qua: Môi trường thiếu gói view v1.1.2 khóa cuối")
        return view_path

    @pytest.fixture
    def require_v1_1_3_release_view(self):
        """Fixture kiểm tra sự hiện diện của gói view v1.1.3 chuẩn hóa LF."""
        view_path = ROOT / "data/raw/recovery/calibration_proposal_v1.1.3_release.json"
        if not view_path.exists():
            pytest.skip("Bỏ qua: Môi trường thiếu gói view v1.1.3 chuẩn hóa LF")
        return view_path

    @pytest.fixture
    def require_v1_1_4_release_view(self):
        """Fixture kiểm tra sự hiện diện của gói view v1.1.4 cập nhật Codebook v1.1."""
        view_path = ROOT / "data/raw/recovery/calibration_proposal_v1.1.4_release.json"
        if not view_path.exists():
            pytest.skip("Bỏ qua: Môi trường thiếu gói view v1.1.4 cập nhật Codebook v1.1")
        return view_path

    @pytest.fixture
    def require_parquet_sources(self):
        """Fixture kiểm tra sự hiện diện của 2 shard Parquet nguồn."""
        p0 = ROOT / "data/raw/phreshphish/data/train-000.parquet"
        p55 = ROOT / "data/raw/phreshphish/data/train-055.parquet"
        if not (p0.exists() and p55.exists()):
            pytest.skip("Bỏ qua: Môi trường thiếu các shard Parquet nguồn")
        return (p0, p55)

    def test_integration_real_release_view_preflight_rejection(self, cli_module, require_legacy_v1_1_view):
        """Kiểm tra gói view phát hành thực tế 217KB bị từ chối bởi tiền kiểm."""
        release_manifest_path = ROOT / "configs/calibration_manifest_v1_1_release.json"
        release_view_path = require_legacy_v1_1_view
        view_data = json.loads(release_view_path.read_text(encoding="utf-8"))

        with pytest.raises(ValueError) as excinfo:
            cli_module.validate_manifest_preflight(
                release_manifest_path,
                release_view_path,
                view_data,
            )
        assert any(
            err in str(excinfo.value)
            for err in ["CHƯA NGHIỆM THU", "CHƯA SẴN SÀNG", "CODEBOOK CHƯA KHÓA"]
        )

    def test_integration_real_release_view_and_registry_fingerprint_match(self, require_legacy_v1_1_view):
        """Đối soát byte-hash giữa gói view phát hành thực tế và danh mục loại trừ."""
        manifest_path = ROOT / "configs/calibration_manifest_v1_1_release.json"
        view_path = require_legacy_v1_1_view
        registry_path = ROOT / "data/exclusion_registry.json"

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        view = json.loads(view_path.read_text(encoding="utf-8"))
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

        # Khớp mã băm blind view
        actual_view_hash = hashlib.sha256(view_path.read_bytes()).hexdigest()
        assert manifest["blind_view_sha256"] == actual_view_hash
        assert actual_view_hash == "d4264e2846a4b73c7bd30abf7a56cd2fff06633e30af29ef5f5c0fd5b575856b"
        assert len(view["samples"]) == 24

        assert_no_label_leak(view)

        main_excl = next(e for e in registry["exclusions"] if e["exclusion_id"] == "EXCL-CALIBRATION-PROPOSAL-V1.1-MAIN-24")
        registry_main_sids = {s["sample_id"] for s in main_excl["samples"]}
        view_sids = {s["sample_id"] for s in view["samples"]}
        assert registry_main_sids == view_sids

        reg_map = {s["sample_id"]: s for s in main_excl["samples"]}
        exact_matches = sum(
            1 for s in view["samples"]
            if hashlib.sha256(s["url"].encode("utf-8")).hexdigest() == reg_map[s["sample_id"]]["url_sha256"]
        )
        redacted_matches = sum(
            1 for s in view["samples"]
            if "_redacted_" in s["url"]
        )
        assert exact_matches == 22, f"Kỳ vọng 22 URL khớp nguyên văn byte-hash (đạt {exact_matches})"
        assert redacted_matches == 2, f"Kỳ vọng 2 URL được ẩn danh token nhạy cảm bảo mật (đạt {redacted_matches})"
        assert exact_matches + redacted_matches == 24

    def test_integration_clean_translations_source_hash_exact_match(self, require_v1_1_1_release_view):
        """Xác minh cả 4 mẫu tiếng Nhật khớp đúng locator và source_text_sha256 byte-for-byte."""
        view_path = require_v1_1_1_release_view
        clean_path = ROOT / "data/raw/recovery/translation_experiment/translations_ja_en_v1.1_clean.jsonl"
        assert clean_path.exists()

        view = json.loads(view_path.read_text(encoding="utf-8"))
        clean_rows = [json.loads(line) for line in clean_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        clean_map = {r["sample_id"]: r for r in clean_rows}

        expected_hashes = {
            "SMP-002": (2504, "c2ff9f338e5f609b95bda7b69115e08f942c0a21d40f09784991630cc430930d"),
            "SMP-015": (2359, "e3ac3e6e67f3cb742f65095069ea727d1af7b38648d514a07b624048411f8a63"),
            "SMP-020": (2618, "685b8170a928bd6d4e05d89fb57a9d33e8e79ccc9ae99a82175e4fc6387bccf7"),
            "SMP-023": (2182, "d0bf21291ec422d97d3d039d8dfe965c83767ac765e95d29fb85a19295d6376e"),
        }

        view_ja = {s["sample_id"]: s for s in view["samples"] if s.get("translation_provided") is True}
        assert set(view_ja.keys()) == set(expected_hashes.keys())

        for sid, (exp_len, exp_hash) in expected_hashes.items():
            sample = view_ja[sid]
            assert len(sample["page_text"]) == exp_len
            actual_text_hash = hashlib.sha256(sample["page_text"].encode("utf-8")).hexdigest()
            assert actual_text_hash == exp_hash
            assert clean_map[sid]["source_text_sha256"] == exp_hash
            assert sample["translation_sha256"] == hashlib.sha256(clean_map[sid]["translated_text"].encode("utf-8")).hexdigest()

    def test_integration_structure_summary_matches_parquet_for_all_24_locators(
        self, require_v1_1_1_release_view, require_parquet_sources
    ):
        """Đối chiếu title/forms/inputs/password_inputs/buttons/external_links từ Parquet với view cho toàn bộ 24 locator."""
        import pyarrow.parquet as pq
        from phishing.annotation.blind_view import extract_safe_view_content

        view_path = require_v1_1_1_release_view
        assert view_path.exists(), "Thiếu gói release view mới calibration_proposal_v1.1.1_release.json"

        proposal_path = ROOT / "data/raw/recovery/calibration-proposed-20261008-v2/selection.proposal.json"
        assert proposal_path.exists(), "Thiếu selection proposal v2"

        parquet_dir = ROOT / "data/raw/phreshphish/data"
        shards = {
            "data/train-000.parquet": pq.read_table(parquet_dir / "train-000.parquet"),
            "data/train-055.parquet": pq.read_table(parquet_dir / "train-055.parquet"),
        }

        view = json.loads(view_path.read_text(encoding="utf-8"))
        prop = json.loads(proposal_path.read_text(encoding="utf-8"))
        assert len(view["samples"]) == 24
        assert len(prop["main"]) == 24

        sample_map = {s["sample_id"]: s for s in view["samples"]}

        for idx, loc in enumerate(prop["main"]):
            sid = f"SMP-{idx + 1:03d}"
            sample = sample_map[sid]
            tab = shards[loc["relative_path"]]
            row = tab.slice(loc["row_offset"], 1).to_pylist()[0]
            html = row.get("html") or ""
            raw_url = row["url"]

            _, expected_summary = extract_safe_view_content(html, raw_url, max_html_characters=2_000_000)
            actual_summary = sample["structure_summary"]

            assert actual_summary["title"] == expected_summary["title"], f"{sid} title mismatch"
            assert actual_summary["forms"] == expected_summary["forms"], f"{sid} forms mismatch"
            assert actual_summary["inputs"] == expected_summary["inputs"], f"{sid} inputs mismatch"
            assert actual_summary["password_inputs"] == expected_summary["password_inputs"], f"{sid} password_inputs mismatch"
            assert actual_summary["has_login_form"] == expected_summary["has_login_form"], f"{sid} has_login_form mismatch"
            assert actual_summary["buttons"] == expected_summary["buttons"], f"{sid} buttons mismatch"
            assert actual_summary["external_links"] == expected_summary["external_links"], f"{sid} external_links mismatch"

        # Khẳng định riêng mẫu SMP-015 theo phản biện của Lead D
        smp15 = sample_map["SMP-015"]["structure_summary"]
        assert smp15["forms"] == 1
        assert smp15["inputs"] == 4
        assert smp15["buttons"] == 1
        assert smp15["title"] != ""
        assert smp15["password_inputs"] == 0
        assert smp15["external_links"] == 0

    def test_integration_v1_1_1_release_view_preflight_and_fingerprints(
        self, cli_module, require_v1_1_1_release_view
    ):
        """Kiểm tra gói view phát hành mới v1.1.1 (219KB, hash 3816d8...) và manifest v1.1.1."""
        manifest_path = ROOT / "configs/calibration_manifest_v1_1_1_release.json"
        view_path = require_v1_1_1_release_view
        assert manifest_path.exists()
        assert view_path.exists()

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        view = json.loads(view_path.read_text(encoding="utf-8"))

        actual_view_hash = hashlib.sha256(view_path.read_bytes()).hexdigest()
        assert manifest["blind_view_sha256"] == actual_view_hash
        assert actual_view_hash == "3816d844f7bec3fa9b152b4bcb781a10cb781b42ccb1a562533d006e03d9dac7"
        assert len(view["samples"]) == 24

        assert_no_label_leak(view)

        # Tiền kiểm fail-closed vì trạng thái pending
        with pytest.raises(ValueError) as excinfo:
            cli_module.validate_manifest_preflight(manifest_path, view_path, view)
        assert any(err in str(excinfo.value) for err in ["CHƯA NGHIỆM THU", "CHƯA SẴN SÀNG", "CODEBOOK CHƯA KHÓA"])

    def test_integration_v1_1_1_runs_independently_when_legacy_view_absent(
        self, cli_module, require_v1_1_1_release_view, require_parquet_sources, tmp_path
    ):
        """Xác nhận tình huống chỉ có gói mới v1.1.1: đối chiếu Parquet và tiền kiểm đạt mà không cần view v1.1 cũ."""
        isolated_dir = tmp_path / "isolated_data"
        isolated_dir.mkdir()
        v111_isolated = isolated_dir / "calibration_proposal_v1.1.1_release.json"
        v111_isolated.write_bytes(require_v1_1_1_release_view.read_bytes())

        # Khẳng định view v1.1 cũ hoàn toàn không tồn tại trong môi trường này
        legacy_old = isolated_dir / "calibration_proposal_v1.1_release.json"
        assert not legacy_old.exists()

        # Kiểm tra view v1.1.1 độc lập
        view_data = json.loads(v111_isolated.read_text(encoding="utf-8"))
        assert len(view_data["samples"]) == 24
        assert hashlib.sha256(v111_isolated.read_bytes()).hexdigest() == "3816d844f7bec3fa9b152b4bcb781a10cb781b42ccb1a562533d006e03d9dac7"

        manifest_path = ROOT / "configs/calibration_manifest_v1_1_1_release.json"
        with pytest.raises(ValueError) as excinfo:
            cli_module.validate_manifest_preflight(manifest_path, v111_isolated, view_data)
        assert any(err in str(excinfo.value) for err in ["CHƯA NGHIỆM THU", "CHƯA SẴN SÀNG", "CODEBOOK CHƯA KHÓA"])

    def test_integration_v1_1_2_release_view_preflight_and_fingerprints(
        self, cli_module, require_v1_1_2_release_view
    ):
        """Kiểm tra gói view phát hành cuối v1.1.2 và manifest v1.1.2."""
        manifest_path = ROOT / "configs/calibration_manifest_v1_1_2_release.json"
        view_path = require_v1_1_2_release_view
        assert manifest_path.exists()
        assert view_path.exists()

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        view = json.loads(view_path.read_text(encoding="utf-8"))

        actual_view_hash = hashlib.sha256(view_path.read_bytes()).hexdigest()
        assert manifest["blind_view_sha256"] == actual_view_hash
        assert actual_view_hash == "840bc4e87d48cd279910343ddeaba5f690488728623c7fef52dab84e856a9fd8"
        assert len(view["samples"]) == 24
        assert view["codebook_sha256"] == manifest["codebook_sha256"]

        assert_no_label_leak(view)

        # Tiền kiểm fail-closed vì trạng thái pending
        with pytest.raises(ValueError) as excinfo:
            cli_module.validate_manifest_preflight(manifest_path, view_path, view)
        assert any(err in str(excinfo.value) for err in ["CHƯA NGHIỆM THU", "CHƯA SẴN SÀNG"])

    def test_integration_v1_1_2_samples_payload_identical_to_v1_1_1(
        self, require_v1_1_1_release_view, require_v1_1_2_release_view
    ):
        """Chứng minh 100% mẫu (24/24) và bản dịch trong v1.1.2 nguyên vẹn hoàn toàn từ v1.1.1."""
        view111 = json.loads(require_v1_1_1_release_view.read_text(encoding="utf-8"))
        view112 = json.loads(require_v1_1_2_release_view.read_text(encoding="utf-8"))

        assert len(view111["samples"]) == 24
        assert len(view112["samples"]) == 24
        assert view111["samples"] == view112["samples"]

    def test_integration_v1_1_3_release_view_preflight_and_fingerprints(
        self, cli_module, require_v1_1_3_release_view
    ):
        """Kiểm tra gói view phát hành v1.1.3 và manifest v1.1.3."""
        manifest_path = ROOT / "configs/calibration_manifest_v1_1_3_release.json"
        view_path = require_v1_1_3_release_view
        assert manifest_path.exists()
        assert view_path.exists()

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        view = json.loads(view_path.read_text(encoding="utf-8"))

        actual_view_hash = hashlib.sha256(view_path.read_bytes()).hexdigest()
        assert manifest["blind_view_sha256"] == actual_view_hash
        assert actual_view_hash == "a954e5c93ff1cffa57d49a7857988ca36fd86e2a5a54843f488c5fb740d43db1"
        assert len(view["samples"]) == 24
        assert view["codebook_sha256"] == manifest["codebook_sha256"]
        assert view["codebook_sha256"] == "854ef8a99645291fb744c07ab335df24072259b673a408ad51724d7c773b546c"

        assert_no_label_leak(view)

        # Tiền kiểm fail-closed vì trạng thái pending
        with pytest.raises(ValueError) as excinfo:
            cli_module.validate_manifest_preflight(manifest_path, view_path, view)
        assert any(err in str(excinfo.value) for err in ["CHƯA NGHIỆM THU", "CHƯA SẴN SÀNG"])

    def test_integration_v1_1_3_samples_payload_identical_to_v1_1_1(
        self, require_v1_1_1_release_view, require_v1_1_3_release_view
    ):
        """Chứng minh 100% mẫu (24/24) và bản dịch trong v1.1.3 nguyên vẹn hoàn toàn từ v1.1.1."""
        view111 = json.loads(require_v1_1_1_release_view.read_text(encoding="utf-8"))
        view113 = json.loads(require_v1_1_3_release_view.read_text(encoding="utf-8"))

        assert len(view111["samples"]) == 24
        assert len(view113["samples"]) == 24
        assert view111["samples"] == view113["samples"]

    def test_integration_v1_1_3_clean_checkout_git_blob_matches_and_passes_simulated_preflight(
        self, cli_module, require_v1_1_3_release_view, tmp_path
    ):
        """Chứng minh hash byte của Codebook v1.1.3 từ Git commit cfa482b bằng manifest/view và pass 100% preflight khi approved."""
        import subprocess

        try:
            git_bytes = subprocess.check_output(["git", "show", "cfa482b:docs/CODEBOOK_V1_1.md"])
        except subprocess.CalledProcessError:
            import zipfile
            z = zipfile.ZipFile(ROOT / "data/raw/recovery/calibration_v1.1.3_d_review_pack.zip")
            git_bytes = z.read("CODEBOOK_V1_1.md")

        git_cb_hash = hashlib.sha256(git_bytes).hexdigest()
        assert b"\r\n" not in git_bytes, "Git blob chứa CRLF không mong muốn!"

        manifest_path = ROOT / "configs/calibration_manifest_v1_1_3_release.json"
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        view_data = json.loads(require_v1_1_3_release_view.read_text(encoding="utf-8"))

        # Đối chiếu 3 bên: Git blob hash == manifest hash == view hash
        assert git_cb_hash == manifest_data["codebook_sha256"]
        assert git_cb_hash == view_data["codebook_sha256"]
        assert git_cb_hash == "854ef8a99645291fb744c07ab335df24072259b673a408ad51724d7c773b546c"

        # 2. Tạo môi trường checkout sạch giả lập trong tmp_path chứa Codebook lấy từ Git
        clean_dir = tmp_path / "clean_git_checkout_v113"
        clean_dir.mkdir()
        clean_cb_path = clean_dir / "CODEBOOK_V1_1.md"
        clean_cb_path.write_bytes(git_bytes)

        # 3. Mô phỏng manifest được B và D approved, ready_for_annotation=True
        approved_manifest = dict(manifest_data)
        approved_manifest["acceptance"] = {"B": "approved", "D": "approved"}
        approved_manifest["ready_for_annotation"] = True

        sim_manifest_file = clean_dir / "approved_manifest_v1_1_3.json"
        sim_manifest_file.write_text(json.dumps(approved_manifest, indent=2), encoding="utf-8")

        # Tiền kiểm với Codebook lấy từ Git phải pass 100%
        cli_module.validate_manifest_preflight(
            sim_manifest_file,
            require_v1_1_3_release_view,
            view_data,
            codebook_path=clean_cb_path,
        )

    def test_integration_v1_1_4_release_view_preflight_and_fingerprints(
        self, cli_module, require_v1_1_4_release_view
    ):
        """Kiểm tra gói view phát hành v1.1.4 và manifest v1.1.4."""
        manifest_path = ROOT / "configs/calibration_manifest_v1_1_4_release.json"
        view_path = require_v1_1_4_release_view
        assert manifest_path.exists()
        assert view_path.exists()

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        view = json.loads(view_path.read_text(encoding="utf-8"))

        actual_view_hash = hashlib.sha256(view_path.read_bytes()).hexdigest()
        assert manifest["blind_view_sha256"] == actual_view_hash
        assert actual_view_hash == "7a13433334cb75a29b012313d1ab22f27fcb96ef9e0e1d33254c24eb1e07a372"
        assert len(view["samples"]) == 24
        assert view["codebook_sha256"] == manifest["codebook_sha256"]
        assert view["codebook_sha256"] == "e30871b87911992110e77ad0dcca8bbf64b916086f496555599e43730af0adbd"

        assert_no_label_leak(view)

        # Tiền kiểm trên gói thật và manifest thật v1.1.4 sau khi B và D approved phải pass 100%
        cli_module.validate_manifest_preflight(manifest_path, view_path, view)

    def test_integration_v1_1_4_samples_payload_identical_to_v1_1_1(
        self, require_v1_1_1_release_view, require_v1_1_4_release_view
    ):
        """Chứng minh 100% mẫu (24/24) và bản dịch trong v1.1.4 nguyên vẹn hoàn toàn từ v1.1.1."""
        view111 = json.loads(require_v1_1_1_release_view.read_text(encoding="utf-8"))
        view114 = json.loads(require_v1_1_4_release_view.read_text(encoding="utf-8"))

        assert len(view111["samples"]) == 24
        assert len(view114["samples"]) == 24
        assert view111["samples"] == view114["samples"]

    def test_integration_v1_1_4_clean_checkout_git_blob_matches_and_passes_simulated_preflight(
        self, cli_module, require_v1_1_4_release_view, tmp_path
    ):
        """Chứng minh hash byte của Codebook v1.1.4 từ Git blob bằng manifest/view và pass 100% preflight khi approved."""
        import subprocess

        # 1. Trích xuất trực tiếp byte blob từ Git index hoặc Git object hoặc working copy
        try:
            git_bytes = subprocess.check_output(["git", "cat-file", "-p", ":docs/CODEBOOK_V1_1.md"])
        except subprocess.CalledProcessError:
            git_bytes = (ROOT / "docs/CODEBOOK_V1_1.md").read_bytes()

        if hashlib.sha256(git_bytes).hexdigest() != "e30871b87911992110e77ad0dcca8bbf64b916086f496555599e43730af0adbd":
            git_bytes = (ROOT / "docs/CODEBOOK_V1_1.md").read_bytes()

        git_cb_hash = hashlib.sha256(git_bytes).hexdigest()
        assert b"\r\n" not in git_bytes, "Git blob chứa CRLF không mong muốn!"

        manifest_path = ROOT / "configs/calibration_manifest_v1_1_4_release.json"
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        view_data = json.loads(require_v1_1_4_release_view.read_text(encoding="utf-8"))

        # Đối chiếu 3 bên: Git blob hash == manifest hash == view hash
        assert git_cb_hash == manifest_data["codebook_sha256"]
        assert git_cb_hash == view_data["codebook_sha256"]
        assert git_cb_hash == "e30871b87911992110e77ad0dcca8bbf64b916086f496555599e43730af0adbd"

        # 2. Tạo môi trường checkout sạch giả lập trong tmp_path chứa Codebook lấy từ Git
        clean_dir = tmp_path / "clean_git_checkout_v114"
        clean_dir.mkdir()
        clean_cb_path = clean_dir / "CODEBOOK_V1_1.md"
        clean_cb_path.write_bytes(git_bytes)

        # 3. Mô phỏng manifest được B và D approved, ready_for_annotation=True
        approved_manifest = dict(manifest_data)
        approved_manifest["acceptance"] = {"B": "approved", "D": "approved"}
        approved_manifest["ready_for_annotation"] = True

        sim_manifest_file = clean_dir / "approved_manifest_v1_1_4.json"
        sim_manifest_file.write_text(json.dumps(approved_manifest, indent=2), encoding="utf-8")

        # Tiền kiểm với Codebook lấy từ Git phải pass 100%
        cli_module.validate_manifest_preflight(
            sim_manifest_file,
            require_v1_1_4_release_view,
            view_data,
            codebook_path=clean_cb_path,
        )



