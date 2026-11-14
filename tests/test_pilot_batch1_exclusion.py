"""Bộ kiểm thử cho Cổng chọn mẫu 5 giai đoạn và Kiểm định loại trừ Pilot Lô 1 (Task DATA-02 / Lead D).

Quy chuẩn ARS & Fail-Closed Protocols:
1. Gate 0: Chặn đứng shard cách ly (train-000, train-055) và nguồn chưa duyệt (PhishVN).
2. Gate 1: Chặn URL sai định dạng, HTML rỗng hoặc vượt ngưỡng 2MB.
3. Gate 2: Cố ý đưa mẫu Pilot vào đường chọn mẫu -> Gate 2 phải CHẶN.
4. Gate 2: Cố ý đưa mẫu trùng domain với Pilot vào đường chọn mẫu -> Gate 2 phải CHẶN (chống rò rỉ tenant/domain).
5. Fail-Closed: Thiếu hồ sơ hạn chế -> Ném RuntimeError dừng an toàn.
6. Fail-Closed: Hồ sơ hạn chế sai SHA-256 cam kết -> Ném RuntimeError dừng an toàn.
7. Gate 3 & 4: Khử trùng lặp nội bộ và tính tái lập 100% qua Seed niêm phong.
"""

import hashlib
import json
from pathlib import Path
import pytest

from phishing.data.exclusion import ExclusionRegistry
from phishing.data.selection_gate import (
    SelectionGateError,
    SelectionGatePipeline,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOSSIER_PATH = PROJECT_ROOT / "data" / "restricted" / "pilot_batch1_recovery_dossier_restricted.json"
REGISTRY_PATH = PROJECT_ROOT / "data" / "exclusion_registry.json"


@pytest.fixture
def clean_pipeline():
    """Khởi tạo pipeline với cấu hình chuẩn."""
    return SelectionGatePipeline()


class TestGate0SourceAndShardQuarantine:
    """Kiểm tra Cổng 0: Cách ly nguồn và shard."""

    def test_gate0_rejects_quarantined_train_000(self, clean_pipeline):
        with pytest.raises(SelectionGateError, match="BỊ CÁCH LY"):
            clean_pipeline.gate_0_source_and_shard("phreshphish", "train-000.parquet")

    def test_gate0_rejects_quarantined_train_055(self, clean_pipeline):
        with pytest.raises(SelectionGateError, match="BỊ CÁCH LY"):
            clean_pipeline.gate_0_source_and_shard("phreshphish", "train-055.parquet")

    def test_gate0_rejects_unvetted_source_phishvn(self, clean_pipeline):
        with pytest.raises(SelectionGateError, match="chưa được phê duyệt"):
            clean_pipeline.gate_0_source_and_shard("PhishVN", "phishvn-001.parquet")

    def test_gate0_rejects_tampered_lfs_hash(self, clean_pipeline):
        with pytest.raises(SelectionGateError, match="không khớp với manifest"):
            clean_pipeline.gate_0_source_and_shard(
                "phreshphish",
                "train-001.parquet",
                shard_lfs_sha256="0000000000000000000000000000000000000000000000000000000000000000",
            )

    def test_gate0_accepts_valid_manifest_shard(self, clean_pipeline):
        assert clean_pipeline.gate_0_source_and_shard("phreshphish", "train-001.parquet") is True


class TestGate1FieldValidity:
    """Kiểm tra Cổng 1: Hợp lệ trường và ngưỡng ký tự."""

    def test_gate1_rejects_empty_url(self, clean_pipeline):
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "", "html": "<html>abc</html>"})
        assert ok is False
        assert reason == "reject_empty_url"

    def test_gate1_rejects_invalid_url_scheme(self, clean_pipeline):
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "ftp://example.com", "html": "<html>abc</html>"})
        assert ok is False
        assert reason == "reject_invalid_url_format"

    def test_gate1_rejects_empty_html(self, clean_pipeline):
        ok, reason = clean_pipeline.gate_1_field_validity({"url": "https://example.com", "html": ""})
        assert ok is False
        assert reason == "reject_empty_html"

    def test_gate1_rejects_oversized_html(self, clean_pipeline):
        sample = {"url": "https://example.com", "html": "a" * 2_000_001}
        ok, reason = clean_pipeline.gate_1_field_validity(sample)
        assert ok is False
        assert "reject_html_len_" in reason

    def test_gate1_accepts_valid_sample(self, clean_pipeline):
        sample = {"url": "https://example.com/test", "html": "<html>Valid Page Content</html>"}
        ok, reason = clean_pipeline.gate_1_field_validity(sample)
        assert ok is True
        assert reason == "passed"


