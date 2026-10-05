"""Bộ kiểm thử hồi quy cho Gói Pilot Mới REAL-PILOT-32-V2 và Quy chuẩn Xử lý Sự cố (Task LABEL-01).

Kiểm tra:
1. configs/pilot_manifest.json (V1) được đánh dấu invalidated, ready_for_annotation=False.
2. configs/pilot_manifest_v2.json tồn tại, trạng thái pending_lead_acceptance, ready_for_annotation=False.
3. Mã băm SHA-256 trong manifest V2 khớp byte thực tế của blind view, source mapping, codebook, dictionary.
4. data/annotations/blind_view_pilot_real_v2.json mù hóa 100% (không chứa source_label, target_org, group_id).
5. Kiểm định 3 tầng chống trùng lặp: Zero URL, Zero HTML hash, Zero Domain Group overlap giữa V2 và (V1 + practice).
6. data/exclusion_registry.json cô lập cả 64 mẫu pilot (V1 + V2) và chặn huấn luyện (training_blocked=True).
"""

import hashlib
import json
from pathlib import Path
import pytest
import tldextract

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_V1_PATH = REPO_ROOT / "configs" / "pilot_manifest.json"
MANIFEST_V2_PATH = REPO_ROOT / "configs" / "pilot_manifest_v2.json"
BLIND_VIEW_V1_PATH = REPO_ROOT / "data" / "annotations" / "blind_view_pilot_real.json"
BLIND_VIEW_V2_PATH = REPO_ROOT / "data" / "annotations" / "blind_view_pilot_real_v2.json"
PRACTICE_VIEW_PATH = REPO_ROOT / "data" / "annotations" / "blind_view_pilot.json"
SOURCE_MAPPING_V2_PATH = REPO_ROOT / "data" / "raw" / "pilot_v2" / "source_mapping.json"
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
        assert m2["source_class_counts"] == {"phish": 20, "benign": 12}
        assert m2["ready_for_annotation"] is False
        assert m2["status"] == "pending_lead_acceptance"
        assert m2["acceptance"] == {"B": "pending", "D": "pending"}
        assert m2["is_synthetic"] is False
        assert m2["official_test_used"] is False

    def test_v2_manifest_checksums_match_actual_files(self):
        """Mã băm trong manifest V2 phải khớp 100% với nội dung các artifact trên đĩa."""
        m2 = json.loads(MANIFEST_V2_PATH.read_text(encoding="utf-8"))
        
        # Blind view V2 checksum
        assert BLIND_VIEW_V2_PATH.exists()
        actual_bv_hash = _sha256(BLIND_VIEW_V2_PATH.read_bytes())
        assert m2["blind_view_sha256"] == actual_bv_hash

        # Source mapping V2 checksum
        assert SOURCE_MAPPING_V2_PATH.exists()
        actual_mapping_hash = _sha256(SOURCE_MAPPING_V2_PATH.read_bytes())
        assert m2["restricted_source_mapping_sha256"] == actual_mapping_hash

        # Codebook & Dictionary checksum
        codebook_path = REPO_ROOT / "docs" / "CODEBOOK_V1.md"
        dict_path = REPO_ROOT / "configs" / "dictionary_v1.json"
        assert m2["codebook_sha256"] == _sha256(codebook_path.read_bytes())
        assert m2["dictionary_sha256"] == _sha256(dict_path.read_bytes())

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

    def test_strict_three_tier_deduplication_between_v2_and_previous(self):
        """Kiểm định 3 tầng chống trùng lặp: V2 không trùng URL, HTML, hoặc domain group với V1/tập dượt."""
        # 1. Thu thập dữ liệu cấm từ V1 và tập dượt
        forbidden_urls = set()
        forbidden_html_hashes = set()
        forbidden_domain_groups = set()

        # Từ V1
        if BLIND_VIEW_V1_PATH.exists():
            bv1 = json.loads(BLIND_VIEW_V1_PATH.read_text(encoding="utf-8"))
            for s in bv1.get("samples", []):
                u = s["url"].strip().lower()
                forbidden_urls.add(u)
                ext = tldextract.extract(u)
                dom = ext.top_domain_under_public_suffix
                if dom:
                    forbidden_domain_groups.add(dom.lower())

        # Từ tập dượt
        if PRACTICE_VIEW_PATH.exists():
            bvp = json.loads(PRACTICE_VIEW_PATH.read_text(encoding="utf-8"))
            for s in bvp.get("samples", []):
                u = s["url"].strip().lower()
                forbidden_urls.add(u)
                ext = tldextract.extract(u)
                dom = ext.top_domain_under_public_suffix
                if dom:
                    forbidden_domain_groups.add(dom.lower())

        # Từ Exclusion Registry (V1 hashes)
        reg = json.loads(EXCLUSION_REGISTRY_PATH.read_text(encoding="utf-8"))
        for excl in reg.get("exclusions", []):
            if excl.get("exclusion_id") in ("EXCL-REAL-PILOT-32", "EXCL-PILOT-01"):
                for smp in excl.get("samples", []):
                    if "html_sha256" in smp:
                        forbidden_html_hashes.add(smp["html_sha256"])

        # 2. Đối chiếu với 32 mẫu V2
        assert SOURCE_MAPPING_V2_PATH.exists()
        mapping_v2 = json.loads(SOURCE_MAPPING_V2_PATH.read_text(encoding="utf-8"))
        assert len(mapping_v2) == 32

        v2_domain_groups = set()
        for rec in mapping_v2:
            u_clean = rec["raw_url"].strip().lower()
            u_norm = rec["normalized_url"].strip().lower() if "normalized_url" in rec else u_clean
            
            # Tầng 1: URL trùng lặp
            assert u_clean not in forbidden_urls, f"URL V2 trùng lặp với tập cũ: {u_clean}"
            assert u_norm not in forbidden_urls, f"Normalized URL V2 trùng lặp với tập cũ: {u_norm}"

            # Tầng 2: HTML byte hash trùng lặp
            html_hash = rec["html_sha256"]
            assert html_hash not in forbidden_html_hashes, f"HTML hash V2 trùng lặp: {html_hash}"

            # Tầng 3: Domain group (eTLD+1)
            group_id = rec["group_id"].lower()
            assert group_id not in forbidden_domain_groups, f"Domain group V2 trùng lặp: {group_id}"
            v2_domain_groups.add(group_id)

        # Đảm bảo V2 có đúng 32 domain groups độc nhất
        assert len(v2_domain_groups) == 32, f"V2 có domain group trùng lặp nội bộ: {len(v2_domain_groups)} != 32"

    def test_exclusion_registry_contains_both_v1_and_v2(self):
        """Exclusion registry phải cô lập cả V1 (32 mẫu) và V2 (32 mẫu), cấm huấn luyện."""
        from phishing.data.exclusion import ExclusionRegistry

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
        for rec in mapping_v2:
            assert reg.is_excluded({"url": rec["raw_url"]}) is True, f"Mẫu {rec['raw_url']} không bị chặn!"
