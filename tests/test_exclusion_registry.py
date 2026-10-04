"""Bộ kiểm thử cho Exclusion Registry và bộ lọc chống rò rỉ dữ liệu (Task DATA-01).

Kiểm tra:
1. Đọc và xác thực cấu trúc của data/exclusion_registry.json.
2. Chứng minh 20 mẫu pilot đã kiểm tra sơ bộ bị chặn 100% khỏi tập train/val/test.
3. Kiểm tra tính năng lọc tách biệt (kept vs excluded).
4. Kiểm tra ném lỗi phát hiện rò rỉ (assert_no_leakage).
"""

import json
from pathlib import Path
import pytest

from phishing.data.exclusion import ExclusionRegistry

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PILOT_SUMMARY_PATH = PROJECT_ROOT / "data" / "source_audit" / "phreshphish" / "pilot_summary.json"
EXCLUSION_PATH = PROJECT_ROOT / "data" / "exclusion_registry.json"


class TestExclusionRegistry:
    """Kiểm tra sự cô lập triệt để của các mẫu pilot khỏi dữ liệu thực nghiệm."""

    def test_registry_file_structure(self):
        assert EXCLUSION_PATH.exists()
        data = json.loads(EXCLUSION_PATH.read_text(encoding="utf-8"))
        assert data["version"] == "1.1.0"
        assert data["registry_status"] == "in_progress_unresolved"
        assert data["total_excluded_samples"] == 20
        assert len(data["exclusions"]) >= 1

        excl = data["exclusions"][0]
        assert excl["exclusion_id"] == "EXCL-PILOT-01"
        assert excl["mapping_status"] == "unresolved_source_mapping"
        assert excl["rows_api_revision_pinned"] is False
        assert len(excl["samples"]) == 20

    def test_all_20_pilot_samples_are_blocked(self):
        """Chứng minh toàn bộ 20 mẫu trong pilot_summary.json đều bị nhận diện và chặn."""
        assert PILOT_SUMMARY_PATH.exists()
        pilot_data = json.loads(PILOT_SUMMARY_PATH.read_text(encoding="utf-8"))
        pilot_rows = pilot_data["rows"]
        assert len(pilot_rows) == 20

        registry = ExclusionRegistry(EXCLUSION_PATH)

        for row in pilot_rows:
            assert registry.is_excluded(row) is True, f"Mẫu pilot row_idx={row.get('row_idx')} không bị chặn!"

    def test_benign_non_pilot_samples_pass(self):
        """Mẫu mới không trùng fingerprint với pilot phải được giữ lại bình thường."""
        registry = ExclusionRegistry(EXCLUSION_PATH)
        clean_sample = {
            "label": "benign",
            "lang": "vi",
            "html_chars": 9999999,  # Khác biệt
            "text_chars": 8888,
            "forms": 1,
            "inputs": 2,
            "password_inputs": 0,
        }
        assert registry.is_excluded(clean_sample) is False

    def test_filter_split_isolates_pilot_samples(self):
        registry = ExclusionRegistry(EXCLUSION_PATH)
        pilot_sample = {
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
        registry = ExclusionRegistry(EXCLUSION_PATH)
        leaked_split = [
            {"label": "benign", "lang": "en", "html_chars": 518982, "text_chars": 27006, "forms": 2, "inputs": 14, "password_inputs": 0}
        ]
        with pytest.raises(ValueError, match="RÒ RỈ DỮ LIỆU PHÁT HIỆN"):
            registry.assert_no_leakage("official_test", leaked_split)

        clean_split = [
            {"label": "phish", "lang": "vi", "html_chars": 33333, "text_chars": 111, "forms": 1, "inputs": 1, "password_inputs": 0}
        ]
        # Không ném lỗi
        registry.assert_no_leakage("official_test", clean_split)
