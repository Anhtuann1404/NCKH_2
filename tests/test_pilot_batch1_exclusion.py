"""Bộ kiểm thử cho Cổng chọn mẫu 5 giai đoạn và Kiểm định loại trừ Pilot Lô 1 (Task DATA-02 / Lead D).

Phân định rõ ràng:
- [FIXTURE]: Các ca kiểm thử dùng dữ liệu giả lập (synthetic fixtures) để kiểm tra logic từng cổng và biên lỗi.
- [REAL SHARD]: Các ca kiểm thử chạy trực tiếp trên tệp shard parquet thật trong data/raw/phreshphish/data/.

Quy chuẩn ARS & Fail-Closed Protocols:
1. Gate 0: Chặn đứng shard cách ly (train-000, train-055), nguồn chưa duyệt (PhishVN), sai revision, sai/thiếu hash byte tệp thực tế.
2. Gate 1: Chặn URL sai định dạng, HTML rỗng hoặc vượt ngưỡng 2MB, ngày thiếu/sai định dạng hoặc ngoài cửa sổ.
3. Gate 2: Cố ý đưa URL thô, HTML thô, HTML làm sạch, hoặc tên miền của mẫu Pilot vào -> Gate 2 phải CHẶN.
4. Gate 2 Fail-Closed: Thiếu hồ sơ hạn chế hoặc sai SHA-256 cam kết -> Ném RuntimeError dừng an toàn.
5. Gate 3: Khử trùng lặp nội bộ (URL, HTML, Domain diversity: max 1/domain) và chặn template clone/near-duplicate.
6. Gate 4: Bắt buộc đủ quota mẫu (thiếu quota ném SelectionGateError dừng an toàn) và tái lập 100% qua Seed niêm phong.
7. End-to-end: Chạy toàn pipeline và kiểm thử runner Main thực tế.
"""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
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
    compute_template_skeleton_hash,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOSSIER_PATH = PROJECT_ROOT / "data" / "restricted" / "pilot_batch1_recovery_dossier_restricted.json"
REAL_TRAIN_000_PATH = PROJECT_ROOT / "data" / "raw" / "phreshphish" / "data" / "train-000.parquet"
REAL_TRAIN_055_PATH = PROJECT_ROOT / "data" / "raw" / "phreshphish" / "data" / "train-055.parquet"


@pytest.fixture
def clean_pipeline():
    """Khởi tạo pipeline với cấu hình chuẩn."""
    return SelectionGatePipeline()


