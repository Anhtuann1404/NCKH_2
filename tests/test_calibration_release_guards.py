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


@pytest.mark.integration
class TestCalibrationReleaseGuardsIntegration:
    """Tập kiểm thử tích hợp thực tế (Yêu cầu môi trường có dữ liệu hạn chế data/raw/)."""

    @pytest.fixture(autouse=True)
    def check_restricted_data_available(self):
        release_view_path = ROOT / "data/raw/recovery/calibration_proposal_v1.1_release.json"
        if not release_view_path.exists():
            pytest.skip("Bỏ qua integration test: Môi trường clean checkout không có dữ liệu hạn chế data/raw/")

    def test_integration_real_release_view_preflight_rejection(self, cli_module, tmp_path):
        """Kiểm tra gói view phát hành thực tế 217KB bị từ chối bởi tiền kiểm."""
        release_manifest_path = ROOT / "configs/calibration_manifest_v1_1_release.json"
        release_view_path = ROOT / "data/raw/recovery/calibration_proposal_v1.1_release.json"
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

    def test_integration_real_release_view_and_registry_fingerprint_match(self):
        """Đối soát byte-hash giữa gói view phát hành thực tế và danh mục loại trừ."""
        manifest_path = ROOT / "configs/calibration_manifest_v1_1_release.json"
        view_path = ROOT / "data/raw/recovery/calibration_proposal_v1.1_release.json"
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

    def test_integration_clean_translations_source_hash_exact_match(self):
        """Xác minh cả 4 mẫu tiếng Nhật khớp đúng locator và source_text_sha256 byte-for-byte."""
        view_path = ROOT / "data/raw/recovery/calibration_proposal_v1.1_release.json"
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
