"""Bộ kiểm thử cho Cổng chọn mẫu 5 giai đoạn và Kiểm định loại trừ Pilot Lô 1 (Task DATA-02 / Lead D).

Phân định rõ ràng:
- [FIXTURE]: Các ca kiểm thử dùng dữ liệu giả lập tự chứa (Self-contained fixtures) để kiểm tra logic
  từng cổng, các trường hợp biên lỗi, loại bỏ thiên lệch thứ tự hàng và chặn template kit clone.
  Bộ test này chạy độc lập 100% trên mọi môi trường (kể cả clean git checkout không có dữ liệu hạn chế).
- [REAL SHARD & RESTRICTED INTEGRATION]: Các ca kiểm thử tích hợp chạy trực tiếp trên tệp shard parquet
  và hồ sơ hạn chế thật (nếu có trên đĩa). Nếu môi trường là clean checkout không có dữ liệu này,
  test sẽ tự động SKIPPED có lý do kiểm toán rõ ràng mà không gây lỗi giả (false failure).

Quy chuẩn ARS & Fail-Closed Protocols (Theo chỉ đạo V3.5 Lead D & Errata v1.1 QA Lead B):
1. Gate 0: Chặn đứng shard cách ly (train-000, train-055), nguồn chưa duyệt (PhishVN), sai revision, sai/thiếu hash byte tệp thực tế.
2. Gate 1: Cửa sổ ngày [2024-10-01, 2025-09-08], kiểm định regex YYYY-MM-DD nghiêm ngặt, từ chối mọi chuỗi có hậu tố rác.
3. Gate 2: Chống rò rỉ 6 lớp (raw/norm URL, raw/cleaned HTML, bare/prefixed domain). Fail-closed khi thiếu/sai cam kết hạn chế.
4. Gate 3: Khử trùng lặp nội bộ (max 1/eTLD+1), loại bỏ thiên lệch thứ tự hàng (Row-Order Bias Elimination qua canonical sort + seeded shuffle), và chặn template clone/near-duplicate qua TemplateSimilarityEngine.
5. Gate 4: Bắt buộc đủ quota mẫu (thiếu quota ném SelectionGateError dừng an toàn) và tái lập 100% qua Seed niêm phong.
6. End-to-end: Chạy toàn pipeline và kiểm thử runner CLI thực tế.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List
import pytest

import pyarrow as pa
import pyarrow.parquet as pq

from phishing.data.exclusion import ExclusionRegistry
from phishing.data.selection_gate import (
    DEFAULT_APPROVED_REVISION,
    DEFAULT_APPROVED_SOURCE,
    SelectionGateError,
    SelectionGatePipeline,
    compute_file_sha256,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REAL_TRAIN_000_PATH = PROJECT_ROOT / "data" / "raw" / "phreshphish" / "data" / "train-000.parquet"
REAL_TRAIN_055_PATH = PROJECT_ROOT / "data" / "raw" / "phreshphish" / "data" / "train-055.parquet"
REAL_DOSSIER_V2_PATH = PROJECT_ROOT / "data" / "restricted" / "pilot_batch1_recovery_dossier_restricted_v2.json"

MOCK_PILOT_RAW_URL = "https://mock-pilot-site.org/login"
MOCK_PILOT_NORM_URL = "https://mock-pilot-site.org/login"
MOCK_PILOT_RAW_HTML = "<html><body><h1>Mock Pilot Attack Page</h1><form action='/steal'><input name='u'/><input name='p' type='password'/></form></body></html>"
MOCK_PILOT_CLEAN_HTML = "Mock Pilot Attack Page"
MOCK_PILOT_DOMAIN = "mock-pilot-site.org"


@pytest.fixture
def self_contained_registry(tmp_path: Path) -> ExclusionRegistry:
    """Fixture tạo một ExclusionRegistry tự chứa (self-contained mock) độc lập 100% với Git.

    Bảo đảm chạy mượt mà trên clean checkout mà vẫn thực thi đầy đủ logic kiểm tra 6 lớp.
    """
    mock_dossier_path = tmp_path / "mock_dossier_v2.json"
    mock_mapping = [
        {
            "entry_id": "EXCL-PLT-MOCK-01",
            "pilot_row_idx": 0,
            "raw_url_sha256": hashlib.sha256(MOCK_PILOT_RAW_URL.encode("utf-8")).hexdigest(),
            "normalized_url_sha256": hashlib.sha256(MOCK_PILOT_NORM_URL.encode("utf-8")).hexdigest(),
            "raw_html_sha256": hashlib.sha256(MOCK_PILOT_RAW_HTML.encode("utf-8")).hexdigest(),
            "cleaned_html_sha256": hashlib.sha256(MOCK_PILOT_CLEAN_HTML.encode("utf-8")).hexdigest(),
            "group_id": f"domain:{MOCK_PILOT_DOMAIN}",
            "group_sha256": hashlib.sha256(f"domain:{MOCK_PILOT_DOMAIN}".encode("utf-8")).hexdigest(),
        }
    ]
    mock_dossier_content = json.dumps({"mapping": mock_mapping}, indent=2)
    mock_dossier_path.write_bytes(mock_dossier_content.encode("utf-8"))
    mock_commitment_sha = hashlib.sha256(mock_dossier_path.read_bytes()).hexdigest()

    registry_json = {
        "metadata": {"version": "v3.5-test"},
        "exclusions": [
            {
                "exclusion_id": "EXCL-PILOT-01",
                "status": "sealed_restricted_commitment",
                "restricted_dossier_reference": str(mock_dossier_path),
                "commitment_sha256": mock_commitment_sha,
                "n_samples": 1,
            }
        ],
        "training_blocked": True,
    }
    reg_file = tmp_path / "test_exclusion_registry.json"
    reg_file.write_text(json.dumps(registry_json, indent=2), encoding="utf-8")

    return ExclusionRegistry(registry_path=reg_file)


@pytest.fixture
def clean_pipeline(self_contained_registry: ExclusionRegistry) -> SelectionGatePipeline:
    """Fixture tạo pipeline chọn mẫu hoàn toàn tự chứa (Self-contained SelectionGatePipeline)."""
    return SelectionGatePipeline(
        exclusion_registry=self_contained_registry,
        min_date="2024-10-01",
        max_date="2025-09-08",
    )


# ==============================================================================
# GATE 0: SOURCE & SHARD INTEGRITY TESTS
# ==============================================================================
class TestGate0SourceAndShardIntegrity:
    """Kiểm tra Cổng 0: Tính toàn vẹn của nguồn, shard và kiểm soát cách ly."""

    def test_gate0_rejects_quarantined_train_000_by_name(self, clean_pipeline):
        """[FIXTURE] Chặn chuỗi định danh tên shard train-000."""
        with pytest.raises(SelectionGateError, match="CÁCH LY"):
            clean_pipeline.gate_0_source_and_shard(
                source_id="phreshphish",
                shard_path="train-000.parquet",
                revision=DEFAULT_APPROVED_REVISION,
            )

    def test_gate0_rejects_quarantined_train_055_by_name(self, clean_pipeline):
        """[FIXTURE] Chặn chuỗi định danh tên shard train-055."""
        with pytest.raises(SelectionGateError, match="CÁCH LY"):
            clean_pipeline.gate_0_source_and_shard(
                source_id="phreshphish",
                shard_path="data/train-055.parquet",
                revision=DEFAULT_APPROVED_REVISION,
            )

    def test_gate0_rejects_quarantined_real_shard_path(self, clean_pipeline):
        """[REAL SHARD] Chặn đường dẫn tệp thực tế của shard cách ly (nếu có trên đĩa)."""
        if not REAL_TRAIN_000_PATH.exists():
            pytest.skip("Chưa có shard train-000 trên clean checkout")
        with pytest.raises(SelectionGateError, match="CÁCH LY"):
            clean_pipeline.gate_0_source_and_shard(
                source_id="phreshphish",
                shard_path=REAL_TRAIN_000_PATH,
                revision=DEFAULT_APPROVED_REVISION,
            )

    def test_gate0_rejects_unvetted_source_phishvn(self, clean_pipeline):
        """[FIXTURE] Chặn đứng nguồn dữ liệu PhishVN khi chưa có biên bản phê duyệt."""
        with pytest.raises(SelectionGateError, match="chưa được phê duyệt"):
            clean_pipeline.gate_0_source_and_shard(
                source_id="phishvn",
                shard_path="data/train-001.parquet",
                revision=DEFAULT_APPROVED_REVISION,
            )

    def test_gate0_rejects_arbitrary_unapproved_source(self, clean_pipeline):
        """[FIXTURE] Chặn đứng bất kỳ nguồn lạ nào không nằm trong danh mục."""
        with pytest.raises(SelectionGateError, match="không khớp với nguồn được duyệt"):
            clean_pipeline.gate_0_source_and_shard(
                source_id="unvetted_external_source",
                shard_path="data/train-001.parquet",
                revision=DEFAULT_APPROVED_REVISION,
            )

    def test_gate0_rejects_unapproved_revision(self, clean_pipeline):
        """[FIXTURE] Chặn đứng git revision không khớp với revision đã khóa."""
        with pytest.raises(SelectionGateError, match="không khớp với revision đã khóa"):
            clean_pipeline.gate_0_source_and_shard(
                source_id="phreshphish",
                shard_path="data/train-001.parquet",
                revision="1111111111111111111111111111111111111111",
            )

    def test_gate0_rejects_non_existent_shard_file(self, clean_pipeline):
        """[FIXTURE] Báo lỗi khi tệp shard không tồn tại trên đĩa."""
        with pytest.raises(SelectionGateError, match="Không tìm thấy tệp shard thực tế"):
            clean_pipeline.gate_0_source_and_shard(
                source_id="phreshphish",
                shard_path=PROJECT_ROOT / "data" / "raw" / "phreshphish" / "data" / "train-999.parquet",
                revision=DEFAULT_APPROVED_REVISION,
            )

    def test_gate0_rejects_shard_not_in_manifest(self, clean_pipeline, tmp_path):
        """[FIXTURE] Báo lỗi khi tệp shard hợp lệ về tên nhưng không có trong source_manifest.json."""
        dummy_shard = tmp_path / "train-999.parquet"
        dummy_shard.write_bytes(b"dummy parquet bytes")
        with pytest.raises(SelectionGateError, match="không tồn tại trong source_manifest"):
            clean_pipeline.gate_0_source_and_shard(
                source_id="phreshphish",
                shard_path=dummy_shard,
                revision=DEFAULT_APPROVED_REVISION,
            )

    def test_gate0_rejects_tampered_shard_actual_bytes(self, tmp_path):
        """[FIXTURE & BYTE READ] Tự tính mã băm byte thực tế và chặn tệp bị sai lệch hash so với manifest."""
        dummy_shard = tmp_path / "train-001.parquet"
        dummy_shard.write_bytes(b"tampered content bytes")

        # Tạo manifest giả lập với hash khác
        fake_manifest_path = tmp_path / "source_manifest.json"
        fake_manifest = {
            "source_id": "phreshphish",
            "revision": DEFAULT_APPROVED_REVISION,
            "files": [
                {
                    "file_name": "train-001.parquet",
                    "source_metadata_lfs_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                    "bytes": 22,
                }
            ],
        }
        fake_manifest_path.write_text(json.dumps(fake_manifest), encoding="utf-8")

        pipeline = SelectionGatePipeline(source_manifest_path=fake_manifest_path)
        with pytest.raises(SelectionGateError, match="không khớp với mã băm trong manifest"):
            pipeline.gate_0_source_and_shard(
                source_id="phreshphish",
                shard_path=dummy_shard,
                revision=DEFAULT_APPROVED_REVISION,
            )

    def test_gate0_accepts_valid_shard_with_matching_bytes(self, tmp_path):
        """[FIXTURE & BYTE READ] Chấp nhận tệp shard khi mã băm byte đọc thực tế khớp 100% với manifest."""
        dummy_shard = tmp_path / "train-001.parquet"
        content = b"clean uncorrupted parquet stream data"
        dummy_shard.write_bytes(content)
        expected_sha = hashlib.sha256(content).hexdigest()

        fake_manifest_path = tmp_path / "source_manifest.json"
        fake_manifest = {
            "source_id": "phreshphish",
            "revision": DEFAULT_APPROVED_REVISION,
            "files": [
                {
                    "file_name": "train-001.parquet",
                    "source_metadata_lfs_sha256": expected_sha,
                    "bytes": len(content),
                }
            ],
        }
        fake_manifest_path.write_text(json.dumps(fake_manifest), encoding="utf-8")

        pipeline = SelectionGatePipeline(source_manifest_path=fake_manifest_path)
        ok = pipeline.gate_0_source_and_shard(
            source_id="phreshphish",
            shard_path=dummy_shard,
            revision=DEFAULT_APPROVED_REVISION,
        )
        assert ok is True


# ==============================================================================
# GATE 1: FIELD VALIDITY & DATE WINDOW TESTS (V3.5 Plan: 2024-10-01 to 2025-09-08)
# ==============================================================================
class TestGate1FieldValidityAndDates:
    """Kiểm tra Cổng 1: URL hợp lệ, giới hạn độ dài HTML và kiểm định ngày nghiêm ngặt (ARS)."""

    def test_gate1_rejects_empty_url(self, clean_pipeline):
        """[FIXTURE] Chặn URL rỗng."""
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "", "html": "abc", "date": "2025-01-15"})
        assert ok is False
        assert reason == "reject_empty_url"

    def test_gate1_rejects_invalid_url_scheme(self, clean_pipeline):
        """[FIXTURE] Chặn scheme không hợp lệ (không phải http/https)."""
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "ftp://example.com", "html": "abc", "date": "2025-01-15"})
        assert ok is False
        assert reason == "reject_invalid_url_format"

    def test_gate1_rejects_empty_html(self, clean_pipeline):
        """[FIXTURE] Chặn HTML rỗng."""
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": "   ", "date": "2025-01-15"})
        assert ok is False
        assert reason == "reject_empty_html"

    def test_gate1_rejects_oversized_html(self, clean_pipeline):
        """[FIXTURE] Chặn HTML vượt quá 2,000,000 ký tự."""
        huge_html = "x" * 2000001
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": huge_html, "date": "2025-01-15"})
        assert ok is False
        assert "reject_html_len_" in reason

    def test_gate1_rejects_missing_date(self, clean_pipeline):
        """[FIXTURE] Chặn mẫu thiếu trường ngày hoặc rỗng."""
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": "<p>x</p>", "date": None})
        assert ok is False
        assert reason == "reject_missing_date"

        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": "<p>x</p>", "date": ""})
        assert ok is False
        assert reason == "reject_missing_date"

    def test_gate1_rejects_invalid_date_format_and_garbage_suffix(self, clean_pipeline):
        """[FIXTURE] Bỏ cắt [:10] - Chặn chuỗi ngày có hậu tố rác hoặc định dạng sai."""
        # Chuỗi có hậu tố rác (trước đây bị [:10] cắt lọt)
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": "<p>x</p>", "date": "2024-10-01T00:00:00"})
        assert ok is False
        assert reason == "reject_invalid_date_format"

        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": "<p>x</p>", "date": "2024-10-01-extra"})
        assert ok is False
        assert reason == "reject_invalid_date_format"

        # Định dạng DD/MM/YYYY sai quy định
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": "<p>x</p>", "date": "15/01/2025"})
        assert ok is False
        assert reason == "reject_invalid_date_format"

    def test_gate1_rejects_date_before_min_boundary(self, clean_pipeline):
        """[FIXTURE] Chặn ngày trước min_date (2024-10-01 theo V3.5)."""
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": "<p>x</p>", "date": "2024-09-30"})
        assert ok is False
        assert "reject_date_before_min" in reason

    def test_gate1_rejects_date_after_max_boundary(self, clean_pipeline):
        """[FIXTURE] Chặn ngày sau max_date (2025-09-08)."""
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": "<p>x</p>", "date": "2025-09-09"})
        assert ok is False
        assert "reject_date_after_max" in reason

    def test_gate1_accepts_boundary_and_valid_dates(self, clean_pipeline):
        """[FIXTURE] Chấp nhận mẫu có ngày đúng tại hai đầu ranh giới và nằm trong cửa sổ."""
        # Cận dưới: 2024-10-01
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com/min", "html": "<p>x</p>", "date": "2024-10-01"})
        assert ok is True
        assert reason == "passed"

        # Cận trên: 2025-09-08
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com/max", "html": "<p>x</p>", "date": "2025-09-08"})
        assert ok is True
        assert reason == "passed"

        # Giữa cửa sổ: 2025-03-15
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com/mid", "html": "<p>x</p>", "date": "2025-03-15"})
        assert ok is True
        assert reason == "passed"


# ==============================================================================
# GATE 2: CRYPTOGRAPHIC ANTI-LEAKAGE TESTS (6 Layers)
# ==============================================================================
class TestGate2CryptographicAntiLeakage:
    """Kiểm tra Cổng 2: Kiểm soát chống rò rỉ loại trừ 6 lớp và hành vi Fail-Closed."""

    def test_gate2_deliberate_injection_of_raw_url_of_pilot_sample(self, clean_pipeline):
        """[FIXTURE] Cố ý đưa URL thô của mẫu Pilot Lô 1 vào pipeline -> BỊ CHẶN Ở CỔNG 2."""
        injected_sample = {
            "url": MOCK_PILOT_RAW_URL,
            "html": "<html>Different Content But Same URL</html>",
            "date": "2025-01-15",
        }
        ok, reason = clean_pipeline.gate_2_anti_leakage(injected_sample)
        assert ok is False
        assert reason == "reject_exclusion_registry_match"

    def test_gate2_deliberate_injection_of_raw_html_of_pilot_sample(self, clean_pipeline):
        """[FIXTURE] Cố ý đưa HTML thô của mẫu Pilot Lô 1 vào pipeline -> BỊ CHẶN Ở CỔNG 2."""
        injected_sample = {
            "url": "https://completely-new-unseen-url.com/page",
            "html": MOCK_PILOT_RAW_HTML,
            "date": "2025-01-15",
        }
        ok, reason = clean_pipeline.gate_2_anti_leakage(injected_sample)
        assert ok is False
        assert reason == "reject_exclusion_registry_match"

    def test_gate2_deliberate_injection_of_domain_sharing_sample(self, clean_pipeline):
        """[FIXTURE] Cố ý đưa mẫu có tên miền chia sẻ với Pilot vào pipeline -> BỊ CHẶN Ở CỔNG 2."""
        injected_sample = {
            "url": f"https://sub.{MOCK_PILOT_DOMAIN}/article",
            "html": "<html>Unique content on shared domain</html>",
            "date": "2025-01-15",
        }
        ok, reason = clean_pipeline.gate_2_anti_leakage(injected_sample)
        assert ok is False
        assert reason == "reject_exclusion_registry_match"

    def test_gate2_missing_restricted_dossier_fails_closed(self, tmp_path):
        """[FIXTURE FAIL-CLOSED] Nếu hồ sơ hạn chế bị thiếu trên đường chạy thật, pipeline ném RuntimeError."""
        fake_reg = {
            "metadata": {"version": "test"},
            "exclusions": [
                {
                    "exclusion_id": "EXCL-PUBLIC-MOCK",
                    "samples": [{"url_sha256": "1111111111111111111111111111111111111111111111111111111111111111"}],
                },
                {
                    "exclusion_id": "EXCL-PILOT-01",
                    "status": "sealed_restricted_commitment",
                    "restricted_dossier_reference": "data/restricted/non_existent_dossier.json",
                    "commitment_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                    "n_samples": 20,
                },
            ],
            "training_blocked": True,
        }
        reg_file = tmp_path / "exclusion_registry.json"
        reg_file.write_text(json.dumps(fake_reg), encoding="utf-8")

        reg = ExclusionRegistry(registry_path=reg_file)
        pipeline = SelectionGatePipeline(exclusion_registry=reg)

        valid_sample = {
            "url": "https://normal-page.org/test",
            "html": "<html>Hello World</html>",
            "date": "2025-01-15",
        }
        with pytest.raises(RuntimeError, match="LỆNH CHẶN FAIL-CLOSED"):
            pipeline.gate_2_anti_leakage(valid_sample)

    def test_gate2_tampered_restricted_dossier_hash_fails_closed(self, tmp_path):
        """[FIXTURE FAIL-CLOSED] Nếu mã băm tệp hạn chế bị sai lệch so với cam kết, ném RuntimeError."""
        dossier = tmp_path / "tampered_dossier.json"
        dossier.write_text(json.dumps({"mapping": []}), encoding="utf-8")

        fake_reg = {
            "metadata": {"version": "test"},
            "exclusions": [
                {
                    "exclusion_id": "EXCL-PUBLIC-MOCK",
                    "samples": [{"url_sha256": "1111111111111111111111111111111111111111111111111111111111111111"}],
                },
                {
                    "exclusion_id": "EXCL-PILOT-01",
                    "status": "sealed_restricted_commitment",
                    "restricted_dossier_reference": str(dossier),
                    "commitment_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                    "n_samples": 20,
                },
            ],
            "training_blocked": True,
        }
        reg_file = tmp_path / "exclusion_registry.json"
        reg_file.write_text(json.dumps(fake_reg), encoding="utf-8")

        with pytest.raises(RuntimeError, match="LỖI TOÀN VẸN HỒ SƠ HẠN CHẾ"):
            ExclusionRegistry(registry_path=reg_file)

    def test_gate2_integration_with_real_restricted_dossier_v2(self):
        """[REAL RESTRICTED INTEGRATION] Đối soát với hồ sơ V2 thật trên đĩa (Bỏ qua nếu clean checkout)."""
        if not REAL_DOSSIER_V2_PATH.exists():
            pytest.skip("Chưa có hồ sơ restricted V2 cục bộ trên clean checkout")

        real_dossier = json.loads(REAL_DOSSIER_V2_PATH.read_text(encoding="utf-8"))
        first_pilot = real_dossier["mapping"][0]

        # Nạp pipeline với registry thật của repo
        pipeline = SelectionGatePipeline()
        injected = {
            "url": "https://new-url-injecting-pilot-html.org/page",
            "html": "<html>dummy</html>",
            "raw_html_sha256": first_pilot["raw_html_sha256"],
            "date": "2025-01-15",
        }
        ok, reason = pipeline.gate_2_anti_leakage(injected)
        assert ok is False
        assert reason == "reject_exclusion_registry_match"

    def test_gate2_regression_raw_url_differs_but_normalized_url_matches(self, clean_pipeline, self_contained_registry):
        """[REGRESSION] Raw URL khác biệt nhưng Normalized URL trùng khớp registry -> Bị loại trừ nhất quán."""
        # MOCK_PILOT_NORM_URL trong fixture là "https://mock-pilot-site.org/login"
        # Biến thể URL thô có uppercase hostname, explicit port 443 và fragment (không đổi normalized URL):
        variant_raw_url = "https://MOCK-PILOT-SITE.ORG:443/login#fragment"
        sample = {
            "url": variant_raw_url,
            "html": "<p>Body text completely distinct from any pilot</p>",
            "date": "2025-01-15",
        }
        # Chứng minh: mã băm raw URL hoàn toàn không trùng khớp trong registry
        raw_hash = hashlib.sha256(variant_raw_url.encode("utf-8")).hexdigest()
        assert raw_hash not in self_contained_registry._url_hashes

        # Kiểm tra 1: ExclusionRegistry.is_excluded() nhận diện qua normalize_url và loại trừ
        assert self_contained_registry.is_excluded(sample) is True

        # Kiểm tra 2: filter_split() đưa vào excluded, không đưa vào kept
        kept, excluded = self_contained_registry.filter_split([sample], allow_unverified_commitments=True)
        assert sample in excluded
        assert len(kept) == 0

        # Kiểm tra 3: Gate 2 từ chối với lý do reject_exclusion_registry_match
        ok, reason = clean_pipeline.gate_2_anti_leakage(sample)
        assert ok is False
        assert reason == "reject_exclusion_registry_match"

    def test_gate2_regression_raw_html_differs_but_cleaned_html_matches(self, tmp_path):
        """[REGRESSION] Raw HTML khác biệt nhưng Cleaned HTML trùng khớp registry -> Bị loại trừ nhất quán."""
        from phishing.preprocessing.html import clean_html

        target_page_url = "https://unrelated-sample-domain.org/index.html"
        raw_clean_target = "<p>Standard clean login form structure</p>"
        cleaned_target = clean_html(raw_clean_target, page_url=target_page_url)
        cleaned_hash = hashlib.sha256(cleaned_target.encode("utf-8")).hexdigest()

        # Tạo registry độc lập chứa cleaned_html_sha256 này
        dossier_path = tmp_path / "mock_html_dossier.json"
        dossier_data = {
            "mapping": [
                {
                    "entry_id": "EXCL-REG-HTML-01",
                    "raw_url_sha256": "0" * 64,
                    "raw_html_sha256": "0" * 64,
                    "cleaned_html_sha256": cleaned_hash,
                }
            ]
        }
        dossier_path.write_bytes(json.dumps(dossier_data).encode("utf-8"))
        commitment_sha = hashlib.sha256(dossier_path.read_bytes()).hexdigest()

        reg_data = {
            "metadata": {"version": "test"},
            "exclusions": [
                {
                    "exclusion_id": "EXCL-PILOT-01",
                    "status": "sealed_restricted_commitment",
                    "restricted_dossier_reference": str(dossier_path),
                    "commitment_sha256": commitment_sha,
                    "n_samples": 1,
                }
            ],
            "training_blocked": True,
        }
        reg_file = tmp_path / "reg_html.json"
        reg_file.write_text(json.dumps(reg_data), encoding="utf-8")
        registry = ExclusionRegistry(registry_path=reg_file)
        pipeline = SelectionGatePipeline(exclusion_registry=registry)

        # Mẫu kiểm tra có thêm script và inline styles -> Raw HTML hash khác biệt hoàn toàn
        injected_raw_html = "<p>Standard clean login form structure</p><script>alert('exploit');</script>"
        injected_raw_hash = hashlib.sha256(injected_raw_html.encode("utf-8")).hexdigest()
        assert injected_raw_hash not in registry._html_hashes

        candidate = {
            "url": target_page_url,
            "html": injected_raw_html,
            "date": "2025-01-15",
        }

        # Kiểm tra 1: ExclusionRegistry.is_excluded() nhận diện qua clean_html và loại trừ
        assert registry.is_excluded(candidate) is True

        # Kiểm tra 2: filter_split() đưa vào excluded, không đưa vào kept
        kept, excluded = registry.filter_split([candidate], allow_unverified_commitments=True)
        assert candidate in excluded
        assert len(kept) == 0

        # Kiểm tra 3: Gate 2 từ chối với lý do reject_exclusion_registry_match
        ok, reason = pipeline.gate_2_anti_leakage(candidate)
        assert ok is False
        assert reason == "reject_exclusion_registry_match"

    def test_gate2_regression_malformed_input_preprocessing_error_fails_closed(self, clean_pipeline, self_contained_registry):
        """[REGRESSION FAIL-CLOSED] Lỗi định dạng/tiền xử lý trên dữ liệu thật không biến thành 'passed'."""
        # URL có khoảng trắng và ký tự điều khiển bất hợp pháp -> normalize_url ném ValueError
        malformed_sample = {
            "url": "https://invalid domain with spaces.com/test\x00",
            "html": "<html><body>Valid Body</body></html>",
            "date": "2025-01-15",
        }

        # Gate 2 từ chối rõ ràng với lý do preprocessing error, TUYỆT ĐỐI không trả 'passed'
        ok, reason = clean_pipeline.gate_2_anti_leakage(malformed_sample)
        assert ok is False
        assert reason == "reject_gate2_preprocessing_error"

        # is_excluded() xử lý fail-closed (loại trừ vì không thể đối chiếu an toàn)
        assert self_contained_registry.is_excluded(malformed_sample) is True

        # filter_split() đưa vào excluded, không đưa vào kept
        kept, excluded = self_contained_registry.filter_split([malformed_sample], allow_unverified_commitments=True)
        assert malformed_sample in excluded
        assert len(kept) == 0

    def test_gate2_regression_system_runtime_error_propagates_unswallowed(self, clean_pipeline, self_contained_registry, monkeypatch):
        """[REGRESSION FAIL-CLOSED] Ngoại lệ hệ thống nghiêm trọng (RuntimeError) không bị nuốt, dừng pipeline ngay lập tức."""
        def mock_broken_normalize(url: str) -> str:
            raise RuntimeError("LỖI HỆ THỐNG: Bộ chuẩn hóa URL gặp sự cố nghiêm trọng")

        monkeypatch.setattr("phishing.data.selection_gate.normalize_url", mock_broken_normalize)
        monkeypatch.setattr("phishing.data.exclusion.normalize_url", mock_broken_normalize)

        sample = {
            "url": "https://valid-normal-site.com/index",
            "html": "<html><body>Content</body></html>",
            "date": "2025-01-15",
        }

        # Cả Gate 2 và is_excluded đều ném RuntimeError, không âm thầm nuốt lỗi bằng except Exception: pass
        with pytest.raises(RuntimeError, match="LỖI HỆ THỐNG"):
            clean_pipeline.gate_2_anti_leakage(sample)

        with pytest.raises(RuntimeError, match="LỖI HỆ THỐNG"):
            self_contained_registry.is_excluded(sample)

    def test_gate2_regression_missing_or_tampered_commitment_halts_before_export(self, tmp_path):
        """[REGRESSION FAIL-CLOSED] Thiếu hoặc sai hash cam kết hồ sơ hạn chế -> dừng trước khi xuất danh sách hay artifact."""
        # 1. Hồ sơ hạn chế có hash không khớp cam kết
        bad_dossier = tmp_path / "bad_dossier.json"
        bad_dossier.write_text(json.dumps({"mapping": []}), encoding="utf-8")

        tampered_reg_data = {
            "metadata": {"version": "test"},
            "exclusions": [
                {
                    "exclusion_id": "EXCL-PILOT-01",
                    "status": "sealed_restricted_commitment",
                    "restricted_dossier_reference": str(bad_dossier),
                    "commitment_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                    "n_samples": 20,
                }
            ],
            "training_blocked": True,
        }
        reg_file = tmp_path / "tampered_reg.json"
        reg_file.write_text(json.dumps(tampered_reg_data), encoding="utf-8")

        # Ném lỗi toàn vẹn ngay từ constructor
        with pytest.raises(RuntimeError, match="LỖI TOÀN VẸN HỒ SƠ HẠN CHẾ"):
            ExclusionRegistry(registry_path=reg_file)

        # 2. Hồ sơ hạn chế bị thiếu tệp
        missing_reg_data = {
            "metadata": {"version": "test"},
            "exclusions": [
                {
                    "exclusion_id": "EXCL-PUBLIC-MOCK",
                    "samples": [{"url_sha256": "1" * 64}],
                },
                {
                    "exclusion_id": "EXCL-PILOT-01",
                    "status": "sealed_restricted_commitment",
                    "restricted_dossier_reference": "data/restricted/non_existent.json",
                    "commitment_sha256": "0" * 64,
                    "n_samples": 20,
                }
            ],
            "training_blocked": True,
        }
        missing_reg_file = tmp_path / "missing_reg.json"
        missing_reg_file.write_text(json.dumps(missing_reg_data), encoding="utf-8")
        missing_reg = ExclusionRegistry(registry_path=missing_reg_file)

        # assert_restricted_commitments_verified() ném RuntimeError
        with pytest.raises(RuntimeError, match="LỆNH CHẶN FAIL-CLOSED"):
            missing_reg.assert_restricted_commitments_verified()

        # filter_split() ném RuntimeError trước khi trả kết quả
        with pytest.raises(RuntimeError, match="LỆNH CHẶN FAIL-CLOSED"):
            missing_reg.filter_split([{"url": "https://example.com", "html": "abc"}])

        # pipeline.run_selection() ném RuntimeError trước khi chọn bất kỳ mẫu nào
        pipe = SelectionGatePipeline(exclusion_registry=missing_reg)
        with pytest.raises(RuntimeError, match="LỆNH CHẶN FAIL-CLOSED"):
            pipe.run_selection(
                [{"url": "https://example.com", "html": "abc", "date": "2025-01-15"}],
                skip_gate_0_file_check=True,
            )


# ==============================================================================
# GATE 3: DEDUPLICATION, ROW-ORDER BIAS ELIMINATION & TEMPLATE CLONES
# ==============================================================================
class TestGate3DeduplicationAndTemplateClones:
    """Kiểm tra Cổng 3: Khử trùng lặp, triệt tiêu thiên lệch thứ tự hàng và chặn template clone V3.5."""

    def test_gate3_deduplicates_exact_url_and_html(self, clean_pipeline):
        """[FIXTURE] Khử trùng lặp URL và HTML chính xác trong nội bộ đợt rút."""
        pool = [
            {"url": "https://dup-a.com/page", "html": "<html>Page A</html>", "date": "2025-01-15"},
            {"url": "https://dup-a.com/page", "html": "<html>Page A Different HTML</html>", "date": "2025-01-15"},
            {"url": "https://dup-b.com/page", "html": "<html>Page A</html>", "date": "2025-01-15"},
        ]
        res = clean_pipeline.run_selection(pool, target_quota=1, seed=42, skip_gate_0_file_check=True)
        assert len(res["selected_samples"]) == 1
        assert res["audit_log"]["rejections"].get("reject_gate3_duplicate_url", 0) >= 1 or res["audit_log"]["rejections"].get("reject_gate3_duplicate_html", 0) >= 1

    def test_gate3_enforces_domain_diversity(self, clean_pipeline):
        """[FIXTURE] Giới hạn nghiêm ngặt tối đa 1 mẫu trên mỗi tên miền eTLD+1."""
        pool = [
            {"url": "https://sub1.shared-domain.org/login", "html": "<html><div>Sub 1</div></html>", "date": "2025-01-15"},
            {"url": "https://sub2.shared-domain.org/portal", "html": "<html><section>Sub 2</section></html>", "date": "2025-01-15"},
        ]
        res = clean_pipeline.run_selection(pool, target_quota=1, seed=42, skip_gate_0_file_check=True)
        assert len(res["selected_samples"]) == 1
        assert res["audit_log"]["rejections"]["reject_gate3_domain_collision"] == 1

    def test_gate3_eliminates_row_order_bias(self, clean_pipeline):
        """[FIXTURE] Loại bỏ thiên lệch thứ tự hàng: Cùng seed, thứ tự đầu vào bị đảo ngược vẫn chọn ra kết quả giống hệt nhau."""
        tag_list = ["article", "section", "main", "aside", "nav", "header", "footer", "dialog", "details", "blockquote", "figure", "table"]
        candidates = []
        for i in range(12):
            t = tag_list[i % len(tag_list)]
            candidates.append({
                "url": f"https://domain-{i % 6}.org/path/{i}",
                "html": f"<html><body><{t} id='node_{i}'><p>Unique distinct vocabulary content for item {i}</p></{t}></body></html>",
                "date": "2025-01-15",
            })

        # Chạy lượt 1 với danh sách xuôi
        res_forward = clean_pipeline.run_selection(candidates, target_quota=5, seed=12345, skip_gate_0_file_check=True)
        selected_forward = [s["url"] for s in res_forward["selected_samples"]]

        # Chạy lượt 2 với danh sách đảo ngược hoàn toàn
        candidates_reversed = list(reversed(candidates))
        res_reversed = clean_pipeline.run_selection(candidates_reversed, target_quota=5, seed=12345, skip_gate_0_file_check=True)
        selected_reversed = [s["url"] for s in res_reversed["selected_samples"]]

        # Kết quả chọn mẫu phải hoàn toàn trùng khớp từng phần tử
        assert selected_forward == selected_reversed

    def test_gate3_sequential_near_duplicate_template_clone_rejection(self, clean_pipeline):
        """[FIXTURE] Chặn các template clone sinh từ cùng phishing kit bằng TemplateSimilarityEngine."""
        # Hai mẫu có cùng cấu trúc DOM tag multiset và khung văn bản tương đồng cao (>85% Jaccard)
        base_html = "<html><head><title>Login</title></head><body><div class='box'><h2>Sign in</h2><form><input type='text'/><input type='password'/><button>Submit</button></form></div></body></html>"
        clone_html = "<html><head><title>Signin</title></head><body><div class='box'><h2>Log in</h2><form><input type='text'/><input type='password'/><button>Continue</button></form></div></body></html>"

        pool = [
            {"url": "https://kit-attack-1.com/login", "html": base_html, "date": "2025-01-15"},
            {"url": "https://kit-attack-2.org/signin", "html": clone_html, "date": "2025-01-15"},
        ]
        res = clean_pipeline.run_selection(pool, target_quota=1, seed=42, skip_gate_0_file_check=True)
        assert len(res["selected_samples"]) == 1
        assert res["audit_log"]["rejections"].get("reject_gate3_template_clone", 0) >= 1


# ==============================================================================
# GATE 4: QUOTA & SEEDED SAMPLING TESTS
# ==============================================================================
class TestGate4QuotaAndSampling:
    """Kiểm tra Cổng 4: Thực thi Quota Fail-Closed và tính xác định của PRNG seed."""

    def test_gate4_insufficient_quota_fails_closed(self, clean_pipeline):
        """[FIXTURE FAIL-CLOSED] Số lượng ứng viên sạch nhỏ hơn quota yêu cầu -> ném SelectionGateError."""
        pool = [
            {"url": f"https://valid-{i}.com/page", "html": f"<html><body><p>Content {i}</p></body></html>", "date": "2025-01-15"}
            for i in range(5)
        ]
        with pytest.raises(SelectionGateError, match="không đạt chỉ tiêu quota yêu cầu"):
            clean_pipeline.run_selection(pool, target_quota=10, seed=42, skip_gate_0_file_check=True)

    def test_gate4_seeded_sampling_is_deterministic(self, clean_pipeline):
        """[FIXTURE] Cùng một seed niêm phong phải cho ra chính xác 100% cùng một tập mẫu."""
        tags = [
            "div", "section", "article", "main", "aside", "nav", "header", "footer",
            "table", "form", "figure", "details", "blockquote", "dialog", "canvas",
            "progress", "meter", "time", "mark", "ruby", "kbd", "samp", "output",
            "address", "audio", "video", "picture", "template", "fieldset", "menu"
        ]
        pool = []
        for i in range(25):
            t = tags[i % len(tags)]
            pool.append({
                "url": f"https://site-{i}.org/page",
                "html": f"<html><body><{t}><p>Completely unique body vocabulary and semantics for index {i}</p></{t}></body></html>",
                "date": "2025-01-15",
            })
        run1 = clean_pipeline.run_selection(pool, target_quota=10, seed=99999, skip_gate_0_file_check=True)
        run2 = clean_pipeline.run_selection(pool, target_quota=10, seed=99999, skip_gate_0_file_check=True)
        assert [s["url"] for s in run1["selected_samples"]] == [s["url"] for s in run2["selected_samples"]]


# ==============================================================================
# END-TO-END PIPELINE & RUNNER CLI TESTS
# ==============================================================================
class TestEndToEndPipelineAndRunner:
    """Kiểm thử tích hợp đầu-cuối và runner script thực tế."""

    def test_end_to_end_blocks_train_000_by_name_and_path(self, clean_pipeline):
        """[FIXTURE] Chặn đứng train-000 ngay tại Cổng 0."""
        with pytest.raises(SelectionGateError, match="CÁCH LY"):
            clean_pipeline.run_selection([], shard_path="train-000.parquet", skip_gate_0_file_check=False)

    def test_end_to_end_blocks_train_055_by_name_and_path(self, clean_pipeline):
        """[FIXTURE] Chặn đứng train-055 ngay tại Cổng 0."""
        with pytest.raises(SelectionGateError, match="CÁCH LY"):
            clean_pipeline.run_selection([], shard_path="train-055.parquet", skip_gate_0_file_check=False)

    def test_end_to_end_pipeline_with_injected_pilot_sample(self, clean_pipeline):
        """[FIXTURE] Tập ứng viên có 1 mẫu pilot lẫn vào -> Mẫu pilot bị loại ở Cổng 2, mẫu sạch qua đủ 5 cổng."""
        candidate_pool = [
            # Mẫu pilot giả lập bị tiêm vào
            {
                "url": MOCK_PILOT_RAW_URL,
                "html": MOCK_PILOT_RAW_HTML,
                "date": "2025-01-15",
            }
        ]
        tags = [
            "div", "section", "article", "main", "aside", "nav", "header", "footer",
            "table", "form", "figure", "details", "blockquote", "dialog", "canvas"
        ]
        # Thêm 15 mẫu sạch hợp lệ với cấu trúc đa dạng
        for i in range(15):
            t = tags[i % len(tags)]
            candidate_pool.append({
                "url": f"https://clean-candidate-{i}.org/page",
                "html": f"<html><body><{t}><p>Semantic distinct payload {i}</p></{t}></body></html>",
                "date": "2025-01-15",
            })

        res = clean_pipeline.run_selection(candidate_pool, target_quota=10, seed=42, skip_gate_0_file_check=True)
        assert len(res["selected_samples"]) == 10
        # Xác nhận mẫu pilot không bao giờ lọt vào kết quả cuối cùng
        selected_urls = [s["url"] for s in res["selected_samples"]]
        assert MOCK_PILOT_RAW_URL not in selected_urls
        assert res["audit_log"]["rejections"]["reject_exclusion_registry_match"] == 1

    def test_runner_cli_rejects_quarantined_shard(self):
        """[RUNNER INTEGRATION] Chạy script CLI run_main_selection.py với shard bị cách ly -> Dừng an toàn (exit code 1)."""
        cmd = [
            sys.executable,
            "scripts/data/run_main_selection.py",
            "--shard-path",
            "train-000.parquet",
            "--quota",
            "100",
        ]
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="replace", env=env)
        assert proc.returncode == 1
        assert "CÁCH LY" in proc.stderr