# ==============================================================================
# CỔNG 0: KIỂM ĐỊNH TÍNH TOÀN VẸN SHARD VÀ NGUỒN (GATE 0)
# ==============================================================================
class TestGate0SourceAndShardIntegrity:
    """Kiểm tra Cổng 0: Cách ly nguồn, kiểm tra revision và mã băm byte thực tế."""

    def test_gate0_rejects_quarantined_train_000_real_and_named(self, clean_pipeline):
        """[REAL SHARD & FIXTURE] Shard train-000 chứa vết pilot phải bị Cổng 0 chặn đứng."""
        with pytest.raises(SelectionGateError, match="BỊ CÁCH LY"):
            clean_pipeline.gate_0_source_and_shard(DEFAULT_APPROVED_SOURCE, REAL_TRAIN_000_PATH)

        with pytest.raises(SelectionGateError, match="BỊ CÁCH LY"):
            clean_pipeline.gate_0_source_and_shard(DEFAULT_APPROVED_SOURCE, "train-000.parquet")

    def test_gate0_rejects_quarantined_train_055_real_and_named(self, clean_pipeline):
        """[REAL SHARD & FIXTURE] Shard train-055 chứa vết pilot extra phải bị Cổng 0 chặn đứng."""
        with pytest.raises(SelectionGateError, match="BỊ CÁCH LY"):
            clean_pipeline.gate_0_source_and_shard(DEFAULT_APPROVED_SOURCE, REAL_TRAIN_055_PATH)

        with pytest.raises(SelectionGateError, match="BỊ CÁCH LY"):
            clean_pipeline.gate_0_source_and_shard(DEFAULT_APPROVED_SOURCE, "train-055.parquet")

    def test_gate0_rejects_unvetted_source_phishvn(self, clean_pipeline):
        """[FIXTURE] Nguồn PhishVN chưa được phê duyệt trích xuất độc lập phải bị chặn."""
        with pytest.raises(SelectionGateError, match="chưa được phê duyệt"):
            clean_pipeline.gate_0_source_and_shard("PhishVN", "phishvn-001.parquet")

    def test_gate0_rejects_arbitrary_unapproved_source(self, clean_pipeline):
        """[FIXTURE] Nguồn không nằm trong danh mục được duyệt bị từ chối."""
        with pytest.raises(SelectionGateError, match="không khớp với nguồn được duyệt"):
            clean_pipeline.gate_0_source_and_shard("unapproved_dataset", "sample.parquet")

    def test_gate0_rejects_unapproved_revision(self, clean_pipeline):
        """[FIXTURE] Revision bị thay đổi không khớp với manifest đã khóa phải bị từ chối."""
        with pytest.raises(SelectionGateError, match="không khớp với revision đã khóa"):
            clean_pipeline.gate_0_source_and_shard(
                DEFAULT_APPROVED_SOURCE,
                REAL_TRAIN_000_PATH,
                revision="1111222233334444555566667777888899990000",
            )

    def test_gate0_rejects_non_existent_shard_file(self, clean_pipeline):
        """[FIXTURE] Tệp shard không tồn tại trên đĩa phải ném SelectionGateError."""
        with pytest.raises(SelectionGateError, match="Không tìm thấy tệp shard thực tế"):
            clean_pipeline.gate_0_source_and_shard(DEFAULT_APPROVED_SOURCE, "data/non_existent_shard.parquet")

    def test_gate0_rejects_shard_not_in_manifest(self, clean_pipeline, tmp_path):
        """[FIXTURE] Tệp shard tồn tại trên đĩa nhưng không có trong manifest bị chặn."""
        fake_parquet = tmp_path / "unknown-shard-999.parquet"
        fake_parquet.write_bytes(b"PAR1dummybytes")
        with pytest.raises(SelectionGateError, match="không tồn tại trong source_manifest"):
            clean_pipeline.gate_0_source_and_shard(DEFAULT_APPROVED_SOURCE, fake_parquet)

    def test_gate0_rejects_tampered_shard_actual_bytes(self, tmp_path):
        """[FIXTURE] Tệp shard có tên đúng trong manifest nhưng byte thực tế bị sai mã băm -> FAIL-CLOSED."""
        manifest_file = tmp_path / "source_manifest.json"
        manifest_file.write_text(json.dumps({
            "revision": DEFAULT_APPROVED_REVISION,
            "files": [
                {
                    "file_name": "train-010.parquet",
                    "source_metadata_lfs_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                }
            ]
        }), encoding="utf-8")

        tampered_shard = tmp_path / "train-010.parquet"
        tampered_shard.write_bytes(b"PAR1corruptedcontent")

        pipeline = SelectionGatePipeline(source_manifest_path=manifest_file)
        with pytest.raises(SelectionGateError, match="không khớp với mã băm trong manifest"):
            pipeline.gate_0_source_and_shard(DEFAULT_APPROVED_SOURCE, tampered_shard)

    def test_gate0_accepts_valid_shard_with_matching_bytes(self, tmp_path):
        """[FIXTURE] Tệp shard tồn tại, đúng nguồn, đúng revision và mã băm byte thực tế khớp -> ĐẠT."""
        valid_shard = tmp_path / "train-010.parquet"
        valid_bytes = b"PAR1validparquetcontenttest"
        valid_shard.write_bytes(valid_bytes)
        expected_sha = hashlib.sha256(valid_bytes).hexdigest()

        manifest_file = tmp_path / "source_manifest.json"
        manifest_file.write_text(json.dumps({
            "revision": DEFAULT_APPROVED_REVISION,
            "files": [
                {
                    "file_name": "train-010.parquet",
                    "source_metadata_lfs_sha256": expected_sha,
                }
            ]
        }), encoding="utf-8")

        pipeline = SelectionGatePipeline(source_manifest_path=manifest_file)
        assert pipeline.gate_0_source_and_shard(DEFAULT_APPROVED_SOURCE, valid_shard) is True


# ==============================================================================
# CỔNG 1: HỢP LỆ TRƯỜNG, KÝ TỰ HTML VÀ CỬA SỔ NGÀY BẮT BUỘC (GATE 1)
# ==============================================================================
class TestGate1FieldValidityAndDates:
    """Kiểm tra Cổng 1: URL, HTML và ngày bắt buộc trong cửa sổ thời gian."""

    def test_gate1_rejects_empty_url(self, clean_pipeline):
        """[FIXTURE] URL rỗng bị từ chối."""
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "", "html": "<html>abc</html>", "date": "2025-08-25"})
        assert ok is False
        assert reason == "reject_empty_url"

    def test_gate1_rejects_invalid_url_scheme(self, clean_pipeline):
        """[FIXTURE] URL không có scheme HTTP/HTTPS bị từ chối."""
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "ftp://example.com", "html": "<html>abc</html>", "date": "2025-08-25"})
        assert ok is False
        assert reason == "reject_invalid_url_format"

    def test_gate1_rejects_empty_html(self, clean_pipeline):
        """[FIXTURE] HTML rỗng bị từ chối."""
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": "", "date": "2025-08-25"})
        assert ok is False
        assert reason == "reject_empty_html"

    def test_gate1_rejects_oversized_html(self, clean_pipeline):
        """[FIXTURE] HTML vượt quá 2MB bị từ chối."""
        sample = {"url": "https://example.com", "html": "a" * 2_000_001, "date": "2025-08-25"}
        ok, reason = clean_pipeline.gate_1_field_validity(sample)
        assert ok is False
        assert "reject_html_len_" in reason

    def test_gate1_rejects_missing_date(self, clean_pipeline):
        """[FIXTURE] Thiếu trường ngày bị từ chối (quy chuẩn ARS bắt buộc)."""
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": "<html>abc</html>"})
        assert ok is False
        assert reason == "reject_missing_date"

        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": "<html>abc</html>", "date": None})
        assert ok is False
        assert reason == "reject_missing_date"

    def test_gate1_rejects_invalid_date_format(self, clean_pipeline):
        """[FIXTURE] Ngày sai định dạng bị từ chối."""
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": "<html>abc</html>", "date": "invalid-date"})
        assert ok is False
        assert reason == "reject_invalid_date_format"

    def test_gate1_rejects_date_before_min(self, clean_pipeline):
        """[FIXTURE] Ngày trước min_date (2024-07-04) bị từ chối."""
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": "<html>abc</html>", "date": "2024-01-01"})
        assert ok is False
        assert "reject_date_before_min" in reason

    def test_gate1_rejects_date_after_max(self, clean_pipeline):
        """[FIXTURE] Ngày sau max_date (2025-09-08) bị từ chối."""
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": "<html>abc</html>", "date": "2025-12-31"})
        assert ok is False
        assert "reject_date_after_max" in reason

    def test_gate1_accepts_valid_sample(self, clean_pipeline):
        """[FIXTURE] Mẫu hợp lệ URL, HTML và ngày trong cửa sổ thời gian -> ĐẠT."""
        sample = {"url": "https://example.com/test", "html": "<html>Valid Page Content</html>", "date": "2025-08-25"}
        ok, reason = clean_pipeline.gate_1_field_validity(sample)
        assert ok is True
        assert reason == "passed"


