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

    def test_training_blocked_even_if_flag_is_false_when_mapping_unresolved(self):
        """Dù cờ training_blocked bị đổi thành False, hàm assert_training_allowed vẫn phải chặn nếu còn lô unresolved."""
        registry = ExclusionRegistry()
        # Giả lập can thiệp cờ sai quy chuẩn
        registry.training_blocked = False
        with pytest.raises(
            RuntimeError,
            match="Lô loại trừ 'EXCL-PILOT-01' có trạng thái mapping='unresolved_source_mapping'",
        ):
            registry.assert_training_allowed()

    def test_training_allowed_when_all_batches_resolved_and_pinned(self):
        """Khi tất cả các lô đã được resolved, rows_api_revision_pinned=True và training_blocked=False, cho phép huấn luyện."""
        registry = ExclusionRegistry()
        registry.training_blocked = False
        registry._raw_exclusions = [
            {
                "exclusion_id": "EXCL-PILOT-01",
                "mapping_status": "resolved",
                "rows_api_revision_pinned": True,
            }
        ]
        # Không được ném ngoại lệ
        registry.assert_training_allowed()

    def test_registry_file_structure(self):
        assert EXCLUSION_PATH.exists()
        data = json.loads(EXCLUSION_PATH.read_text(encoding="utf-8"))
        assert data["version"] == "1.1.0"
        assert data["registry_status"] == "in_progress_unresolved"
        assert data["total_excluded_samples"] == 20
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

    def test_filter_split_isolates_pilot_samples(self):
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
        clean_sample = {
            "label": "phish",
            "lang": "en",
            "html_chars": 12345,
            "text_chars": 500,
            "forms": 1,
            "inputs": 2,
            "password_inputs": 1,
        }
        dataset = [pilot_sample, clean_sample]
        kept, excluded = registry.filter_split(dataset)

        assert len(kept) == 1
        assert kept[0] == clean_sample
        assert len(excluded) == 1
        assert excluded[0] == pilot_sample

    def test_assert_no_leakage_raises_on_pilot_entry(self):
        registry = ExclusionRegistry()
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