class TestGate2AntiLeakageAndFailClosed:
    """Kiểm tra Cổng 2: Chống rò rỉ dữ liệu và cơ chế Fail-Closed."""

    def test_gate2_deliberate_injection_of_pilot_sample_is_blocked(self, clean_pipeline):
        """Cố ý đưa mẫu thuộc 20 mẫu Pilot vào -> Gate 2 phải CHẶN."""
        if not DOSSIER_PATH.exists():
            pytest.skip("Chưa tạo hồ sơ hạn chế pilot_batch1_recovery_dossier_restricted.json")

        dossier = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
        pilot_sample_0 = dossier["mapping"][0]

        # Giả lập mẫu nạp vào chứa url_sha256 của mẫu pilot
        injected_sample = {
            "url": "https://dummy-url.org",
            "url_sha256": pilot_sample_0["raw_url_sha256"],
            "html": "<html>Sample Content</html>",
        }
        ok, reason = clean_pipeline.gate_2_anti_leakage(injected_sample)
        assert ok is False
        assert reason == "reject_exclusion_registry_match"

    def test_gate2_deliberate_injection_of_domain_sharing_sample_is_blocked(self, clean_pipeline):
        """Cố ý đưa mẫu có URL khác nhưng cùng domain/tenant với Pilot vào -> Gate 2 phải CHẶN."""
        if not DOSSIER_PATH.exists():
            pytest.skip("Chưa tạo hồ sơ hạn chế")

        # Mẫu có URL hoàn toàn mới trên cùng eTLD+1 của Pilot 0 (lifeonthemediterranean.com)
        injected_sample = {
            "url": "https://subdomain.lifeonthemediterranean.com/new-article-2026",
            "html": "<html>Unique Content on Shared Tenant</html>",
        }
        ok, reason = clean_pipeline.gate_2_anti_leakage(injected_sample)
        assert ok is False
        assert reason == "reject_exclusion_registry_match"

    def test_missing_restricted_dossier_fails_closed(self, tmp_path):
        """Thiếu hồ sơ hạn chế đã đăng ký cam kết -> Ném RuntimeError dừng an toàn."""
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
            pipeline.gate_2_anti_leakage({"url": "https://example.com", "html": "abc"})

    def test_tampered_restricted_dossier_hash_fails_closed(self, tmp_path):
        """Hồ sơ hạn chế bị sửa đổi nội dung (sai SHA-256) -> Ném RuntimeError dừng an toàn."""
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


class TestGate3And4DeduplicationAndSampling:
    """Kiểm tra Cổng 3 và Cổng 4: Khử trùng lặp nội bộ và tính tái lập của phân tầng."""

    def test_gate3_deduplicates_url_html_and_domain(self, clean_pipeline):
        samples = [
            {"url": "https://site-a.com/page1", "html": "<html>A</html>"},
            {"url": "https://site-a.com/page1", "html": "<html>A</html>"},  # Trùng URL & HTML
            {"url": "https://site-a.com/page2", "html": "<html>Different</html>"},  # Trùng Domain site-a.com
            {"url": "https://site-b.com/page1", "html": "<html>B</html>"},
        ]
        res = clean_pipeline.run_selection(samples, shard_name="train-001.parquet", target_quota=10, seed=123)
        assert res["audit_log"]["gate_counts"]["gate_3_in"] == 4
        assert res["audit_log"]["gate_counts"]["gate_3_out"] == 2
        assert res["audit_log"]["rejections"]["reject_gate3_duplicate_url"] == 1
        assert res["audit_log"]["rejections"]["reject_gate3_domain_collision"] == 1

    def test_gate4_seeded_sampling_is_deterministic(self, clean_pipeline):
        samples = [{"url": f"https://site-{i}.com/", "html": f"<html>{i}</html>"} for i in range(50)]
        res1 = clean_pipeline.run_selection(samples, shard_name="train-001.parquet", target_quota=10, seed=999)
        res2 = clean_pipeline.run_selection(samples, shard_name="train-001.parquet", target_quota=10, seed=999)
        res3 = clean_pipeline.run_selection(samples, shard_name="train-001.parquet", target_quota=10, seed=111)

        urls1 = [s["url"] for s in res1["selected_samples"]]
        urls2 = [s["url"] for s in res2["selected_samples"]]
        urls3 = [s["url"] for s in res3["selected_samples"]]

        assert urls1 == urls2, "Cùng seed phải cho thứ tự và danh sách mẫu giống hệt 100%"
        assert urls1 != urls3, "Khác seed phải cho thứ tự khác nhau"