# ==============================================================================
# CỔNG 2: CHỐNG RÒ RỈ LOẠI TRỪ VÀ FAIL-CLOSED (GATE 2)
# ==============================================================================
class TestGate2CryptographicAntiLeakage:
    """Kiểm tra Cổng 2: Chặn mẫu pilot và cơ chế Fail-Closed."""

    def test_gate2_deliberate_injection_of_raw_url_of_pilot_sample(self, clean_pipeline):
        """[REAL SHARD & DOSSIER] Đưa URL thô của mẫu Pilot Lô 1 vào -> BỊ CHẶN."""
        if not REAL_TRAIN_000_PATH.exists():
            pytest.skip("Chưa có shard train-000 cục bộ")

        # Đọc trực tiếp URL thô từ hàng 0 của train-000.parquet
        table = pq.read_table(REAL_TRAIN_000_PATH)
        pilot_row_0 = table.slice(0, 1).to_pandas().iloc[0]

        injected_sample = {
            "url": pilot_row_0["url"],
            "html": "<html>Different Content But Same URL</html>",
            "date": "2025-08-25",
        }
        ok, reason = clean_pipeline.gate_2_anti_leakage(injected_sample)
        assert ok is False
        assert reason == "reject_exclusion_registry_match"

    def test_gate2_deliberate_injection_of_raw_html_of_pilot_sample(self, clean_pipeline):
        """[REAL SHARD & DOSSIER] Đưa HTML thô của mẫu Pilot Lô 1 vào -> BỊ CHẶN."""
        if not REAL_TRAIN_000_PATH.exists():
            pytest.skip("Chưa có shard train-000 cục bộ")

        table = pq.read_table(REAL_TRAIN_000_PATH)
        pilot_row_0 = table.slice(0, 1).to_pandas().iloc[0]

        injected_sample = {
            "url": "https://completely-new-unseen-url.com/page",
            "html": pilot_row_0["html"],
            "date": "2025-08-25",
        }
        ok, reason = clean_pipeline.gate_2_anti_leakage(injected_sample)
        assert ok is False
        assert reason == "reject_exclusion_registry_match"

    def test_gate2_deliberate_injection_of_domain_sharing_sample(self, clean_pipeline):
        """[FIXTURE & REGISTRY] Đưa mẫu có tên miền chia sẻ với Pilot (lifeonthemediterranean.com) -> BỊ CHẶN."""
        injected_sample = {
            "url": "https://blog.lifeonthemediterranean.com/new-article-2026",
            "html": "<html>Fresh unique content on shared domain</html>",
            "date": "2025-08-25",
        }
        ok, reason = clean_pipeline.gate_2_anti_leakage(injected_sample)
        assert ok is False
        assert reason == "reject_exclusion_registry_match"

    def test_gate2_missing_restricted_dossier_fails_closed(self, tmp_path):
        """[FIXTURE] Thiếu hồ sơ hạn chế đã cam kết -> FAIL-CLOSED ném RuntimeError."""
        reg_file = tmp_path / "registry.json"
        reg_file.write_text(json.dumps({
            "version": "1.1.0",
            "training_blocked": True,
            "exclusions": [
                {
                    "exclusion_id": "EXCL-TEST-PUBLIC",
                    "samples": [{"url_sha256": "11112222333344445555666677778888"}]
                },
                {
                    "exclusion_id": "EXCL-TEST-MISSING",
                    "status": "sealed_restricted_commitment",
                    "restricted_dossier_reference": "data/restricted/non_existent_file.json",
                    "commitment_sha256": "abcdef123456",
                    "samples": []
                }
            ]
        }), encoding="utf-8")

        reg = ExclusionRegistry(registry_path=reg_file)
        pipeline = SelectionGatePipeline(exclusion_registry=reg)

        with pytest.raises(RuntimeError, match="LỆNH CHẶN FAIL-CLOSED"):
            pipeline.gate_2_anti_leakage({"url": "https://example.com", "html": "abc", "date": "2025-08-25"})

    def test_gate2_tampered_restricted_dossier_hash_fails_closed(self, tmp_path):
        """[FIXTURE] Hồ sơ hạn chế bị sửa sai SHA-256 -> FAIL-CLOSED ném RuntimeError."""
        dossier_fake = tmp_path / "fake_dossier.json"
        dossier_fake.write_text(json.dumps({"mapping": []}), encoding="utf-8")

        reg_file = tmp_path / "registry.json"
        reg_file.write_text(json.dumps({
            "version": "1.1.0",
            "training_blocked": True,
            "exclusions": [
                {
                    "exclusion_id": "EXCL-TEST-TAMPERED",
                    "status": "sealed_restricted_commitment",
                    "restricted_dossier_reference": str(dossier_fake),
                    "commitment_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                    "samples": []
                }
            ]
        }), encoding="utf-8")

        with pytest.raises(RuntimeError, match="LỖI TOÀN VẸN HỒ SƠ HẠN CHẾ"):
            ExclusionRegistry(registry_path=reg_file)


