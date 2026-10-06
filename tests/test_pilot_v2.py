"""Bộ kiểm thử hồi quy cho Gói Pilot Mới REAL-PILOT-32-V2 và Quy chuẩn Xử lý Sự cố (Task LABEL-01).

Kiểm tra:
1. configs/pilot_manifest.json (V1) được đánh dấu invalidated, ready_for_annotation=False.
2. configs/pilot_manifest_v2.json ghi D/B và exposure approved, vẫn chờ lệnh mở Pass 1.
3. Mã băm SHA-256 trong manifest V2 khớp byte thực tế của blind view, codebook, dictionary.
4. data/annotations/blind_view_pilot_real_v2.json mù hóa 100% (không chứa source_label, target_org, group_id).
5. Kiểm định URL/HTML/nhóm/view không trùng các lô practice, V1, audit và V2 cũ.
6. Registry chính giữ các loại trừ cũ, bổ sung V2 mới và vẫn chặn huấn luyện.
"""

import hashlib
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_V1_PATH = REPO_ROOT / "configs" / "pilot_manifest.json"
MANIFEST_V2_PATH = REPO_ROOT / "configs" / "pilot_manifest_v2.json"
BLIND_VIEW_V2_PATH = REPO_ROOT / "data" / "annotations" / "blind_view_pilot_real_v2.json"
PRIVATE_V2_DIR = REPO_ROOT / "data" / "raw" / "recovery" / "pilot-v2-proposed-20261006"
SOURCE_MAPPING_V2_PATH = PRIVATE_V2_DIR / "source_mapping.json"
PRIOR_EVIDENCE_PATH = REPO_ROOT / "data" / "raw" / "recovery" / "pilot-v2-prepare-20261006" / "prior_evidence.json"
EXCLUSION_REGISTRY_PATH = REPO_ROOT / "data" / "exclusion_registry.json"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class TestPilotIncidentAndV2Package:
    """Kiểm tra xử lý sự cố pilot V1 và tính toàn vẹn của gói mới V2."""

    def test_v1_manifest_is_frozen_and_invalidated(self):
        """V1 manifest phải ở trạng thái invalidated và không được sẵn sàng gán nhãn."""
        assert MANIFEST_V1_PATH.exists()
        m1 = json.loads(MANIFEST_V1_PATH.read_text(encoding="utf-8"))
        assert m1.get("status") == "invalidated"
        assert m1.get("ready_for_annotation") is False
        assert "invalidation_metadata" in m1
        inv = m1["invalidation_metadata"]
        assert inv.get("status") == "invalidated"
        assert inv.get("usable_for_kappa_or_plan01") is False
        assert inv.get("superseded_by") == "REAL-PILOT-32-V2"

    def test_v2_manifest_structure_and_lock_status(self):
        """V2 manifest phải có dataset_id chuẩn, ready_for_annotation=False và chờ duyệt."""
        assert MANIFEST_V2_PATH.exists()
        m2 = json.loads(MANIFEST_V2_PATH.read_text(encoding="utf-8"))
        assert m2["dataset_id"] == "REAL-PILOT-32-V2"
        assert m2["sample_count"] == 32
        assert m2["ready_for_annotation"] is False
        assert m2["status"] == "pending_final_lead_release"
        assert m2["acceptance"] == {"B": "approved", "D": "approved"}
        assert m2["exposure_review"] == {"A": "approved", "B": "approved", "D": "approved"}
        assert "Lead D" in m2["exposure_review_provenance"]["A"]
        assert "not an A self-attestation" in m2["exposure_review_provenance"]["A"]
        assert m2["blind_view_review_B"]["reported_sha256"] == m2["blind_view_sha256"]
        assert m2["exclusion_registry_sha256"] == _sha256(EXCLUSION_REGISTRY_PATH.read_bytes())
        registry = json.loads(EXCLUSION_REGISTRY_PATH.read_text(encoding="utf-8"))
        rebuilt = next(e for e in registry["exclusions"] if e["exclusion_id"].startswith("EXCL-PILOT-02-REBUILD-"))
        assert rebuilt["n_samples"] == len(rebuilt["samples"]) == 32
        assert registry["training_blocked"] is True
        assert all(set(s) == {"url_sha256", "normalized_url_sha256", "html_sha256",
                              "group_sha256", "view_content_sha256"} for s in rebuilt["samples"])
        assert m2["blind_view_sha256"] == "e039c774ef5ff11b36786ccc8c762254974d89a4f4bfa7d5bc46b12e323ad1dc"
        assert m2["audit_trail"]["previous_pending_manifest_sha256"] == "be60d69953f19d88bc1993ac20ffef46531ce4d4837d0a34560ea508bd8910ac"
        assert m2["is_synthetic"] is False
        assert m2["official_test_used"] is False

    @pytest.mark.integration
    @pytest.mark.skipif(not BLIND_VIEW_V2_PATH.exists(), reason="Restricted V2 view is local only")
    def test_v2_manifest_checksums_match_actual_files(self):
        """Mã băm trong manifest V2 phải khớp 100% với nội dung các artifact trên đĩa."""
        m2 = json.loads(MANIFEST_V2_PATH.read_text(encoding="utf-8"))
        
        # Blind view V2 checksum
        assert BLIND_VIEW_V2_PATH.exists()
        actual_bv_hash = _sha256(BLIND_VIEW_V2_PATH.read_bytes())
        assert m2["blind_view_sha256"] == actual_bv_hash

        # Codebook & Dictionary checksum
        codebook_path = REPO_ROOT / "docs" / "CODEBOOK_V1.md"
        dict_path = REPO_ROOT / "configs" / "dictionary_v1.json"
        assert m2["codebook_sha256"] == _sha256(codebook_path.read_bytes())
        assert m2["dictionary_sha256"] == _sha256(dict_path.read_bytes())

    @pytest.mark.integration
    @pytest.mark.skipif(not BLIND_VIEW_V2_PATH.exists(), reason="Restricted V2 view is local only")
    def test_v2_blind_view_has_zero_leakage(self):
        """Blind view V2 phải chứa đúng 32 mẫu và hoàn toàn ẩn thông tin nhãn, gợi ý."""
        assert BLIND_VIEW_V2_PATH.exists()
        bv2 = json.loads(BLIND_VIEW_V2_PATH.read_text(encoding="utf-8"))
        assert bv2["dataset_id"] == "REAL-PILOT-32-V2"
        assert bv2["total_samples"] == 32
        assert len(bv2["samples"]) == 32

        forbidden_keys = {"source_label", "target_org", "target", "group_id", "source_path", "model_score"}
        sample_ids = set()
        for s in bv2["samples"]:
            sample_ids.add(s["sample_id"])
            for f_key in forbidden_keys:
                assert f_key not in s, f"Rò rỉ trường nhạy cảm '{f_key}' trong blind sample {s.get('sample_id')}!"
            assert "url" in s and s["url"].strip() != ""
            assert "page_text" in s
            assert "structure_summary" in s
            assert s.get("codebook_version") == "1.0.0"

        # Đảm bảo 32 ID độc nhất từ PILOT-001 đến PILOT-032
        assert len(sample_ids) == 32
        assert sample_ids == {f"PILOT-{i:03d}" for i in range(1, 33)}

    @pytest.mark.integration
    @pytest.mark.skipif(not SOURCE_MAPPING_V2_PATH.exists(), reason="Restricted V2 mapping is local only")
    def test_strict_three_tier_deduplication_between_v2_and_previous(self):
        """Đối chiếu URL, HTML, nhóm và view hash với tất cả lô cũ bằng chứng hạn chế."""
        from scripts.data.build_real_pilot_v2 import check_deduplication, load_blocked_entities
        mapping_v2 = json.loads(SOURCE_MAPPING_V2_PATH.read_text(encoding="utf-8"))
        assert len(mapping_v2) == 32
        blocked = load_blocked_entities(PRIOR_EVIDENCE_PATH, EXCLUSION_REGISTRY_PATH)
        check_deduplication(mapping_v2, blocked)

    @pytest.mark.integration
    @pytest.mark.skipif(not SOURCE_MAPPING_V2_PATH.exists(), reason="Restricted V2 mapping is local only")
    def test_exclusion_registry_contains_both_v1_and_v2(self):
        """Exclusion registry phải cô lập cả V1 (32 mẫu) và V2 (32 mẫu), cấm huấn luyện."""
        from phishing.data.exclusion import ExclusionRegistry

        assert json.loads(EXCLUSION_REGISTRY_PATH.read_text(encoding="utf-8"))["training_blocked"] is True
        reg = ExclusionRegistry(EXCLUSION_REGISTRY_PATH)
        assert reg.training_blocked is True
        with pytest.raises(RuntimeError, match="LỆNH CHẶN HUẤN LUYỆN CHÍNH"):
            reg.assert_training_allowed()

        data = json.loads(EXCLUSION_REGISTRY_PATH.read_text(encoding="utf-8"))
        excl_ids = {e["exclusion_id"] for e in data["exclusions"]}
        assert "EXCL-REAL-PILOT-32" in excl_ids
        assert "EXCL-PILOT-02" in excl_ids
        # Kiểm tra mẫu V2 bị chặn bởi registry
        mapping_v2 = json.loads(SOURCE_MAPPING_V2_PATH.read_text(encoding="utf-8"))
        assert len(mapping_v2) == 32
        assert all(reg.is_excluded({"url": rec["url"]}) for rec in mapping_v2)
