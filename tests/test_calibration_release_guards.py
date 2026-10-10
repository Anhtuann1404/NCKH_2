"""Kiểm thử chốt chặn an toàn cho đường chạy hiệu chuẩn Calibration v1.1.

Quy chuẩn ARS & Safety:
1. Gói pending (cả bản cũ và bản phát hành mới do C chuẩn bị) bắt buộc bị từ chối
   bởi tiền kiểm của annotate_cli.py trước khi hiển thị mẫu hoặc tạo bản ghi gán nhãn.
2. Gói approved giả lập (simulated approved package) vượt qua tiền kiểm,
   chứng minh đầy đủ chuỗi provenance và ràng buộc bản dịch vào sample_content_hash.
3. Gói thật duy trì tuyệt đối: ready_for_annotation=false, codebook_status=draft,
   acceptance={"B": "pending", "D": "pending"}, training_blocked=true.
4. Toàn bộ 24 mẫu chính và 8 mẫu dự phòng được khóa an toàn trong exclusion_registry.json;
   tuyệt đối không sử dụng Official Test.
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


class TestCalibrationReleaseGuards:
    """Bộ kiểm tra các chốt chặn phát hành Calibration v1.1."""

    def test_pending_manifest_and_release_manifest_are_rejected(self, cli_module, tmp_path):
        """Chứng minh cả QA manifest cũ và release runway manifest mới đều bị từ chối."""
        qa_manifest_path = ROOT / "configs/calibration_manifest_v1_1.json"
        release_manifest_path = ROOT / "configs/calibration_manifest_v1_1_release.json"
        release_view_path = ROOT / "data/raw/recovery/calibration_proposal_v1.1_release.json"

        assert qa_manifest_path.exists(), "Thiếu QA manifest configs/calibration_manifest_v1_1.json"
        assert release_manifest_path.exists(), "Thiếu release manifest configs/calibration_manifest_v1_1_release.json"
        assert release_view_path.exists(), "Thiếu release view data/raw/recovery/calibration_proposal_v1.1_release.json"

        view_data = json.loads(release_view_path.read_text(encoding="utf-8"))

        # 1. Kiểm tra tiền kiểm từ chối release_manifest do acceptance pending & ready_for_annotation=false
        with pytest.raises(ValueError) as excinfo:
            cli_module.validate_manifest_preflight(
                release_manifest_path,
                release_view_path,
                view_data,
            )
        assert any(
            err_msg in str(excinfo.value)
            for err_msg in ["CHƯA NGHIỆM THU", "CHƯA SẴN SÀNG", "CODEBOOK CHƯA KHÓA"]
        ), f"Lỗi không mong đợi: {excinfo.value}"

        # 2. Chứng minh annotate_interactive_session fail-closed trước khi hiển thị mẫu hoặc tạo file kết quả
        dummy_out = tmp_path / "should_not_exist.jsonl"
        with pytest.raises(ValueError):
            cli_module.annotate_interactive_session(
                annotator_id="A",
                input_path=release_view_path,
                output_path=dummy_out,
                manifest_path=release_manifest_path,
            )
        assert not dummy_out.exists(), "File kết quả không được phép sinh ra khi tiền kiểm thất bại!"

    def test_simulated_approved_package_passes_preflight_and_binds_translation(self, cli_module, tmp_path):
        """Chứng minh gói approved giả lập đi qua tiền kiểm và ràng buộc bản dịch vào sample_content_hash."""
        release_view_path = ROOT / "data/raw/recovery/calibration_proposal_v1.1_release.json"
        view_data = json.loads(release_view_path.read_text(encoding="utf-8"))

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

        # Tạo gói view giả lập khớp với sim_cb_hash
        sim_view_data = dict(view_data)
        sim_view_data["codebook_sha256"] = sim_cb_hash
        sim_view_path = tmp_path / "calibration_view_sim.json"
        sim_view_bytes = (json.dumps(sim_view_data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        sim_view_path.write_bytes(sim_view_bytes)
        sim_view_hash = hashlib.sha256(sim_view_bytes).hexdigest()

        dict_path = ROOT / "configs/dictionary_v1.json"
        dict_hash = hashlib.sha256(dict_path.read_bytes()).hexdigest()

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

        # Kiểm tra tính toàn vẹn của sample_content_hash ràng buộc chặt chẽ bản dịch
        samples = sim_view_data["samples"]
        ja_samples = [s for s in samples if s.get("translation_provided") is True]
        assert len(ja_samples) == 4, f"Yêu cầu đủ 4 mẫu có bản dịch tiếng Nhật (tìm thấy {len(ja_samples)})"

        for s in ja_samples:
            content_hash_orig = compute_sample_content_hash(s)
            assert len(content_hash_orig) == 64

            # Nếu thay đổi translated_text, mã băm phải thay đổi hoàn toàn
            s_tampered = dict(s)
            s_tampered["translated_text"] = s["translated_text"] + " [TAMPERED]"
            content_hash_tampered = compute_sample_content_hash(s_tampered)
            assert content_hash_tampered != content_hash_orig, (
                f"sample_content_hash không bắt được thay đổi bản dịch trên mẫu {s['sample_id']}"
            )

            # Nếu gỡ bỏ cờ translation_provided, mã băm cũng phải thay đổi
            s_no_trans = dict(s)
            s_no_trans["translation_provided"] = False
            assert compute_sample_content_hash(s_no_trans) != content_hash_orig

    def test_real_package_state_and_exclusion_registry_integrity(self):
        """Kiểm tra tính toàn vẹn trạng thái gói thật và đăng ký loại trừ vĩnh viễn."""
        manifest_path = ROOT / "configs/calibration_manifest_v1_1_release.json"
        view_path = ROOT / "data/raw/recovery/calibration_proposal_v1.1_release.json"
        registry_path = ROOT / "data/exclusion_registry.json"

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        view = json.loads(view_path.read_text(encoding="utf-8"))
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

        # 1. Trạng thái gói thật tuyệt đối an toàn (blocked & draft)
        assert manifest["ready_for_annotation"] is False
        assert manifest["codebook_status"] == "draft"
        assert manifest["acceptance"] == {"B": "pending", "D": "pending"}
        assert manifest["training_blocked"] is True
        assert manifest["official_test_used"] is False

        # 2. Khớp mã băm và số lượng mẫu
        actual_view_hash = hashlib.sha256(view_path.read_bytes()).hexdigest()
        assert manifest["blind_view_sha256"] == actual_view_hash
        assert manifest["sample_count"] == len(view["samples"]) == 24
        assert manifest["dataset_id"] == view["dataset_id"] == "CALIBRATION-V1.1-24"
        assert manifest["sampling_plan_version"] == view["sampling_plan_version"] == "CALIBRATION-PLAN-V1.1-STRATIFIED"

        # 3. Chống rò rỉ nhãn
        assert_no_label_leak(view)

        # 4. Kiểm tra danh mục loại trừ (exclusion registry) chứa đủ 24 mẫu chính + 8 mẫu dự phòng
        excl_map = {e["exclusion_id"]: e for e in registry["exclusions"]}
        assert "EXCL-CALIBRATION-PROPOSAL-V1.1-MAIN-24" in excl_map, "Thiếu đăng ký 24 mẫu chính"
        assert "EXCL-CALIBRATION-PROPOSAL-V1.1-RESERVE-08" in excl_map, "Thiếu đăng ký 8 mẫu dự phòng"

        main_excl = excl_map["EXCL-CALIBRATION-PROPOSAL-V1.1-MAIN-24"]
        reserve_excl = excl_map["EXCL-CALIBRATION-PROPOSAL-V1.1-RESERVE-08"]

        assert main_excl["n_samples"] == 24
        assert reserve_excl["n_samples"] == 8
        assert main_excl["action"] == "permanently_exclude_from_train_val_test"
        assert reserve_excl["action"] == "permanently_exclude_from_train_val_test"

        # 5. Khớp sample_id và URL hashes giữa gói phát hành và đăng ký loại trừ
        registry_main_sids = {s["sample_id"] for s in main_excl["samples"]}
        view_sids = {s["sample_id"] for s in view["samples"]}
        assert registry_main_sids == view_sids, "Tập sample_id trong gói phát hành không khớp 100% với registry loại trừ!"

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
        assert exact_matches + redacted_matches == 24, "Tất cả 24 mẫu phát hành phải được định danh trong registry loại trừ"