# ==============================================================================
# CỔNG 3: KHỬ TRÙNG LẶP NỘI BỘ VÀ CLONE TEMPLATE (GATE 3)
# ==============================================================================
class TestGate3DeduplicationAndTemplateClones:
    """Kiểm tra Cổng 3: Khử trùng lặp URL, HTML, Domain diversity và Template skeleton."""

    def test_gate3_deduplicates_exact_url_and_html(self, clean_pipeline):
        """[FIXTURE] Trùng URL hoặc trùng HTML trong cùng đợt bị Cổng 3 loại bỏ."""
        samples = [
            {"url": "https://site-a.com/page1", "html": "<html><body><div>Unique A</div></body></html>", "date": "2025-08-25"},
            {"url": "https://site-a.com/page1", "html": "<html><body><div>Unique A</div></body></html>", "date": "2025-08-25"},  # Trùng URL
            {"url": "https://site-b.com/page1", "html": "<html><body><div>Unique A</div></body></html>", "date": "2025-08-25"},  # Trùng HTML
            {"url": "https://site-c.com/page1", "html": "<html><body><article><section><p>C</p></section></article></body></html>", "date": "2025-08-25"},
        ]
        res = clean_pipeline.run_selection(samples, target_quota=2, seed=42, skip_gate_0_file_check=True)
        assert res["audit_log"]["gate_counts"]["gate_3_in"] == 4
        assert res["audit_log"]["gate_counts"]["gate_3_out"] == 2
        assert res["audit_log"]["rejections"]["reject_gate3_duplicate_url"] == 1
        assert res["audit_log"]["rejections"]["reject_gate3_duplicate_html"] == 1

    def test_gate3_enforces_domain_diversity(self, clean_pipeline):
        """[FIXTURE] Tối đa 1 mẫu cho mỗi domain (eTLD+1); mẫu thứ hai cùng domain bị loại."""
        samples = [
            {"url": "https://service.domain-one.com/login", "html": "<html><body><div>Form 1</div></body></html>", "date": "2025-08-25"},
            {"url": "https://portal.domain-one.com/auth", "html": "<html><body><section><span>Form 2</span></section></body></html>", "date": "2025-08-25"},  # Cùng domain-one.com
            {"url": "https://site-two.com/index", "html": "<html><body><article><p>Normal Page</p></article></body></html>", "date": "2025-08-25"},
        ]
        res = clean_pipeline.run_selection(samples, target_quota=2, seed=42, skip_gate_0_file_check=True)
        assert res["audit_log"]["rejections"]["reject_gate3_domain_collision"] == 1
        assert len(res["selected_samples"]) == 2

    def test_gate3_sequential_template_clone_rejection(self, clean_pipeline):
        """[FIXTURE] Hai trang có text và domain khác nhau nhưng chung khung sườn tag HTML (phishing kit) -> BỊ LOẠI."""
        # Trang 1: Kit giả mạo ngân hàng A
        html1 = (
            "<html><head><title>Bank A</title></head><body>"
            "<h1>Sign In</h1>"
            "<form action='/login'><input type='text'/><input type='password'/><button>Submit</button></form>"
            "</body></html>"
        )
        # Trang 2: Kit tương tự chỉ đổi text thành ngân hàng B trên domain khác
        html2 = (
            "<html><head><title>Bank B Verification</title></head><body>"
            "<h1>Identity Verification</h1>"
            "<form action='/verify'><input type='text'/><input type='password'/><button>Continue</button></form>"
            "</body></html>"
        )

        samples = [
            {"url": "https://auth-portal-alpha.net/login.html", "html": html1, "date": "2025-08-25"},
            {"url": "https://secure-gate-beta.org/verify.html", "html": html2, "date": "2025-08-25"},
            {"url": "https://normal-article.info/read", "html": "<html><body><article><section><p>Unrelated Article</p></section></article></body></html>", "date": "2025-08-25"},
        ]
        res = clean_pipeline.run_selection(samples, target_quota=2, seed=42, skip_gate_0_file_check=True)
        assert res["audit_log"]["rejections"]["reject_gate3_template_clone"] == 1
        assert len(res["selected_samples"]) == 2


