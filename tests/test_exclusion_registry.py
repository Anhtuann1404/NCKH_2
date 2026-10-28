"""Bộ kiểm thử cho Exclusion Registry và bộ lọc chống rò rỉ dữ liệu (Task DATA-01).

Kiểm tra:
1. Gọi ExclusionRegistry() với đường dẫn mặc định (không truyền đối số) phải tìm đúng file và nạp đủ 20 mẫu.
2. Ném FileNotFoundError khi đường dẫn registry không tồn tại.
3. Ném RuntimeError chặn huấn luyện chính (assert_training_allowed) khi mapping pilot còn unresolved (kể cả khi cờ training_blocked bị sửa thành False).
4. Chứng minh toàn bộ 20 mẫu pilot bị chặn thông qua summary_fingerprint_hash và fingerprint cấu trúc.
5. Kiểm tra tính năng lọc tách biệt (kept vs excluded).
6. Kiểm tra ném lỗi phát hiện rò rỉ (assert_no_leakage).
"""

import json
from pathlib import Path
import pytest

from phishing.data.exclusion import (
    ExclusionRegistry,
    compute_sample_fingerprint_hash,
    compute_summary_fingerprint_hash,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PILOT_SUMMARY_PATH = PROJECT_ROOT / "data" / "source_audit" / "phreshphish" / "pilot_summary.json"
EXCLUSION_PATH = PROJECT_ROOT / "data" / "exclusion_registry.json"


class TestExclusionRegistry:
    """Kiểm tra sự cô lập triệt để của các mẫu pilot khỏi dữ liệu thực nghiệm."""

    def test_default_constructor_finds_registry(self):
        """Khởi tạo không truyền đối số phải tìm đúng file data/exclusion_registry.json."""
        registry = ExclusionRegistry()
        assert registry.path.exists()
        assert len(registry._sample_fingerprints) == 20
        assert len(registry._sample_hashes) == 20

    def test_missing_registry_file_raises_filenotfound(self):
        """Khi file không tồn tại, phải ném lỗi FileNotFoundError, không được âm thầm bỏ qua."""
        with pytest.raises(FileNotFoundError, match="Không tìm thấy tệp exclusion registry"):
            ExclusionRegistry(registry_path="non_existent/path/registry.json")

    def test_training_blocked_until_pilot_resolved(self):
        """Chặn huấn luyện chính khi ánh xạ pilot chưa được giải quyết."""
        registry = ExclusionRegistry()
        assert registry.training_blocked is True
        with pytest.raises(RuntimeError, match="LỆNH CHẶN HUẤN LUYỆN CHÍNH"):
            registry.assert_training_allowed()

    def test_training_blocked_even_if_flag_is_false_when_mapping_unresolved(self, tmp_path):
        """Dù cờ training_blocked bị đổi thành False, hàm assert_training_allowed vẫn phải chặn nếu còn lô unresolved."""
        reg_file = tmp_path / "registry.json"
        reg_file.write_text(json.dumps({
            "version": "1.1.0",
            "training_blocked": False,
            "exclusions": [
                {
                    "exclusion_id": "EXCL-PILOT-01",
                    "mapping_status": "unresolved_source_mapping",
                    "rows_api_revision_pinned": False,
                    "samples": [{"url_sha256": "1234567890abcdef"}]
                }
            ]
        }), encoding="utf-8")
        registry = ExclusionRegistry(reg_file)
        with pytest.raises(
            RuntimeError,
            match="Lô loại trừ 'EXCL-PILOT-01' có trạng thái mapping='unresolved_source_mapping'",
        ):
            registry.assert_training_allowed()

    def test_training_allowed_when_all_batches_resolved_and_pinned(self, tmp_path):
        """Khi tất cả các lô đã được resolved, rows_api_revision_pinned=True và training_blocked=False, cho phép huấn luyện."""
        reg_file = tmp_path / "registry.json"
        reg_file.write_text(json.dumps({
            "version": "1.1.0",
            "training_blocked": False,
            "exclusions": [
                {
                    "exclusion_id": "EXCL-TEST-01",
                    "mapping_status": "resolved",
                    "rows_api_revision_pinned": True,
                    "samples": [{"url_sha256": "1234567890abcdef"}]
                }
            ]
        }), encoding="utf-8")
        registry = ExclusionRegistry(reg_file)
        # Không được ném ngoại lệ
        registry.assert_training_allowed()

    def test_registry_file_structure(self):
        assert EXCLUSION_PATH.exists()
        data = json.loads(EXCLUSION_PATH.read_text(encoding="utf-8"))
        assert data["version"] == "1.1.0"
        assert data["total_excluded_samples"] == sum(e.get("n_samples", len(e.get("samples", []))) for e in data["exclusions"])
        assert data["total_excluded_samples"] >= 32
        assert data["training_blocked"] is True

        excl = data["exclusions"][0]
        assert excl["exclusion_id"] == "EXCL-PILOT-01"
        assert excl["mapping_status"] == "unresolved_source_mapping"
        assert excl["rows_api_revision_pinned"] is False
        assert len(excl["samples"]) == 20
        # Đảm bảo mỗi mẫu có summary_fingerprint_hash
        for s in excl["samples"]:
            assert "summary_fingerprint_hash" in s
            assert len(s["summary_fingerprint_hash"]) == 64

    def test_all_20_pilot_samples_are_blocked_by_default_registry(self):
        """Chứng minh toàn bộ 20 mẫu trong pilot_summary.json đều bị nhận diện và chặn bởi default registry."""
        assert PILOT_SUMMARY_PATH.exists()
        pilot_data = json.loads(PILOT_SUMMARY_PATH.read_text(encoding="utf-8"))
        pilot_rows = pilot_data["rows"]
        assert len(pilot_rows) == 20

        registry = ExclusionRegistry()  # Khởi tạo mặc định

        for row in pilot_rows:
            assert registry.is_excluded(row) is True, f"Mẫu pilot row_idx={row.get('row_idx')} không bị chặn!"

    def test_matching_by_summary_fingerprint_hash(self):
        """Kiểm tra nhận diện mẫu thông qua mã băm fingerprint cấu trúc tóm tắt."""
        registry = ExclusionRegistry()
        pilot_sample = {
            "pilot_row_idx": 0,
            "label": "benign",
            "lang": "en",
            "html_chars": 518982,
            "text_chars": 27006,
            "forms": 2,
            "inputs": 14,
            "password_inputs": 0,
        }
        h = compute_summary_fingerprint_hash(pilot_sample)
        assert registry.is_excluded({"summary_fingerprint_hash": h}) is True
        # Tương thích ngược với khóa sample_content_hash
        assert registry.is_excluded({"sample_content_hash": h}) is True
        # Alias compute_sample_fingerprint_hash cho cùng kết quả
        assert compute_sample_fingerprint_hash(pilot_sample) == h

    def test_benign_non_pilot_samples_pass(self):
        """Mẫu mới không trùng fingerprint với pilot phải được giữ lại bình thường."""
        registry = ExclusionRegistry()
        clean_sample = {
            "label": "benign",
            "lang": "vi",
            "html_chars": 9999999,
            "text_chars": 8888,
            "forms": 1,
            "inputs": 2,
            "password_inputs": 0,
        }
        assert registry.is_excluded(clean_sample) is False

    def test_filter_split_isolates_pilot_samples(self, tmp_path):
        pilot_sample = {
            "pilot_row_idx": 0,
            "label": "benign",
            "lang": "en",
            "html_chars": 518982,
            "text_chars": 27006,
            "forms": 2,
            "inputs": 14,
            "password_inputs": 0,
        }
        clean_sample = {
            "label": "phish",
            "lang": "en",
            "html_chars": 12345,
            "text_chars": 500,
            "forms": 1,
            "inputs": 2,
            "password_inputs": 1,
        }
        reg_file = tmp_path / "registry.json"
        reg_file.write_text(json.dumps({
            "version": "1.1.0",
            "training_blocked": True,
            "exclusions": [
                {
                    "exclusion_id": "EXCL-PILOT-01",
                    "mapping_status": "unresolved",
                    "samples": [pilot_sample]
                }
            ]
        }), encoding="utf-8")
        registry = ExclusionRegistry(reg_file)
        dataset = [pilot_sample, clean_sample]
        kept, excluded = registry.filter_split(dataset)

        assert len(kept) == 1
        assert kept[0] == clean_sample
        assert len(excluded) == 1
        assert excluded[0] == pilot_sample

    def test_assert_no_leakage_raises_on_pilot_entry(self, tmp_path):
        pilot_sample = {
            "pilot_row_idx": 0,
            "label": "benign",
            "lang": "en",
            "html_chars": 518982,
            "text_chars": 27006,
            "forms": 2,
            "inputs": 14,
            "password_inputs": 0,
        }
        reg_file = tmp_path / "registry.json"
        reg_file.write_text(json.dumps({
            "version": "1.1.0",
            "training_blocked": True,
            "exclusions": [
                {
                    "exclusion_id": "EXCL-PILOT-01",
                    "mapping_status": "unresolved",
                    "samples": [pilot_sample]
                }
            ]
        }), encoding="utf-8")
        registry = ExclusionRegistry(reg_file)
        leaked_split = [
            {
                "pilot_row_idx": 0,
                "label": "benign",
                "lang": "en",
                "html_chars": 518982,
                "text_chars": 27006,
                "forms": 2,
                "inputs": 14,
                "password_inputs": 0,
            }
        ]
        with pytest.raises(ValueError, match="RÒ RỈ DỮ LIỆU PHÁT HIỆN"):
            registry.assert_no_leakage("official_test", leaked_split)

        clean_split = [
            {"label": "phish", "lang": "vi", "html_chars": 33333, "text_chars": 111, "forms": 1, "inputs": 1, "password_inputs": 0}
        ]
        registry.assert_no_leakage("official_test", clean_split)

    def test_domain_group_exclusion_multi_part_tld(self, tmp_path):
        import hashlib
        reg_file = tmp_path / "registry.json"
        group_hash = hashlib.sha256("example.co.uk".encode()).hexdigest()
        reg_file.write_text(json.dumps({
            "registry_status": "in_progress",
            "training_blocked": True,
            "exclusions": [{
                "exclusion_id": "TEST-01",
                "mapping_status": "unresolved",
                "samples": [{"group_sha256": group_hash}]
            }]
        }), encoding="utf-8")
        registry = ExclusionRegistry(reg_file)
        # login.example.co.uk phải được gộp đúng vào example.co.uk và bị loại trừ
        assert registry.is_excluded({"url": "https://login.example.co.uk/auth/signin"}) is True
        # other.co.uk không bị gộp nhầm thành co.uk
        assert registry.is_excluded({"url": "https://other.co.uk/page"}) is False

    def test_missing_tldextract_raises_importerror_without_fallback(self, tmp_path, monkeypatch):
        import hashlib
        import builtins
        reg_file = tmp_path / "registry.json"
        group_hash = hashlib.sha256("example.com".encode()).hexdigest()
        reg_file.write_text(json.dumps({
            "registry_status": "in_progress",
            "training_blocked": True,
            "exclusions": [{
                "exclusion_id": "TEST-01",
                "mapping_status": "unresolved",
                "samples": [{"group_sha256": group_hash}]
            }]
        }), encoding="utf-8")
        registry = ExclusionRegistry(reg_file)

        orig_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == "tldextract":
                raise ImportError("No module named 'tldextract'")
            return orig_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        with pytest.raises(ImportError, match="tldextract bắt buộc phải được cài đặt"):
            registry.is_excluded({"url": "https://login.example.com/"})

    @pytest.mark.skipif(
        not (PROJECT_ROOT / "data/restricted/clean_calibration_exclusion_mapping_c_32.json").exists(),
        reason="Yêu cầu tệp dữ liệu hạn chế ngoài Git (clean_calibration_exclusion_mapping_c_32.json). Bỏ qua trên clean checkout.",
    )
    def test_restricted_commitment_round_c_loaded_and_verified(self):
        """Chứng minh lô Đợt C niêm phong cam kết hạn chế ngoài Git được nạp và xác minh toàn vẹn thành công."""
        registry = ExclusionRegistry()
        assert "EXCL-CALIBRATION-CLEAN-BATCH-C-RESTRICTED" in registry._restricted_commitments_loaded
        assert registry._restricted_commitments_loaded["EXCL-CALIBRATION-CLEAN-BATCH-C-RESTRICTED"] is True
        details = registry._restricted_commitments_details["EXCL-CALIBRATION-CLEAN-BATCH-C-RESTRICTED"]
        assert details["verified"] is True
        assert details["samples_count"] == 32
        assert details["commitment_sha256"] == "67326e80b2a6f9cb7356450a31fe15054a1193412a8ed0576ea2972f1801a805"

        # Kiểm tra mẫu từ hồ sơ hạn chế bị chặn trong registry
        mapping_path = PROJECT_ROOT / "data/restricted/clean_calibration_exclusion_mapping_c_32.json"
        if mapping_path.exists():
            mapping_data = json.loads(mapping_path.read_text(encoding="utf-8"))
            first_entry = mapping_data["mapping"][0]
            assert registry.is_excluded({"url_sha256": first_entry["url_sha256"]}) is True
            assert registry.is_excluded({"group_sha256": first_entry["group_sha256"]}) is True

    def test_restricted_commitment_self_contained_fixture_loaded_and_verified(self, tmp_path):
        """Chứng minh cơ chế nạp và thẩm định cam kết kín hoạt động hoàn hảo bằng fixture tự chứa."""
        import hashlib
        dossier_file = tmp_path / "mock_restricted_mapping.json"
        mock_entry = {
            "url_sha256": "aaaa1111222233334444555566667777888899990000aaaabbbbccccddddeeee",
            "group_sha256": "bbbb1111222233334444555566667777888899990000aaaabbbbccccddddeeee",
        }
        dossier_content = json.dumps({"mapping": [mock_entry]}, indent=2)
        dossier_file.write_text(dossier_content, encoding="utf-8")
        commitment_hash = hashlib.sha256(dossier_file.read_bytes()).hexdigest()
        rel_dossier_path = str(dossier_file.resolve()).replace("\\", "/")

        reg_file = tmp_path / "registry.json"
        reg_file.write_text(json.dumps({
            "version": "1.1.0",
            "training_blocked": False,
            "exclusions": [
                {
                    "exclusion_id": "TEST-RESTRICTED-01",
                    "status": "sealed_restricted_commitment",
                    "restricted_dossier_reference": rel_dossier_path,
                    "commitment_sha256": commitment_hash,
                    "n_samples": 1,
                    "mapping_status": "resolved_in_restricted_dossier",
                    "rows_api_revision_pinned": True,
                }
            ]
        }), encoding="utf-8")

        reg = ExclusionRegistry(reg_file)
        assert reg._restricted_commitments_loaded["TEST-RESTRICTED-01"] is True
        assert reg.is_excluded({"url_sha256": mock_entry["url_sha256"]}) is True
        assert reg.is_excluded({"group_sha256": mock_entry["group_sha256"]}) is True
        reg.assert_restricted_commitments_verified()

    def test_restricted_commitment_tamper_detection(self, tmp_path):
        """Kiểm tra cơ chế phát hiện sai lệch mã băm cam kết hạn chế (Tamper Detection)."""
        import hashlib
        fake_dossier = tmp_path / "fake_mapping.json"
        fake_dossier.write_text(json.dumps({"mapping": [{"url_sha256": "abc"}]}), encoding="utf-8")
        rel_path = str(fake_dossier.resolve()).replace("\\", "/")

        fake_reg = tmp_path / "fake_reg.json"
        fake_reg.write_text(json.dumps({
            "registry_status": "in_progress",
            "training_blocked": False,
            "exclusions": [
                {
                    "exclusion_id": "TEST-TAMPER-01",
                    "status": "sealed_restricted_commitment",
                    "restricted_dossier_reference": rel_path,
                    "commitment_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                    "n_samples": 1,
                }
            ]
        }), encoding="utf-8")

        with pytest.raises(RuntimeError, match="LỖI TOÀN VẸN HỒ SƠ HẠN CHẾ"):
            ExclusionRegistry(fake_reg)

    def test_restricted_commitment_missing_file_fails_closed(self, tmp_path):
        """Kiểm tra cơ chế fail-closed khi thiếu hồ sơ loại trừ cam kết hạn chế ngoài Git."""
        fake_reg = tmp_path / "fake_reg_missing.json"
        fake_reg.write_text(json.dumps({
            "registry_status": "in_progress",
            "training_blocked": False,
            "exclusions": [
                {
                    "exclusion_id": "TEST-MISSING-01",
                    "status": "sealed_restricted_commitment",
                    "restricted_dossier_reference": "non_existent_restricted_dossier.json",
                    "commitment_sha256": "67326e80b2a6f9cb7356450a31fe15054a1193412a8ed0576ea2972f1801a805",
                    "n_samples": 32,
                    "mapping_status": "resolved_in_restricted_dossier",
                    "rows_api_revision_pinned": True,
                },
                {
                    "exclusion_id": "TEST-PUBLIC-01",
                    "mapping_status": "resolved",
                    "rows_api_revision_pinned": True,
                    "samples": [{"url_sha256": "1234567890abcdef"}]
                }
            ]
        }), encoding="utf-8")

        reg = ExclusionRegistry(fake_reg)
        assert reg._restricted_commitments_loaded["TEST-MISSING-01"] is False

        with pytest.raises(RuntimeError, match="LỆNH CHẶN FAIL-CLOSED"):
            reg.assert_training_allowed()

        with pytest.raises(RuntimeError, match="LỆNH CHẶN FAIL-CLOSED"):
            reg.assert_restricted_commitments_verified()


class TestFailClosedPipelinePathsRegression:
    """Bộ kiểm thử hồi quy trực tiếp cho chỉ đạo của Lead D (2026-10-28):
    Kiểm tra fail-closed trên từng đường: filter_split, assert_no_leakage,
    assert_training_allowed, join_verified_labels_and_filter_eligible và generate_splits.py
    với 3 trạng thái: (1) Hồ sơ hợp lệ, (2) Thiếu tệp hồ sơ, (3) Sai lệch mã băm (tampered).
    """

    @pytest.fixture
    def setup_pipeline_env(self, tmp_path):
        import hashlib
        # 1. Tạo tệp hồ sơ hạn chế mẫu
        dossier_file = tmp_path / "mock_restricted_mapping.json"
        mock_restricted_url = "https://restricted-candidate.org/login"
        mock_restricted_group = "domain:restricted-candidate.org"
        mock_restricted_entry = {
            "entry_id": "EXCL-TEST-RESTRICTED-001",
            "url_sha256": hashlib.sha256(mock_restricted_url.encode()).hexdigest(),
            "group_sha256": hashlib.sha256(mock_restricted_group.encode()).hexdigest(),
        }
        dossier_bytes = json.dumps({"mapping": [mock_restricted_entry]}, indent=2).encode("utf-8")
        dossier_file.write_bytes(dossier_bytes)
        correct_hash = hashlib.sha256(dossier_bytes).hexdigest()
        rel_dossier_path = str(dossier_file.resolve()).replace("\\", "/")

        # 2. Registry hợp lệ
        valid_reg_file = tmp_path / "valid_registry.json"
        valid_reg_file.write_text(json.dumps({
            "version": "1.1.0",
            "training_blocked": False,
            "exclusions": [
                {
                    "exclusion_id": "BATCH-VALID-RESTRICTED",
                    "status": "sealed_restricted_commitment",
                    "restricted_dossier_reference": rel_dossier_path,
                    "commitment_sha256": correct_hash,
                    "n_samples": 1,
                    "mapping_status": "resolved_in_restricted_dossier",
                    "rows_api_revision_pinned": True,
                }
            ]
        }), encoding="utf-8")

        # 3. Registry thiếu tệp hồ sơ (kèm 1 lô công khai để đảm bảo registry hợp lệ về cấu trúc)
        missing_reg_file = tmp_path / "missing_registry.json"
        missing_reg_file.write_text(json.dumps({
            "version": "1.1.0",
            "training_blocked": False,
            "exclusions": [
                {
                    "exclusion_id": "BATCH-PUBLIC-DUMMY",
                    "mapping_status": "resolved",
                    "rows_api_revision_pinned": True,
                    "samples": [{"url_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}]
                },
                {
                    "exclusion_id": "BATCH-MISSING-RESTRICTED",
                    "status": "sealed_restricted_commitment",
                    "restricted_dossier_reference": "non_existent_mapping_file.json",
                    "commitment_sha256": correct_hash,
                    "n_samples": 1,
                    "mapping_status": "resolved_in_restricted_dossier",
                    "rows_api_revision_pinned": True,
                }
            ]
        }), encoding="utf-8")

        # 4. Registry sai lệch mã băm (tampered)
        tampered_reg_file = tmp_path / "tampered_registry.json"
        tampered_reg_file.write_text(json.dumps({
            "version": "1.1.0",
            "training_blocked": False,
            "exclusions": [
                {
                    "exclusion_id": "BATCH-PUBLIC-DUMMY",
                    "mapping_status": "resolved",
                    "rows_api_revision_pinned": True,
                    "samples": [{"url_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}]
                },
                {
                    "exclusion_id": "BATCH-TAMPERED-RESTRICTED",
                    "status": "sealed_restricted_commitment",
                    "restricted_dossier_reference": rel_dossier_path,
                    "commitment_sha256": "bad0000000000000000000000000000000000000000000000000000000000000",
                    "n_samples": 1,
                    "mapping_status": "resolved_in_restricted_dossier",
                    "rows_api_revision_pinned": True,
                }
            ]
        }), encoding="utf-8")

        # 5. Dữ liệu mẫu (mẫu sạch và mẫu thuộc danh mục loại trừ)
        clean_url = "https://clean-example.com/index"
        clean_sample = {
            "sample_id": "PP-000-R000001",
            "source_id": "phreshphish",
            "url": clean_url,
            "raw_url": clean_url,
            "normalized_url": clean_url,
            "html_sha256": "1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
            "url_sha256": hashlib.sha256(clean_url.encode()).hexdigest(),
            "group_id": "domain:clean-example.com",
            "group_sha256": hashlib.sha256(b"domain:clean-example.com").hexdigest(),
            "class_label": "benign",
            "collected_at": "2025-01-15",
            "is_valid_url": True,
            "date_status": "valid",
            "exclusion_reason": None,
        }
        restricted_sample = {
            "sample_id": "PP-000-R000002",
            "source_id": "phreshphish",
            "url": mock_restricted_url,
            "raw_url": mock_restricted_url,
            "normalized_url": mock_restricted_url,
            "html_sha256": "5555222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
            "url_sha256": mock_restricted_entry["url_sha256"],
            "group_id": mock_restricted_group,
            "group_sha256": mock_restricted_entry["group_sha256"],
            "class_label": "phishing",
            "collected_at": "2025-01-16",
            "is_valid_url": True,
            "date_status": "valid",
            "exclusion_reason": None,
        }

        # 6. Tệp JSONL phục vụ generate_splits.py
        records = [
            {
                "sample_id": f"PP-000-R{i:06d}",
                "source_id": "phreshphish",
                "url": f"https://real-domain-{i}.com/path",
                "class_label": "phishing" if i % 2 == 0 else "benign",
                "collected_at": f"2025-01-{(i % 25) + 1:02d}",
            }
            for i in range(1, 31)
        ]
        corpus_file = tmp_path / "real_corpus.jsonl"
        corpus_file.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")

        return {
            "valid_reg_file": valid_reg_file,
            "missing_reg_file": missing_reg_file,
            "tampered_reg_file": tampered_reg_file,
            "clean_sample": clean_sample,
            "restricted_sample": restricted_sample,
            "corpus_file": corpus_file,
            "tmp_path": tmp_path,
        }

    # 1. Đường lọc filter_split
    def test_filter_split_path_with_valid_dossier(self, setup_pipeline_env):
        env = setup_pipeline_env
        reg = ExclusionRegistry(env["valid_reg_file"])
        kept, excluded = reg.filter_split([env["clean_sample"], env["restricted_sample"]])
        assert len(kept) == 1
        assert kept[0]["sample_id"] == env["clean_sample"]["sample_id"]
        assert len(excluded) == 1
        assert excluded[0]["sample_id"] == env["restricted_sample"]["sample_id"]

    def test_filter_split_path_with_missing_dossier_fails_closed(self, setup_pipeline_env):
        env = setup_pipeline_env
        reg = ExclusionRegistry(env["missing_reg_file"])
        with pytest.raises(RuntimeError, match="LỆNH CHẶN FAIL-CLOSED"):
            reg.filter_split([env["clean_sample"]])

    def test_filter_split_path_with_tampered_hash_fails_closed(self, setup_pipeline_env):
        env = setup_pipeline_env
        with pytest.raises(RuntimeError, match="LỖI TOÀN VẸN HỒ SƠ HẠN CHẾ"):
            ExclusionRegistry(env["tampered_reg_file"])

    # 2. Đường kiểm tra rò rỉ assert_no_leakage
    def test_assert_no_leakage_path_with_valid_dossier(self, setup_pipeline_env):
        env = setup_pipeline_env
        reg = ExclusionRegistry(env["valid_reg_file"])
        # Tập sạch không ném ngoại lệ
        reg.assert_no_leakage("train_clean", [env["clean_sample"]])
        # Tập có mẫu lọt ném ValueError rò rỉ
        with pytest.raises(ValueError, match="RÒ RỈ DỮ LIỆU PHÁT HIỆN"):
            reg.assert_no_leakage("train_leaked", [env["restricted_sample"]])

    def test_assert_no_leakage_path_with_missing_dossier_fails_closed(self, setup_pipeline_env):
        env = setup_pipeline_env
        reg = ExclusionRegistry(env["missing_reg_file"])
        with pytest.raises(RuntimeError, match="LỆNH CHẶN FAIL-CLOSED"):
            reg.assert_no_leakage("train", [env["clean_sample"]])

    def test_assert_no_leakage_path_with_tampered_hash_fails_closed(self, setup_pipeline_env):
        env = setup_pipeline_env
        with pytest.raises(RuntimeError, match="LỖI TOÀN VẸN HỒ SƠ HẠN CHẾ"):
            ExclusionRegistry(env["tampered_reg_file"])

    # 3. Đường kiểm tra huấn luyện assert_training_allowed
    def test_assert_training_allowed_path_with_valid_dossier(self, setup_pipeline_env):
        env = setup_pipeline_env
        reg = ExclusionRegistry(env["valid_reg_file"])
        reg.assert_training_allowed()

    def test_assert_training_allowed_path_with_missing_dossier_fails_closed(self, setup_pipeline_env):
        env = setup_pipeline_env
        reg = ExclusionRegistry(env["missing_reg_file"])
        with pytest.raises(RuntimeError, match="LỆNH CHẶN FAIL-CLOSED"):
            reg.assert_training_allowed()

    def test_assert_training_allowed_path_with_tampered_hash_fails_closed(self, setup_pipeline_env):
        env = setup_pipeline_env
        with pytest.raises(RuntimeError, match="LỖI TOÀN VẸN HỒ SƠ HẠN CHẾ"):
            ExclusionRegistry(env["tampered_reg_file"])

    # 4. Đường chuẩn bị fit / join nhãn kiểm chứng
    def test_join_verified_labels_path_with_valid_dossier(self, setup_pipeline_env):
        from phishing.data.loader import join_verified_labels_and_filter_eligible
        env = setup_pipeline_env
        reg = ExclusionRegistry(env["valid_reg_file"])
        vault = {
            env["clean_sample"]["sample_id"]: {
                "sample_id": env["clean_sample"]["sample_id"],
                "class_label": "benign",
                "label_status": "verified_binary",
                "html_sha256": env["clean_sample"]["html_sha256"],
                "raw_url": env["clean_sample"]["url"],
                "verification_method": "expert_pass",
                "verified_by": "expert",
                "verification_evidence": "audit_log",
            },
            env["restricted_sample"]["sample_id"]: {
                "sample_id": env["restricted_sample"]["sample_id"],
                "class_label": "phishing",
                "label_status": "verified_binary",
                "html_sha256": env["restricted_sample"]["html_sha256"],
                "raw_url": env["restricted_sample"]["url"],
                "verification_method": "expert_pass",
                "verified_by": "expert",
                "verification_evidence": "audit_log",
            },
        }
        joined = join_verified_labels_and_filter_eligible(
            [env["clean_sample"], env["restricted_sample"]],
            vault,
            exclusion_registry=reg,
        )
        assert len(joined) == 1
        assert joined[0]["sample_id"] == env["clean_sample"]["sample_id"]

    def test_join_verified_labels_path_with_missing_dossier_fails_closed(self, setup_pipeline_env):
        from phishing.data.loader import join_verified_labels_and_filter_eligible
        env = setup_pipeline_env
        reg = ExclusionRegistry(env["missing_reg_file"])
        vault = {env["clean_sample"]["sample_id"]: {"verified_label": "benign"}}
        with pytest.raises(RuntimeError, match="LỆNH CHẶN FAIL-CLOSED"):
            join_verified_labels_and_filter_eligible([env["clean_sample"]], vault, exclusion_registry=reg)

    def test_join_verified_labels_path_with_tampered_hash_fails_closed(self, setup_pipeline_env):
        env = setup_pipeline_env
        with pytest.raises(RuntimeError, match="LỖI TOÀN VẸN HỒ SƠ HẠN CHẾ"):
            ExclusionRegistry(env["tampered_reg_file"])

    # 5. Đường CLI generate_splits.py
    def test_generate_splits_path_with_valid_dossier(self, setup_pipeline_env):
        from scripts.data import generate_splits
        env = setup_pipeline_env
        out_dir = env["tmp_path"] / "splits_valid_run"
        exit_code = generate_splits.main([
            "--input", str(env["corpus_file"]),
            "--output-dir", str(out_dir),
            "--exclusion-registry", str(env["valid_reg_file"]),
            "--is-real-data",
            "-k", "3",
            "--seeds", "42",
        ])
        assert exit_code == 0
        manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["verified_robust"] is True
        assert manifest["anti_leakage_status"] == "verified_robust"

    def test_generate_splits_path_with_missing_dossier_fails_closed(self, setup_pipeline_env, monkeypatch):
        import io
        import contextlib
        from scripts.data import generate_splits
        env = setup_pipeline_env
        out_dir = env["tmp_path"] / "splits_missing_run"
        buf_err = io.StringIO()
        with contextlib.redirect_stderr(buf_err):
            exit_code = generate_splits.main([
                "--input", str(env["corpus_file"]),
                "--output-dir", str(out_dir),
                "--exclusion-registry", str(env["missing_reg_file"]),
                "--is-real-data",
                "-k", "3",
                "--seeds", "42",
            ])
        assert exit_code == 1
        assert "LỆNH CHẶN FAIL-CLOSED" in buf_err.getvalue()

    def test_generate_splits_path_with_tampered_hash_fails_closed(self, setup_pipeline_env):
        import io
        import contextlib
        from scripts.data import generate_splits
        env = setup_pipeline_env
        out_dir = env["tmp_path"] / "splits_tampered_run"
        buf_err = io.StringIO()
        with contextlib.redirect_stderr(buf_err):
            exit_code = generate_splits.main([
                "--input", str(env["corpus_file"]),
                "--output-dir", str(out_dir),
                "--exclusion-registry", str(env["tampered_reg_file"]),
                "--is-real-data",
                "-k", "3",
                "--seeds", "42",
            ])
        assert exit_code == 1
        assert "LỖI TOÀN VẸN HỒ SƠ HẠN CHẾ" in buf_err.getvalue()

    def test_generate_splits_probe_row_51_real_sample_fails_closed(self, setup_pipeline_env):
        """Lead D probe: 50 bản ghi đầu là fixture, bản ghi thứ 51 có ID PP-real-last.

        Khi thiếu hồ sơ loại trừ hạn chế, CLI KHÔNG được phép nhận diện nhầm là fixture,
        phải fail-closed thoát mã 1 và không công bố split artifacts verified_robust.
        """
        import io
        import contextlib
        from scripts.data import generate_splits
        env = setup_pipeline_env
        tmp_path = env["tmp_path"]

        # Tạo 51 bản ghi: 50 fixture đầu + bản ghi 51 là PP-real-last
        recs = [
            {
                "sample_id": f"S{i}",
                "url": f"https://synthetic-domain-{i}.com/page",
                "class_label": "phishing" if i % 2 == 0 else "benign",
                "collected_at": f"2025-01-{(i % 25) + 1:02d}",
            }
            for i in range(50)
        ]
        recs.append({
            "sample_id": "PP-real-last",
            "url": "https://real-domain-last.com/page",
            "class_label": "phishing",
            "collected_at": "2025-01-26",
        })

        probe_file = tmp_path / "probe_51_records.jsonl"
        probe_file.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
        out_dir = tmp_path / "splits_probe_51_out"

        buf_err = io.StringIO()
        with contextlib.redirect_stderr(buf_err):
            exit_code = generate_splits.main([
                "--input", str(probe_file),
                "--output-dir", str(out_dir),
                "--exclusion-registry", str(env["missing_reg_file"]),
                "-k", "3",
                "--seeds", "42",
            ])

        assert exit_code == 1, f"Probe thất bại: CLI thoát mã 0 thay vì fail-closed 1. Stderr: {buf_err.getvalue()}"
        assert "LỆNH CHẶN FAIL-CLOSED" in buf_err.getvalue()
        # Không được phép sinh manifest verified_robust
        manifest_file = out_dir / "manifest.json"
        if manifest_file.exists():
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            assert manifest.get("verified_robust") is not True

    def test_generate_splits_generic_id_with_real_metadata_fails_closed(self, setup_pipeline_env):
        """Lead D ca 2: ID không mang tiền tố (GEN_01) nhưng metadata nguồn (source_id / locator) là thật.

        CLI phải phát hiện metadata nguồn thật và áp dụng chế độ dữ liệu thật, fail-closed thoát mã 1.
        """
        import io
        import contextlib
        from scripts.data import generate_splits
        env = setup_pipeline_env
        tmp_path = env["tmp_path"]

        recs = [
            {
                "sample_id": f"GEN_{i:03d}",
                "source_id": "phreshphish",
                "locator": {"source_id": "phreshphish", "parquet_path": "train-000.parquet", "row_offset": i},
                "url": f"https://real-meta-domain-{i}.com/page",
                "class_label": "phishing" if i % 2 == 0 else "benign",
                "collected_at": f"2025-01-{(i % 25) + 1:02d}",
            }
            for i in range(20)
        ]

        in_file = tmp_path / "generic_id_real_meta.jsonl"
        in_file.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
        out_dir = tmp_path / "splits_generic_id_out"

        buf_err = io.StringIO()
        with contextlib.redirect_stderr(buf_err):
            exit_code = generate_splits.main([
                "--input", str(in_file),
                "--output-dir", str(out_dir),
                "--exclusion-registry", str(env["missing_reg_file"]),
                "-k", "3",
                "--seeds", "42",
            ])

        assert exit_code == 1
        assert "LỆNH CHẶN FAIL-CLOSED" in buf_err.getvalue()
        assert not (out_dir / "manifest.json").exists()

    def test_generate_splits_mixed_fixture_real_in_fixture_mode_fails_closed(self, setup_pipeline_env):
        """Lead D ca 3: Tệp trộn fixture-thật nhưng người dùng cố ý khai báo --fixture-mode.

        CLI phải từ chối fail-closed với thông báo lỗi rò rỉ dữ liệu thật vào chế độ fixture.
        """
        import io
        import contextlib
        from scripts.data import generate_splits
        env = setup_pipeline_env
        tmp_path = env["tmp_path"]

        recs = [
            {
                "sample_id": f"SYN_{i}",
                "url": f"https://synthetic-{i}.com/page",
                "class_label": "phishing" if i % 2 == 0 else "benign",
                "collected_at": f"2025-01-{(i % 25) + 1:02d}",
            }
            for i in range(10)
        ]
        recs.append({
            "sample_id": "PP-000-MIXED-01",
            "url": "https://mixed-domain.com/login",
            "class_label": "phishing",
            "collected_at": "2025-01-15",
        })

        mixed_file = tmp_path / "mixed_fixture_real.jsonl"
        mixed_file.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
        out_dir = tmp_path / "splits_mixed_out"

        buf_err = io.StringIO()
        with contextlib.redirect_stderr(buf_err):
            exit_code = generate_splits.main([
                "--input", str(mixed_file),
                "--output-dir", str(out_dir),
                "--fixture-mode",
                "-k", "3",
                "--seeds", "42",
            ])

        assert exit_code == 1
        err_msg = buf_err.getvalue()
        assert "LỖI RÒ RỈ DỮ LIỆU THẬT VÀO CHẾ ĐỘ FIXTURE" in err_msg
        assert not (out_dir / "manifest.json").exists()

    def test_generate_splits_valid_fixture_succeeds_without_verified_robust(self, setup_pipeline_env):
        """Lead D ca 4: Fixture hợp lệ 100% dữ liệu mô phỏng chạy qua --fixture-mode.

        CLI cho phép chạy thử nghiệm kiểm toán cấu trúc split nhưng KHÔNG xuất verified_robust=true.
        """
        import io
        import contextlib
        from scripts.data import generate_splits
        env = setup_pipeline_env
        tmp_path = env["tmp_path"]

        recs = [
            {
                "sample_id": f"FIXTURE_{i}",
                "url": f"https://fixture-domain-{i}.com/page",
                "class_label": "phishing" if i % 2 == 0 else "benign",
                "collected_at": f"2025-01-{(i % 25) + 1:02d}",
            }
            for i in range(20)
        ]

        fix_file = tmp_path / "valid_fixture.jsonl"
        fix_file.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
        out_dir = tmp_path / "splits_valid_fixture_out"

        buf_err = io.StringIO()
        with contextlib.redirect_stderr(buf_err):
            exit_code = generate_splits.main([
                "--input", str(fix_file),
                "--output-dir", str(out_dir),
                "--fixture-mode",
                "-k", "3",
                "--seeds", "42",
            ])

        assert exit_code == 0
        manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["verified_robust"] is False
        assert manifest["usable_for_training"] is False
        assert manifest["anti_leakage_status"] == "synthetic_fixture_test_mode"

        # Từng fold cũng phải được đánh dấu is_usable=False
        splits_data = json.loads((out_dir / "grouped_5fold_splits.json").read_text(encoding="utf-8"))
        for seed_val, folds in splits_data["splits_by_seed"].items():
            for fold in folds:
                assert fold["is_usable"] is False
                assert "không được phép dùng để huấn luyện" in fold.get("unusable_reason", "")

    def test_generate_splits_excluded_sample_leak_detected_fails_closed(self, setup_pipeline_env):
        """Lead D ca 8: Dữ liệu thật chứa mẫu thuộc danh mục loại trừ (Exclusion Registry).

        CLI phải phát hiện rò rỉ mẫu loại trừ, fail-closed thoát mã 1 và không xuất artifacts.
        """
        import io
        import contextlib
        from scripts.data import generate_splits
        env = setup_pipeline_env
        tmp_path = env["tmp_path"]

        # Tập dữ liệu chứa mẫu bị loại trừ
        recs = [
            {
                "sample_id": f"PP-000-S{i:05d}",
                "source_id": "phreshphish",
                "url": f"https://real-ok-domain-{i}.com/page",
                "class_label": "phishing" if i % 2 == 0 else "benign",
                "collected_at": f"2025-01-{(i % 25) + 1:02d}",
            }
            for i in range(15)
        ]
        # Chèn mẫu nằm trong dossier loại trừ
        recs.append(env["restricted_sample"])

        leak_file = tmp_path / "corpus_with_leak.jsonl"
        leak_file.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
        out_dir = tmp_path / "splits_leak_detected_out"

        buf_err = io.StringIO()
        with contextlib.redirect_stderr(buf_err):
            exit_code = generate_splits.main([
                "--input", str(leak_file),
                "--output-dir", str(out_dir),
                "--exclusion-registry", str(env["valid_reg_file"]),
                "-k", "3",
                "--seeds", "42",
            ])

        assert exit_code == 1
        assert "LỖI RÒ RỈ DỮ LIỆU ĐẦU VÀO SPLITS" in buf_err.getvalue()
        assert not (out_dir / "manifest.json").exists()

    def test_generate_splits_allow_unverified_commitments_is_audit_only(self, setup_pipeline_env):
        """Lead D ca bổ sung: Cờ --allow-unverified-commitments cho phép audit nhưng KHÔNG xuất verified_robust.

        Mọi fold phải mang is_usable=False và usable_for_training=False.
        """
        import io
        import contextlib
        from scripts.data import generate_splits
        env = setup_pipeline_env
        tmp_path = env["tmp_path"]

        out_dir = tmp_path / "splits_audit_only_out"
        buf_err = io.StringIO()
        with contextlib.redirect_stderr(buf_err):
            exit_code = generate_splits.main([
                "--input", str(env["corpus_file"]),
                "--output-dir", str(out_dir),
                "--exclusion-registry", str(env["missing_reg_file"]),
                "--allow-unverified-commitments",
                "-k", "3",
                "--seeds", "42",
            ])

        assert exit_code == 0
        manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["verified_robust"] is False
        assert manifest["usable_for_training"] is False
        assert manifest["anti_leakage_status"] == "audit_only_unverified_commitments"

        splits_data = json.loads((out_dir / "grouped_5fold_splits.json").read_text(encoding="utf-8"))
        for seed_val, folds in splits_data["splits_by_seed"].items():
            for fold in folds:
                assert fold["is_usable"] is False
                assert "chỉ dùng cho kiểm toán (audit-only)" in fold.get("unusable_reason", "")

