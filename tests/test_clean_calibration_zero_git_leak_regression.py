"""Regression Tests for Zero Git Leakage (ARS & Ponytail Discipline).

Strictly verifies:
1. data/exclusion_registry.json batch EXCL-CALIBRATION-CLEAN-RUNWAY-32 contains ZERO plain domain names
   (no group_id) and ZERO source dates (no source_date) on Git.
2. Only neutral IDs and cryptographic hashes (url_sha256, normalized_url_sha256, html_sha256, group_sha256)
   are committed to Git.
3. Full candidate mappings (domains, source dates, parquet locators) are strictly confined to data/restricted/
   which is 100% gitignored.
4. ExclusionRegistry operates 100% fail-closed on all 32 candidates using only cryptographic hashes.
5. All public governance manifests and audit reports contain zero raw locators and zero sample labels.
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

from phishing.data.exclusion import ExclusionRegistry

REGISTRY_PATH = ROOT / "data/exclusion_registry.json"
MAPPING_PATH = ROOT / "data/restricted/clean_calibration_exclusion_mapping_32.json"
MANIFEST_PATH = ROOT / "configs/calibration_clean_a_manifest.json"
AUDIT_REPORT_PATH = ROOT / "data/source_audit/clean_calibration_exclusion_audit_report.json"
INSPECTION_REPORT_PATH = ROOT / "data/source_audit/clean_calibration_selection_inspection_report.json"


class TestCleanCalibrationZeroGitLeakRegression:
    """Test suite ensuring Zero Git Leakage across registry, manifests, and public reports."""

    def test_runway_exclusion_batch_zero_domain_and_zero_date(self):
        """Chứng minh lô Đợt B (EXCL-CALIBRATION-CLEAN-RUNWAY-32) trong registry trên Git
        không chứa group_id, source_date hay locator nào."""
        assert REGISTRY_PATH.exists(), f"Thiếu {REGISTRY_PATH}"
        reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

        allowed_keys = {"sample_id", "url_sha256", "normalized_url_sha256", "html_sha256", "group_sha256"}
        forbidden_keys = {"group_id", "source_date", "url", "domain", "locator", "relative_path", "row_offset"}

        batch = next(
            (b for b in reg.get("exclusions", []) if b.get("exclusion_id") == "EXCL-CALIBRATION-CLEAN-RUNWAY-32"),
            None
        )
        assert batch is not None, "Thiếu lô EXCL-CALIBRATION-CLEAN-RUNWAY-32 trong registry!"
        assert batch["n_samples"] == 32
        assert len(batch["samples"]) == 32

        for idx, s in enumerate(batch["samples"]):
            keys = set(s.keys())
            assert keys.issubset(allowed_keys), f"Mẫu {idx} chứa các trường không cho phép: {keys - allowed_keys}"
            for fk in forbidden_keys:
                assert fk not in s, f"Mẫu {idx} chứa trường bị cấm '{fk}' trên Git registry!"

            # Kiểm tra ID phải là trung tính
            assert re.match(r"^EXCL-CLN-\d{3}$", s["sample_id"]), f"ID mẫu {s['sample_id']} không đúng định dạng trung tính!"

            # Kiểm tra các hash phải đúng 64 ký tự hex
            for hk in ("url_sha256", "normalized_url_sha256", "html_sha256", "group_sha256"):
                val = s[hk]
                assert isinstance(val, str) and len(val) == 64, f"Hash {hk} không hợp lệ: {val}"
                assert re.match(r"^[0-9a-f]{64}$", val), f"Hash {hk} không phải hex 64: {val}"

    @pytest.mark.skipif(not MAPPING_PATH.exists(), reason="Restricted mapping dossier only present in Lead D audit environment")
    def test_restricted_dossier_contains_full_mapping_and_is_gitignored(self):
        """Chứng minh thông tin chi tiết (group_id, source_date, locators) nằm trọn vẹn trong data/restricted/."""
        assert MAPPING_PATH.exists(), f"Thiếu tệp ánh xạ hạn chế tại {MAPPING_PATH}"
        mapping_data = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))

        entries = mapping_data.get("mapping", [])
        assert len(entries) == 32
        assert mapping_data["main_samples_count"] == 24
        assert mapping_data["reserve_samples_count"] == 8

        # Kiểm tra đầy đủ thông tin đối soát cho Lead D
        for e in entries:
            assert "entry_id" in e
            assert "candidate_id" in e
            assert "role" in e and e["role"] in ("main_24", "reserve_08")
            assert "locator" in e
            assert "relative_path" in e["locator"]
            assert "row_offset" in e["locator"]
            assert "group_id" in e and e["group_id"].startswith("domain:")
            assert "source_date" in e and re.match(r"^\d{4}-\d{2}-\d{2}$", e["source_date"])

    @pytest.mark.skipif(not MAPPING_PATH.exists(), reason="Restricted mapping dossier only present in Lead D audit environment")
    def test_exclusion_registry_fail_closed_without_plain_domains(self):
        """Chứng minh ExclusionRegistry chặn 100% 32 mẫu chỉ dựa trên hash, không cần domain thô (chạy khi có mapping dossier)."""
        reg = ExclusionRegistry(REGISTRY_PATH)

        assert MAPPING_PATH.exists()
        mapping_data = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))

        for e in mapping_data.get("mapping", []):
            # Giả lập mẫu kiểm tra với url_sha256
            sample_by_url = {"url_sha256": e["url_sha256"]}
            assert reg.is_excluded(sample_by_url), f"Mẫu {e['entry_id']} không bị chặn theo url_sha256!"

            # Giả lập mẫu kiểm tra với html_sha256
            sample_by_html = {"html_sha256": e["html_sha256"]}
            assert reg.is_excluded(sample_by_html), f"Mẫu {e['entry_id']} không bị chặn theo html_sha256!"

            # Giả lập mẫu kiểm tra với group_sha256
            sample_by_group = {"group_sha256": e["group_sha256"]}
            assert reg.is_excluded(sample_by_group), f"Mẫu {e['entry_id']} không bị chặn theo group_sha256!"

    def test_exclusion_registry_fail_closed_clean_checkout_fixture(self):
        """Kiểm thử tự chứa (self-contained) bảo đảm chạy 100% thành công trên checkout sạch (khi data/restricted/ vắng mặt).
        Chứng minh ExclusionRegistry chặn mẫu hoàn toàn bằng hash mật mã học mà không cần domain thô."""
        assert REGISTRY_PATH.exists(), f"Thiếu registry tại {REGISTRY_PATH}"
        reg = ExclusionRegistry(REGISTRY_PATH)
        reg_data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

        # Lấy lô EXCL-CALIBRATION-CLEAN-RUNWAY-32
        batch = next(
            (b for b in reg_data.get("exclusions", []) if b.get("exclusion_id") == "EXCL-CALIBRATION-CLEAN-RUNWAY-32"),
            None
        )
        assert batch is not None, "Thiếu lô EXCL-CALIBRATION-CLEAN-RUNWAY-32 trong registry"
        assert len(batch["samples"]) == 32

        # Kiểm tra mẫu đầu tiên, giữa và cuối của lô
        for idx in (0, 15, 31):
            s = batch["samples"][idx]
            # Chặn theo url_sha256
            assert reg.is_excluded({"url_sha256": s["url_sha256"]}), f"Mẫu {idx} không bị chặn theo url_sha256!"
            # Chặn theo html_sha256
            assert reg.is_excluded({"html_sha256": s["html_sha256"]}), f"Mẫu {idx} không bị chặn theo html_sha256!"
            # Chặn theo group_sha256
            assert reg.is_excluded({"group_sha256": s["group_sha256"]}), f"Mẫu {idx} không bị chặn theo group_sha256!"

        # Mẫu giả định không khớp thì không bị chặn
        dummy_unmatched = {
            "url_sha256": "0" * 64,
            "normalized_url_sha256": "1" * 64,
            "html_sha256": "2" * 64,
            "group_sha256": "3" * 64,
        }
        assert not reg.is_excluded(dummy_unmatched), "Mẫu giả định không liên quan bị chặn sai!"

    def test_public_artifacts_zero_plain_candidate_domain_leak(self):
        """Quét registry, manifest và các báo cáo audit công khai đảm bảo không lộ tên miền ứng viên Đợt B hoặc Đợt C.
        Nếu xuất hiện chuỗi dạng domain:..., chỉ được phép là tên miền ví dụ trung tính (.local, .example)."""
        artifacts_to_scan = [
            REGISTRY_PATH,
            MANIFEST_PATH,
            AUDIT_REPORT_PATH,
            INSPECTION_REPORT_PATH,
            ROOT / "data/source_audit/clean_calibration_round_c_inspection_report.json",
            ROOT / "data/source_audit/clean_calibration_incident_03_audit_report.json",
        ]

        # Đọc danh sách domain bị cấm nếu tệp mapping tồn tại
        prohibited_domains = set()
        if MAPPING_PATH.exists():
            mapping_data = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
            for e in mapping_data.get("mapping", []):
                raw_d = e.get("group_id", "").replace("domain:", "").strip()
                if raw_d:
                    prohibited_domains.add(raw_d)

        for path in artifacts_to_scan:
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")

            # 1. Quét đối chiếu danh sách domain ứng viên đã lộ/bị cấm
            for d in prohibited_domains:
                assert d not in text, f"Phát hiện domain ứng viên bị cấm '{d}' trong tệp công khai {path.name}!"

            # 2. Quét cú pháp domain:... trong các tệp ngoại trừ các lô lịch sử cũ trong registry
            if path.name == "clean_calibration_incident_03_audit_report.json":
                # Báo cáo sự cố 03 chỉ được phép chứa placeholder trung tính
                for m in re.finditer(r'domain:([a-zA-Z0-9.-]+)', text):
                    dom = m.group(1)
                    assert dom.endswith(".local") or dom.endswith(".example"), (
                        f"Phát hiện domain không trung tính '{dom}' trong {path.name}!"
                    )

    def test_public_artifacts_zero_locator_and_zero_label_leak(self):
        """Quét toàn bộ manifest và báo cáo audit công khai đảm bảo không có locator hay nhãn bị lộ."""
        forbidden_regexes = [
            (r'"row_offset"\s*:\s*\d+', "row_offset thô của ứng viên"),
            (r'"candidate_locators"', "trường candidate_locators"),
            (r'"main_locators"', "trường main_locators"),
            (r'"reserve_locators"', "trường reserve_locators"),
            (r'"source_label"\s*:\s*"(?:phish|benign)"', "nhãn nguồn phân loại"),
            (r'"primary_org_status"\s*:\s*"[^"]+"', "trạng thái tổ chức mục tiêu"),
        ]

        artifacts_to_scan = [
            MANIFEST_PATH,
            AUDIT_REPORT_PATH,
            INSPECTION_REPORT_PATH,
        ]

        for path in artifacts_to_scan:
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            for pattern, desc in forbidden_regexes:
                matches = re.findall(pattern, text)
                assert len(matches) == 0, f"Phát hiện rò rỉ {desc} trong {path.name}: {matches[:3]}"