# ==============================================================================
# CỔNG 4: THỰC THI QUOTA VÀ CHỌN MẪU TÁI LẬP (GATE 4)
# ==============================================================================
class TestGate4QuotaAndSampling:
    """Kiểm tra Cổng 4: Quota enforcement fail-closed và tính xác định của PRNG."""

    def test_gate4_insufficient_quota_fails_closed(self, clean_pipeline):
        """[FIXTURE] Khi số ứng viên sạch sau Cổng 3 không đủ target_quota -> Ném SelectionGateError dừng an toàn."""
        samples = [
            {"url": f"https://site-{i}.com/page", "html": f"<html><body><div><p>{'<span>t</span>'*i}</p></div></body></html>", "date": "2025-08-25"}
            for i in range(5)
        ]
        # Yêu cầu quota 10 nhưng chỉ có 5 mẫu
        with pytest.raises(SelectionGateError, match="không đạt chỉ tiêu quota yêu cầu"):
            clean_pipeline.run_selection(samples, target_quota=10, seed=42, skip_gate_0_file_check=True)

    def test_gate4_seeded_sampling_is_deterministic(self, clean_pipeline):
        """[FIXTURE] Cùng seed cho danh sách mẫu giống hệt 100%; khác seed cho thứ tự khác."""
        samples = [
            {"url": f"https://site-{i}.com/page", "html": f"<html><body><div><p>{'<span>t</span>'*i}</p></div></body></html>", "date": "2025-08-25"}
            for i in range(30)
        ]
        res1 = clean_pipeline.run_selection(samples, target_quota=10, seed=999, skip_gate_0_file_check=True)
        res2 = clean_pipeline.run_selection(samples, target_quota=10, seed=999, skip_gate_0_file_check=True)
        res3 = clean_pipeline.run_selection(samples, target_quota=10, seed=111, skip_gate_0_file_check=True)

        urls1 = [s["url"] for s in res1["selected_samples"]]
        urls2 = [s["url"] for s in res2["selected_samples"]]
        urls3 = [s["url"] for s in res3["selected_samples"]]

        assert urls1 == urls2, "Cùng seed phải cho kết quả giống hệt 100%"
        assert urls1 != urls3, "Khác seed phải cho kết quả thứ tự khác nhau"


# ==============================================================================
# END-TO-END PIPELINE VÀ RUNNER THỰC TẾ (END-TO-END)
# ==============================================================================
class TestEndToEndPipelineAndRunner:
    """Kiểm tra toàn diện đường chạy và runner Main thực tế."""

    def test_end_to_end_blocks_real_train_000_at_gate_0(self):
        """[REAL SHARD] Runner thực tế phải chặn đứng train-000.parquet ngay tại Cổng 0."""
        pipeline = SelectionGatePipeline()
        with pytest.raises(SelectionGateError, match="BỊ CÁCH LY"):
            pipeline.gate_0_source_and_shard(DEFAULT_APPROVED_SOURCE, REAL_TRAIN_000_PATH)

    def test_end_to_end_blocks_real_train_055_at_gate_0(self):
        """[REAL SHARD] Runner thực tế phải chặn đứng train-055.parquet ngay tại Cổng 0."""
        pipeline = SelectionGatePipeline()
        with pytest.raises(SelectionGateError, match="BỊ CÁCH LY"):
            pipeline.gate_0_source_and_shard(DEFAULT_APPROVED_SOURCE, REAL_TRAIN_055_PATH)

    def test_end_to_end_pipeline_with_injected_pilot_sample(self, clean_pipeline):
        """[REAL SHARD & FIXTURE] Tạo tập ứng viên có 1 mẫu pilot thật lẫn vào -> Mẫu pilot bị loại ở Cổng 2, các mẫu sạch qua đủ 5 cổng."""
        if not REAL_TRAIN_000_PATH.exists():
            pytest.skip("Chưa có shard train-000")

        table = pq.read_table(REAL_TRAIN_000_PATH)
        pilot_row_0 = table.slice(0, 1).to_pandas().iloc[0]

        candidate_pool = [
            # Mẫu pilot bị tiêm vào
            {
                "url": pilot_row_0["url"],
                "html": pilot_row_0["html"],
                "date": "2025-08-25",
            }
        ]
        # Thêm 15 mẫu sạch hợp lệ với khung cấu trúc đa dạng
        for i in range(15):
            candidate_pool.append({
                "url": f"https://clean-candidate-{i}.org/page",
                "html": f"<html><body><div><p>{'<span>content</span>'*i}</p></div></body></html>",
                "date": "2025-08-25",
            })

        res = clean_pipeline.run_selection(candidate_pool, target_quota=10, seed=42, skip_gate_0_file_check=True)
        # Mẫu pilot bị chặn tại Cổng 2
        assert res["audit_log"]["rejections"]["reject_exclusion_registry_match"] == 1
        # Cổng 4 rút đủ 10 mẫu sạch
        assert len(res["selected_samples"]) == 10
        assert all("clean-candidate-" in s["url"] for s in res["selected_samples"])

    def test_runner_cli_rejects_quarantined_shard(self):
        """[CLI & REAL SHARD] Kiểm tra runner CLI scripts/data/run_main_selection.py dừng an toàn với exit code 1."""
        import os
        cmd = [
            sys.executable,
            "scripts/data/run_main_selection.py",
            "--shard-path", str(REAL_TRAIN_000_PATH),
            "--quota", "10",
        ]
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        assert result.returncode == 1
        assert "FAIL-CLOSED" in result.stderr
        assert "CÁCH LY" in result.stderr
