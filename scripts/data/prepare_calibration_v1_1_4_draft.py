#!/usr/bin/env python3
"""Chuẩn bị hồ sơ dự thảo nhãn cuối Calibration v1.1.4 (Phiên bản v4 - Cập nhật chính xác theo phản hồi Lead D).

Thực hiện nghiêm ngặt 2 điểm chỉ đạo mới nhất của Lead D:
1. SMP-021:
   - Sửa catalog_status="outside_catalog" (thay vì in_catalog) vì Robinhood không thuộc 14 mã trong dictionary_v1.json đã khóa (hash 7aa83b68...).
   - Cập nhật mọi bảng thống kê/audit table liên quan; tuyệt đối không sửa từ điển đã khóa.
2. Nguồn phân xử (adjudication_source) & Trạng thái phê duyệt (approval_status):
   - Không ghi cào bằng adjudication_source="lead_d_decisions_..." cho toàn bộ 19 dòng.
   - Phân định rạch ròi nguồn gốc từng dòng:
     + 12 ca thuộc biên bản phân xử D: lead_d_adjudication_decisions_20261020.
     + 6 ca đồng thuận Pass 1 E-B: unanimous_e_b_pass1_consensus.
     + 2 ca đồng thuận E-B kết hợp C tổng hợp đề xuất kỹ thuật (SMP-009, SMP-021): e_b_pass1_consensus_c_synthesized_proposal.
     + 4 ca shop tiếng Nhật C rà soát theo Mục 3 Codebook v1.1 đề xuất QC pending: c_audit_proposal_pending_d_review.
   - Tất cả các dòng đều ghi rõ approval_status="draft_pending_lead_d_final_signoff", khẳng định đây là bản dự thảo chờ D duyệt cuối, không ngụ ý D đã ký toàn bộ 19/24 mẫu.

Giữ nguyên byte Pass 1 E/B, Codebook, Blind View, Dictionary và training_blocked=true.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import urllib.parse
import zipfile

# Reconfigure console encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from phishing.annotation import compute_cohens_kappa

TARGET_HASH_B = "161abf6fee8abec12028f72a2e8a095a276bf70b1c8dc6520c00b227291ede82"
TARGET_HASH_E = "20dfc141e48fbb54939855a942f9c70af49bb6bd8ee805c7093c502b9d8b7340"
TARGET_HASH_D_DECISION = "431a889fed7cb57c1560fa48f2ed362eb25be2e7f82d792f3aad1e82ed7aadda"
TARGET_HASH_BLIND_VIEW = "7a13433334cb75a29b012313d1ab22f27fcb96ef9e0e1d33254c24eb1e07a372"
TARGET_HASH_CODEBOOK = "e30871b87911992110e77ad0dcca8bbf64b916086f496555599e43730af0adbd"
TARGET_HASH_DICTIONARY = "7aa83b68fdb4bb288460c00523e38e0779e8cbeb81ae879e7a5d27e771fcd3b3"


def sha256_file(path: Path) -> str:
    if not path.is_file():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("=== BẮT ĐẦU QUY TRÌNH CHUẨN BỊ HỒ SƠ CALIBRATION V1.1.4 (PHIÊN BẢN V4) ===")

    # 1. Kiểm tra đối soát byte nguyên bản 6 artifact nền tảng
    b_file = ROOT / "data/annotations/B/calibration_pass1.jsonl"
    e_file = ROOT / "data/annotations/E/calibration_pass1.jsonl"
    d_file = ROOT / "data/labels/calibration_v1_1_4/CALIBRATION_V1_1_4_ADJUDICATION_D_DECISIONS.md"
    bv_file = ROOT / "data/raw/recovery/calibration_proposal_v1.1.4_release.json"
    cb_file = ROOT / "docs/CODEBOOK_V1_1.md"
    dict_file = ROOT / "configs/dictionary_v1.json"

    assert sha256_file(b_file) == TARGET_HASH_B, "Pass 1 B hash mismatch!"
    assert sha256_file(e_file) == TARGET_HASH_E, "Pass 1 E hash mismatch!"
    assert sha256_file(d_file) == TARGET_HASH_D_DECISION, "Biên bản D hash mismatch!"
    assert sha256_file(bv_file) == TARGET_HASH_BLIND_VIEW, "Blind view hash mismatch!"
    assert sha256_file(cb_file) == TARGET_HASH_CODEBOOK, "Codebook hash mismatch!"
    assert sha256_file(dict_file) == TARGET_HASH_DICTIONARY, "Dictionary hash mismatch!"
    print("-> XÁC MINH 100% BYTE KHỚP CHO TẤT CẢ CÁC FILE ĐẦU VÀO!")

    # 2. Đọc bản ghi E, B và Blind View
    with open(e_file, encoding="utf-8") as f:
        e_records = [json.loads(line) for line in f if line.strip()]
    with open(b_file, encoding="utf-8") as f:
        b_records = [json.loads(line) for line in f if line.strip()]
    with open(bv_file, encoding="utf-8") as f:
        blind_view_data = json.load(f)

    map_e = {r["sample_id"]: r for r in e_records}
    map_b = {r["sample_id"]: r for r in b_records}
    map_bv = {s["sample_id"]: s for s in blind_view_data["samples"]}
    sids = sorted(map_b.keys())

    # 3. Tính toán độ đồng thuận Pass 1 thô giữa E và B (24 mẫu ban đầu)
    cl_e = [map_e[s]["class_label"] for s in sids]
    cl_b = [map_b[s]["class_label"] for s in sids]
    org_e = [map_e[s]["primary_org"] for s in sids]
    org_b = [map_b[s]["primary_org"] for s in sids]

    res_cl_raw = compute_cohens_kappa(cl_e, cl_b, require_provenance=False)
    res_org_raw = compute_cohens_kappa(org_e, org_b, require_provenance=False)

    print(f"\n[PASS 1 THÔ E-B]")
    print(f"  Class Label Kappa: {res_cl_raw.kappa:.4f} (Observed: {res_cl_raw.observed_agreement*100:.2f}%)")
    print(f"  Primary Org Kappa: {res_org_raw.kappa:.4f} (Observed: {res_org_raw.observed_agreement*100:.2f}%)")

    # 4. Thiết lập Bảng chuẩn hóa Alias ngoài danh mục thực sự xuất hiện
    alias_mapping_registry = {
        "schema_version": "4.0.0",
        "description": "Bảng lưu vết chuẩn hóa alias ngoài danh mục thực sự xuất hiện trong cặp E-B theo quyết định phân xử Lead D",
        "adjudication_reference": "CALIBRATION_V1_1_4_ADJUDICATION_D_DECISIONS.md",
        "adjudication_sha256": TARGET_HASH_D_DECISION,
        "dictionary_reference": "configs/dictionary_v1.json",
        "dictionary_sha256": TARGET_HASH_DICTIONARY,
        "codebook_reference": "docs/CODEBOOK_V1_1.md",
        "codebook_sha256": TARGET_HASH_CODEBOOK,
        "mappings": [
            {
                "raw_alias": "auspost",
                "normalized_org": "australia_post",
                "catalog_status": "outside_catalog",
                "canonical_brand": None,
                "rationale": "auspost là tên viết tắt của cơ quan bưu chính Australia Post (chuẩn hóa đồng nhất với E=australia_post tại SMP-013).",
                "affected_samples": ["SMP-013"]
            },
            {
                "raw_alias": "catedraldesantiago",
                "normalized_org": "catedral_de_santiago",
                "catalog_status": "outside_catalog",
                "canonical_brand": None,
                "rationale": "catedraldesantiago là tên miền dính liền của Nhà thờ chính tòa Santiago de Compostela, chuẩn hóa về danh xưng đầy đủ.",
                "affected_samples": ["SMP-014"]
            },
            {
                "raw_alias": "saberhealth",
                "normalized_org": "saber_healthcare_group",
                "catalog_status": "outside_catalog",
                "canonical_brand": None,
                "rationale": "saberhealth là tên miền dính liền của tập đoàn Saber Healthcare Group.",
                "affected_samples": ["SMP-017"]
            },
            {
                "raw_alias": "jjneedles",
                "normalized_org": "john_james_needles",
                "catalog_status": "outside_catalog",
                "canonical_brand": None,
                "rationale": "jjneedles là tên viết tắt thương mại của hãng kim may John James Needles.",
                "affected_samples": ["SMP-018"]
            },
            {
                "raw_alias": "nytimes",
                "normalized_org": "the_new_york_times",
                "catalog_status": "outside_catalog",
                "canonical_brand": None,
                "rationale": "nytimes là tên viết tắt phổ biến của tòa soạn The New York Times.",
                "affected_samples": ["SMP-022"]
            },
            {
                "raw_alias": "wsfb",
                "normalized_org": "wfsb",
                "catalog_status": "outside_catalog",
                "canonical_brand": None,
                "rationale": "Lỗi chính tả gõ phím đảo ký tự (wsfb -> wfsb) cho đài truyền hình WFSB Eyewitness News.",
                "affected_samples": ["SMP-007"]
            }
        ],
        "excluded_non_aliases": [
            {
                "term": "facebook -> meta",
                "status": "excluded_from_alias_registry",
                "reason": "Không xuất hiện khác biệt trong cặp E-B vì cả hai tệp Pass 1 đều đã ghi nhận 'meta' tại SMP-005 và SMP-008."
            },
            {
                "term": "entertaiment_news",
                "status": "classified_as_generic_category_label",
                "reason": "Mã gán chung chỉ thể loại nội dung của B tại SMP-001, được sửa theo phân xử thành 'radio_times', không phải là alias hợp lệ của thương hiệu."
            }
        ]
    }

    out_dir = ROOT / "data/labels/calibration_v1_1_4"
    out_dir.mkdir(parents=True, exist_ok=True)
    alias_file = out_dir / "alias_normalization_registry.json"
    alias_file.write_text(json.dumps(alias_mapping_registry, indent=2, ensure_ascii=False), encoding="utf-8")

    # 5. Tính toán thỏa thuận E-B sau chuẩn hóa alias
    d_aliases = {m["raw_alias"]: m["normalized_org"] for m in alias_mapping_registry["mappings"]}
    norm_org_e = [d_aliases.get(o, o) for o in org_e]
    norm_org_b = [d_aliases.get(o, o) for o in org_b]

    res_org_norm = compute_cohens_kappa(norm_org_e, norm_org_b, require_provenance=False)
    print(f"\n[SAU CHUẨN HÓA ALIAS E-B]")
    print(f"  Primary Org Kappa: {res_org_norm.kappa:.4f} (Observed: {res_org_norm.observed_agreement*100:.2f}%)")

    # 6. Thiết lập Từ điển Quyết định Phân xử & Dự thảo v4 (Phân tách nguồn gốc & catalog_status chuẩn)
    # - SMP-021: catalog_status='outside_catalog' (Robinhood không thuộc 14 mã khóa).
    # - Nguồn gốc: phân định rõ giữa quyết định của D trong biên bản, đồng thuận E-B, và đề xuất C.
    # - Trạng thái: draft_pending_lead_d_final_signoff cho toàn bộ 24 mẫu.
    decisions_v4 = {
        "SMP-001": {
            "status": "adjudicated",
            "source": "lead_d_adjudication_decisions_20261020",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "benign",
            "org": "radio_times",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "brand_mention_news",
            "ph": None,
            "evidence_quote": "Radio Times",
            "evidence_basis": "heading",
            "rationale": "Biên bản phân xử D: Tên Radio Times ở tiêu đề và các phần tự giới thiệu; entertaiment_news của B là mã thể loại chung sửa thành radio_times."
        },
        "SMP-002": {
            "status": "pending_evidence",
            "source": "c_audit_proposal_pending_d_review",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": None,
            "org": "unresolved",
            "cat": "unresolved",
            "dom": "unverified",
            "id": "unclear",
            "hb": None,
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "rationale": "Đề xuất C rà soát theo Mục 3 Codebook v1.1: Webshop tiếng Nhật trên tên miền .shop, có danh mục hàng hóa và mục phương thức thanh toán nhưng không có form thu thẻ hoặc luồng gian lận thanh toán quan sát được trong view. Đề xuất đưa vào QC pending_evidence, chờ Lead D duyệt."
        },
        "SMP-003": {
            "status": "adjudicated",
            "source": "lead_d_adjudication_decisions_20261020",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "benign",
            "org": "salestaxhandbook",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "other",
            "ph": None,
            "evidence_quote": "SalesTaxHandbook is a free public resource site",
            "evidence_basis": "body",
            "rationale": "Biên bản phân xử D: Trang tự nhận cung cấp tài liệu/công cụ Sales Tax Handbook, có disclaimer không trực thuộc chính phủ."
        },
        "SMP-004": {
            "status": "adjudicated",
            "source": "unanimous_e_b_pass1_consensus",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "insufficient_evidence",
            "org": "unknown",
            "cat": "unresolved",
            "dom": "unverified",
            "id": "unclear",
            "hb": None,
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "rationale": "Đồng thuận Pass 1 E-B: Snapshot hoàn toàn rỗng, không có biểu mẫu hoặc nội dung DOM. Cả E và B đều chọn insufficient_evidence. Trạng thái: Chờ Lead D duyệt cuối."
        },
        "SMP-005": {
            "status": "adjudicated",
            "source": "unanimous_e_b_pass1_consensus",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "phishing",
            "org": "meta",
            "cat": "in_catalog",
            "dom": "unverified",
            "id": "impersonation_claim",
            "hb": None,
            "ph": "impersonation_lure",
            "evidence_quote": "Your Facebook page and account",
            "evidence_basis": "body",
            "rationale": "Đồng thuận Pass 1 E-B: Mạo danh Meta Business Help Center đe dọa hạn chế trang trong 24h để dẫn dụ vào quy trình xác minh giả. Trạng thái: Chờ Lead D duyệt cuối."
        },
        "SMP-006": {
            "status": "adjudicated",
            "source": "unanimous_e_b_pass1_consensus",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "phishing",
            "org": "jojobet",
            "cat": "outside_catalog",
            "dom": "unverified",
            "id": "impersonation_claim",
            "hb": None,
            "ph": "credential_collection",
            "evidence_quote": "JOJOBET",
            "evidence_basis": "form",
            "rationale": "Đồng thuận Pass 1 E-B: Mạo danh nhà cái Jojobet trên tên miền clone chứa form đăng nhập thu thập mật khẩu. Trạng thái: Chờ Lead D duyệt cuối."
        },
        "SMP-007": {
            "status": "adjudicated",
            "source": "lead_d_adjudication_decisions_20261020",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "benign",
            "org": "wfsb",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "brand_mention_news",
            "ph": None,
            "evidence_quote": "Copyright 2024 WFSB",
            "evidence_basis": "body",
            "rationale": "Biên bản phân xử D: Nội dung điều hướng và bản quyền WFSB Eyewitness News; mã wsfb của B sửa chuẩn hóa thành wfsb."
        },
        "SMP-008": {
            "status": "adjudicated",
            "source": "unanimous_e_b_pass1_consensus",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "phishing",
            "org": "meta",
            "cat": "in_catalog",
            "dom": "unverified",
            "id": "impersonation_claim",
            "hb": None,
            "ph": "impersonation_lure",
            "evidence_quote": "Community Standards Policy",
            "evidence_basis": "body",
            "rationale": "Đồng thuận Pass 1 E-B: Mạo danh Meta Community Standards thông báo vi phạm đe dọa khóa tài khoản. Trạng thái: Chờ Lead D duyệt cuối."
        },
        "SMP-009": {
            "status": "adjudicated",
            "source": "e_b_pass1_consensus_c_synthesized_proposal",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "phishing",
            "org": "google",
            "cat": "in_catalog",
            "dom": "user_content_hosting",
            "id": "impersonation_claim",
            "hb": None,
            "ph": "impersonation_lure",
            "evidence_quote": "Drive",
            "evidence_basis": "body",
            "rationale": "Đồng thuận Pass 1 E-B (phishing/google), C tổng hợp đề xuất: Mạo danh giao diện Google Drive trên hạ tầng Firebase web.app (impersonation_lure). Trạng thái: Chờ Lead D duyệt cuối."
        },
        "SMP-010": {
            "status": "pending_evidence",
            "source": "lead_d_adjudication_decisions_20261020",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": None,
            "org": "unresolved",
            "cat": "unresolved",
            "dom": "unverified",
            "id": "unclear",
            "hb": None,
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "rationale": "Biên bản phân xử D: View thể hiện webshop tài liệu y khoa giảm giá sâu nhưng không chứng minh hành vi gian lận thanh toán hoặc mạo danh cụ thể. Chốt đưa vào QC pending_evidence, loại khỏi tập nhãn tham chiếu xác minh."
        },
        "SMP-011": {
            "status": "adjudicated",
            "source": "lead_d_adjudication_decisions_20261020",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "benign",
            "org": "no_clear_target",
            "cat": "unresolved",
            "dom": "first_party_identity",
            "id": "unclear",
            "hb": "brand_mention_news",
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "rationale": "Biên bản phân xử D: Trang đứng tên cá nhân Simon Rushby; danh tính cá nhân ghi trong ghi chú, giữ no_clear_target không ép thành tổ chức theo Codebook v1.1."
        },
        "SMP-012": {
            "status": "adjudicated",
            "source": "unanimous_e_b_pass1_consensus",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "benign",
            "org": "spotify",
            "cat": "in_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "official_login",
            "ph": None,
            "evidence_quote": "Log in to Spotify",
            "evidence_basis": "heading",
            "rationale": "Đồng thuận Pass 1 E-B: Trang đăng nhập tài khoản chính thức Spotify trên tên miền first-party. Trạng thái: Chờ Lead D duyệt cuối."
        },
        "SMP-013": {
            "status": "adjudicated",
            "source": "lead_d_adjudication_decisions_20261020",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "benign",
            "org": "australia_post",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "other",
            "ph": None,
            "evidence_quote": "Australia Post",
            "evidence_basis": "body",
            "rationale": "Biên bản phân xử D: Cổng tài liệu tích hợp API của Australia Post; chuẩn hóa auspost thành australia_post."
        },
        "SMP-014": {
            "status": "adjudicated",
            "source": "lead_d_adjudication_decisions_20261020",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "benign",
            "org": "catedral_de_santiago",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "other",
            "ph": None,
            "evidence_quote": "Catedral de Santiago de Compostela",
            "evidence_basis": "body",
            "rationale": "Biên bản phân xử D: Trang chính thức của Nhà thờ chính tòa Santiago de Compostela; chuẩn hóa catedraldesantiago thành catedral_de_santiago."
        },
        "SMP-015": {
            "status": "pending_evidence",
            "source": "c_audit_proposal_pending_d_review",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": None,
            "org": "unresolved",
            "cat": "unresolved",
            "dom": "unverified",
            "id": "unclear",
            "hb": None,
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "rationale": "Đề xuất C rà soát theo Mục 3 Codebook v1.1: Shop trực tuyến tiếng Nhật trên tên miền .shop thiếu bằng chứng quan sát về luồng gian lận thanh toán/thu thẻ; đề xuất đưa vào QC pending_evidence, chờ Lead D duyệt."
        },
        "SMP-016": {
            "status": "adjudicated",
            "source": "lead_d_adjudication_decisions_20261020",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "insufficient_evidence",
            "org": "no_clear_target",
            "cat": "unresolved",
            "dom": "user_content_hosting",
            "id": "unclear",
            "hb": None,
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "rationale": "Biên bản phân xử D: Snapshot chỉ có ASCII art và thông điệp giữ chỗ của Replit; Replit là nền tảng hosting, không phải danh tính ứng dụng; chốt insufficient_evidence."
        },
        "SMP-017": {
            "status": "adjudicated",
            "source": "lead_d_adjudication_decisions_20261020",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "benign",
            "org": "saber_healthcare_group",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "brand_mention_news",
            "ph": None,
            "evidence_quote": "Saber Healthcare Group",
            "evidence_basis": "heading",
            "rationale": "Biên bản phân xử D: Header và điều hướng tự nhận Saber Healthcare Group; chuẩn hóa saberhealth thành saber_healthcare_group."
        },
        "SMP-018": {
            "status": "adjudicated",
            "source": "lead_d_adjudication_decisions_20261020",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "benign",
            "org": "john_james_needles",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "official_login",
            "ph": None,
            "evidence_quote": "sales@jjneedles.com",
            "evidence_basis": "body",
            "rationale": "Biên bản phân xử D: Trang web bán hàng và hướng dẫn của hãng kim may John James Needles; chuẩn hóa jjneedles thành john_james_needles."
        },
        "SMP-019": {
            "status": "adjudicated",
            "source": "unanimous_e_b_pass1_consensus",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "phishing",
            "org": "amazon",
            "cat": "in_catalog",
            "dom": "unverified",
            "id": "impersonation_claim",
            "hb": None,
            "ph": "credential_collection",
            "evidence_quote": "Create your Amazon account",
            "evidence_basis": "form",
            "rationale": "Đồng thuận Pass 1 E-B: Mạo danh đăng nhập Amazon thu thập mật khẩu. Trạng thái: Chờ Lead D duyệt cuối."
        },
        "SMP-020": {
            "status": "pending_evidence",
            "source": "c_audit_proposal_pending_d_review",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": None,
            "org": "unresolved",
            "cat": "unresolved",
            "dom": "unverified",
            "id": "unclear",
            "hb": None,
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "rationale": "Đề xuất C rà soát theo Mục 3 Codebook v1.1: Trang thương mại điện tử tiếng Nhật trên tên miền .shop thiếu bằng chứng quan sát về luồng gian lận thanh toán/thu thẻ; đề xuất đưa vào QC pending_evidence, chờ Lead D duyệt."
        },
        "SMP-021": {
            "status": "adjudicated",
            "source": "e_b_pass1_consensus_c_synthesized_proposal",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "phishing",
            "org": "robinhood",
            "cat": "outside_catalog",
            "dom": "user_content_hosting",
            "id": "impersonation_claim",
            "hb": None,
            "ph": "support_contact_lure",
            "evidence_quote": "How do I talk directly on Robinhood?",
            "evidence_basis": "body",
            "rationale": "Đồng thuận Pass 1 E-B (phishing/robinhood/support_contact_lure), C tổng hợp đề xuất: Nội dung PDF thể hiện mồi nhử liên hệ hỗ trợ nhắc đến việc gọi số điện thoại 1(833) 534-1857 về tài khoản Robinhood, biểu mẫu thuế 1099, IRA và crypto; tệp lưu trữ trên thư mục webform công khai của sesarju.eu (user_content_hosting). Robinhood thuộc outside_catalog theo từ điển v1 khóa. Trạng thái: Chờ Lead D duyệt cuối."
        },
        "SMP-022": {
            "status": "adjudicated",
            "source": "lead_d_adjudication_decisions_20261020",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "benign",
            "org": "the_new_york_times",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "brand_mention_news",
            "ph": None,
            "evidence_quote": "The New York Times",
            "evidence_basis": "heading",
            "rationale": "Biên bản phân xử D: Bài báo của tòa soạn The New York Times; chuẩn hóa nytimes thành the_new_york_times."
        },
        "SMP-023": {
            "status": "pending_evidence",
            "source": "c_audit_proposal_pending_d_review",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": None,
            "org": "unresolved",
            "cat": "unresolved",
            "dom": "unverified",
            "id": "unclear",
            "hb": None,
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "rationale": "Đề xuất C rà soát theo Mục 3 Codebook v1.1: Shop trực tuyến Viert-store tiếng Nhật trên tên miền .shop thiếu bằng chứng quan sát về luồng gian lận thanh toán/thu thẻ; đề xuất đưa vào QC pending_evidence, chờ Lead D duyệt."
        },
        "SMP-024": {
            "status": "adjudicated",
            "source": "lead_d_adjudication_decisions_20261020",
            "approval_status": "draft_pending_lead_d_final_signoff",
            "class": "benign",
            "org": "wholesomeyum",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "official_login",
            "ph": None,
            "evidence_quote": "Wholesome Yum",
            "evidence_basis": "heading",
            "rationale": "Biên bản phân xử D: Trang blog ẩm thực Wholesome Yum có form đăng nhập thành viên first-party."
        }
    }

    draft_records_19 = []
    qc_pending_evidence_list = []
    full_24_audit_table = []

    for sid in sids:
        sbv = map_bv[sid]
        dec = decisions_v4[sid]
        rb = map_b[sid]
        re = map_e[sid]

        url_str = sbv["url"]
        hostname = urllib.parse.urlsplit(url_str).netloc

        # Tạo org_evidence đồng bộ chính xác với normalized primary_org
        org_evidence_list = []
        if dec["evidence_quote"] and dec["org"] not in ("unknown", "no_clear_target", "unresolved"):
            org_evidence_list.append({
                "org_id": dec["org"],
                "evidence_basis": dec["evidence_basis"],
                "evidence_quote": dec["evidence_quote"]
            })

        # Xử lý trường hợp QC pending_evidence (5 mẫu: SMP-002, 010, 015, 020, 023)
        if dec["status"] == "pending_evidence":
            pending_item = {
                "sample_id": sid,
                "url": url_str,
                "url_hostname": hostname,
                "status": "pending_evidence",
                "adjudicated_class_label": None,
                "binary_model_eligible": False,
                "gold_reference_eligible": False,
                "primary_org": "unresolved",
                "catalog_status": "unresolved",
                "org_evidence": [],
                "adjudication_source": dec["source"],
                "approval_status": dec["approval_status"],
                "provenance": {
                    "rater_e_label": re["class_label"],
                    "rater_b_label": rb["class_label"],
                    "rater_e_confidence": re.get("confidence"),
                    "rater_b_confidence": rb.get("confidence")
                },
                "rationale": dec["rationale"],
                "isolation_policy": "Loại khỏi tập nhãn tham chiếu xác minh và mô hình nhị phân cho đến khi có dữ liệu mạng/sandbox bổ sung."
            }
            qc_pending_evidence_list.append(pending_item)

            full_24_audit_table.append({
                "sample_id": sid,
                "url": url_str,
                "url_hostname": hostname,
                "adjudication_source": dec["source"],
                "approval_status": dec["approval_status"],
                "lead_d_or_c_rationale": dec["rationale"],
                "draft_class_label": "null (pending_evidence)",
                "draft_primary_org": "unresolved",
                "catalog_status": "unresolved",
                "draft_type": "null",
                "binary_model_eligible": False,
                "qc_status": "pending_evidence"
            })
            continue

        # Các mẫu đã phân xử (19 mẫu: 17 nhị phân + 2 insufficient_evidence)
        is_binary_eligible = dec["class"] in ("benign", "phishing")

        rec = {
            "sample_id": sid,
            "url_hostname": hostname,
            "adjudicated_class_label": dec["class"],
            "binary_model_eligible": is_binary_eligible,
            "gold_reference_eligible": True,
            "primary_org": dec["org"],
            "primary_org_status": "identified" if dec["org"] not in ("unknown", "no_clear_target") else dec["org"],
            "catalog_status": dec["cat"],
            "identity_role": dec["id"],
            "domain_role": dec["dom"],
            "primary_phishing_type": dec.get("ph"),
            "hard_benign_type": dec.get("hb"),
            "adjudicated_confidence": None,
            "adjudicated_confidence_status": "pending_lead_d_confirmation",
            "provenance_confidences": {
                "rater_e_confidence": re.get("confidence"),
                "rater_b_confidence": rb.get("confidence")
            },
            "org_evidence": org_evidence_list,
            "evidence_note": dec["rationale"],
            "adjudication_source": dec["source"],
            "approval_status": dec["approval_status"]
        }
        draft_records_19.append(rec)

        full_24_audit_table.append({
            "sample_id": sid,
            "url": url_str,
            "url_hostname": hostname,
            "adjudication_source": dec["source"],
            "approval_status": dec["approval_status"],
            "lead_d_or_c_rationale": dec["rationale"],
            "draft_class_label": dec["class"],
            "draft_primary_org": dec["org"],
            "catalog_status": dec["cat"],
            "draft_type": dec["ph"] or dec["hb"] or "none",
            "binary_model_eligible": is_binary_eligible,
            "qc_status": "adjudicated"
        })

    # Ghi file nháp 19 mẫu đã phân xử
    draft_file = out_dir / "draft_calibration_v1_1_4_adjudicated_19.json"
    draft_file.write_text(json.dumps(draft_records_19, indent=2, ensure_ascii=False), encoding="utf-8")

    # Ghi file QC pending 5 mẫu
    pending_file = out_dir / "qc_pending_evidence_5_samples.json"
    pending_file.write_text(json.dumps(qc_pending_evidence_list, indent=2, ensure_ascii=False), encoding="utf-8")

    # Ghi file bảng đối chiếu 24 dòng đầy đủ
    audit_table_file = out_dir / "calibration_v1_1_4_full_24_audit_table.json"
    audit_table_file.write_text(json.dumps(full_24_audit_table, indent=2, ensure_ascii=False), encoding="utf-8")

    # 7. Tính toán dự phóng công số PLAN-01 chuẩn xác (Điểm 5)
    times_e = [r["seconds_spent"] for r in e_records]
    times_b = [r["seconds_spent"] for r in b_records]
    import statistics
    e_mean = statistics.mean(times_e)
    e_median = statistics.median(times_e)
    b_mean = statistics.mean(times_b)
    b_median = statistics.median(times_b)

    ref_n = 1000
    r_pct = 0.30
    h_pct = 0.12
    r_count = int(ref_n * r_pct)
    h_count = int(ref_n * h_pct)
    expected_overlap = int(r_count * h_count / ref_n)
    expected_union_count = r_count + h_count - expected_overlap
    b_hours_mean = (expected_union_count * b_mean) / 3600
    b_hours_median = (expected_union_count * b_median) / 3600

    # 8. Báo cáo kiểm toán đồng thuận chi tiết v4
    audit_report = {
        "calibration_runway": "CALIBRATION-V1.1-24",
        "evaluator_pair": "E-B (Official Independent Rater Pair)",
        "pair_provenance": {
            "rater_e_hash": TARGET_HASH_E,
            "rater_b_hash": TARGET_HASH_B,
            "lead_d_decision_hash": TARGET_HASH_D_DECISION
        },
        "pass_1_raw_independent_metrics": {
            "class_label": {
                "kappa": round(res_cl_raw.kappa, 4),
                "observed_agreement": round(res_cl_raw.observed_agreement, 4),
                "interpretation": "Almost Perfect (0.8500, 22/24 exact match)",
                "disagreements": [
                    {"sample_id": "SMP-010", "rater_e": "phishing", "rater_b": "benign"},
                    {"sample_id": "SMP-016", "rater_e": "benign", "rater_b": "insufficient_evidence"}
                ],
                "unanimous_insufficient_evidence": ["SMP-004"]
            },
            "primary_org": {
                "kappa": round(res_org_raw.kappa, 4),
                "observed_agreement": round(res_org_raw.observed_agreement, 4),
                "interpretation": "Moderate Agreement (0.4297, 12/24 exact match)"
            }
        },
        "post_normalization_metrics": {
            "methodology": "Áp dụng 6 quy tắc chuẩn hóa alias ngoài danh mục thực sự xuất hiện trong dữ liệu E-B theo quyết định Lead D.",
            "rule_count": 6,
            "primary_org_normalized": {
                "kappa": round(res_org_norm.kappa, 4),
                "observed_agreement": round(res_org_norm.observed_agreement, 4),
                "interpretation": "Moderate Agreement (0.4762, 13/24 exact match)"
            },
            "scientific_integrity_warning": "Tuyệt đối không sử dụng chỉ số 0.4762 sau chuẩn hóa để thay thế cho Kappa độc lập ban đầu trong báo cáo công bố khoa học."
        },
        "binary_model_eligibility_breakdown": {
            "total_corpus_samples": 24,
            "eligible_for_binary_model_count": 17,
            "ineligible_for_binary_model_count": 7,
            "eligible_breakdown": {
                "benign_count": 11,
                "benign_samples": ["SMP-001", "SMP-003", "SMP-007", "SMP-011", "SMP-012", "SMP-013", "SMP-014", "SMP-017", "SMP-018", "SMP-022", "SMP-024"],
                "phishing_count": 6,
                "phishing_samples": ["SMP-005", "SMP-006", "SMP-008", "SMP-009", "SMP-019", "SMP-021"],
                "catalog_status_distribution": {
                    "in_catalog_count": 5,
                    "in_catalog_samples": ["SMP-005", "SMP-008", "SMP-009", "SMP-012", "SMP-019"],
                    "outside_catalog_count": 11,
                    "outside_catalog_samples": ["SMP-001", "SMP-003", "SMP-006", "SMP-007", "SMP-013", "SMP-014", "SMP-017", "SMP-018", "SMP-021", "SMP-022", "SMP-024"],
                    "unresolved_no_clear_target_count": 1,
                    "unresolved_samples": ["SMP-011"]
                }
            },
            "ineligible_details": [
                {"sample_id": "SMP-002", "reason": "QC pending_evidence (shop tiếng Nhật thiếu bằng chứng gian lận thanh toán quan sát được)"},
                {"sample_id": "SMP-004", "reason": "adjudicated_class_label='insufficient_evidence' (snapshot trắng, không DOM)"},
                {"sample_id": "SMP-010", "reason": "QC pending_evidence (webshop y khoa thiếu bằng chứng gian lận cụ thể)"},
                {"sample_id": "SMP-015", "reason": "QC pending_evidence (shop tiếng Nhật thiếu bằng chứng gian lận thanh toán quan sát được)"},
                {"sample_id": "SMP-016", "reason": "adjudicated_class_label='insufficient_evidence' (Replit placeholder, ASCII art thô)"},
                {"sample_id": "SMP-020", "reason": "QC pending_evidence (shop tiếng Nhật thiếu bằng chứng gian lận thanh toán quan sát được)"},
                {"sample_id": "SMP-023", "reason": "QC pending_evidence (shop tiếng Nhật thiếu bằng chứng gian lận thanh toán quan sát được)"}
            ]
        },
        "effort_estimation_plan_01": {
            "rater_a_policy": "Bỏ hoàn toàn số liệu lượt cũ của A do có hỗ trợ bên ngoài; công số chính thức của A sẽ được đo độc lập qua Lượt hiệu chuẩn sạch mới.",
            "rater_b_workload_union_model": {
                "scenario_type": "Kịch bản kỳ vọng (Expected Scenario) dựa trên giả định mô hình",
                "reference_corpus_size": ref_n,
                "random_sampling_rate": f"{r_pct*100}% ({r_count} mẫu)",
                "hard_case_rate_estimate": f"{h_pct*100}% ({h_count} mẫu)",
                "expected_overlap_count": expected_overlap,
                "expected_distinct_samples_to_audit_union": expected_union_count,
                "avoided_duplicate_evaluations": expected_overlap,
                "actual_execution_rule": "Số lượt thực tế trong đợt gán nhãn chính bắt buộc phải tính bằng hợp của hai tập mẫu cụ thể đã chọn: |R_actual ∪ H_actual| = |R_actual| + |H_actual| - |R_actual ∩ H_actual|.",
                "b_timing_basis": f"Mean={b_mean:.1f}s/mẫu (~{b_mean/60:.2f}p), Median={b_median:.1f}s/mẫu (~{b_median/60:.2f}p)",
                "estimated_b_hours_mean": round(b_hours_mean, 2),
                "estimated_b_hours_median": round(b_hours_median, 2)
            }
        }
    }

    report_file = out_dir / "calibration_v1_1_4_agreement_audit_report.json"
    report_file.write_text(json.dumps(audit_report, indent=2, ensure_ascii=False), encoding="utf-8")

    # 9. Bảng phân tích sai khác giữa Review Pack v3 và v4
    diff_analysis_v4 = {
        "comparison_title": "Bảng đối chiếu sai khác chi tiết: Review Pack v3 vs. Review Pack v4 (Sau đối soát Lead D)",
        "differences": [
            {
                "item": "1. catalog_status của mẫu SMP-021",
                "version_3": "catalog_status = 'in_catalog'",
                "version_4": "Sửa thành catalog_status = 'outside_catalog' vì Robinhood không thuộc 14 mã trong dictionary_v1.json đã khóa (hash 7aa83b68...)",
                "impact": "Bảo vệ nguyên vẹn tính nhất quán của từ điển 14 tổ chức khóa; cập nhật chính xác phân bố: 5 in-catalog, 11 outside-catalog, 1 unresolved."
            },
            {
                "item": "2. Phân định nguồn gốc phân xử (adjudication_source)",
                "version_3": "Ghi đồng loạt adjudication_source = 'lead_d_decisions_v3_20261020' cho toàn bộ 19 mẫu",
                "version_4": "Phân định minh bạch: 12 mẫu thuộc biên bản D (lead_d_adjudication_decisions_20261020); 6 mẫu đồng thuận Pass 1 E-B (unanimous_e_b_pass1_consensus); 2 mẫu đồng thuận E-B + C tổng hợp (e_b_pass1_consensus_c_synthesized_proposal); 4 mẫu shop C rà soát (c_audit_proposal_pending_d_review)",
                "impact": "Tuân thủ kỷ luật ARS về nguồn gốc dữ liệu; không gán ghép quyết định của D cho các mẫu D chưa trực tiếp phân xử."
            },
            {
                "item": "3. Trạng thái phê duyệt (approval_status)",
                "version_3": "Không có trường trạng thái phê duyệt rõ ràng",
                "version_4": "Bổ sung approval_status = 'draft_pending_lead_d_final_signoff' cho toàn bộ 24 mẫu",
                "impact": "Xác định rõ ràng đây là bản dự thảo chờ Lead D ký duyệt cuối cùng, không gây hiểu lầm là nhãn đã chốt chính thức."
            }
        ]
    }
    diff_file = out_dir / "diff_analysis_v3_vs_v4.json"
    diff_file.write_text(json.dumps(diff_analysis_v4, indent=2, ensure_ascii=False), encoding="utf-8")

    # 10. Đóng gói lại ZIP review pack mới (v4) và sinh checksum SHA-256
    files_to_pack = [
        "draft_calibration_v1_1_4_adjudicated_19.json",
        "qc_pending_evidence_5_samples.json",
        "calibration_v1_1_4_full_24_audit_table.json",
        "alias_normalization_registry.json",
        "calibration_v1_1_4_agreement_audit_report.json",
        "diff_analysis_v3_vs_v4.json",
        "CALIBRATION_V1_1_4_ADJUDICATION_D_DECISIONS.md"
    ]
    zip_path = out_dir / "calibration_v1_1_4_d_review_pack.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for fname in files_to_pack:
            fp = out_dir / fname
            z.write(fp, arcname=fname)

    zip_bytes = zip_path.read_bytes()
    new_zip_hash = hashlib.sha256(zip_bytes).hexdigest()
    zip_sha_path = out_dir / "calibration_v1_1_4_d_review_pack.zip.sha256"
    zip_sha_path.write_text(f"{new_zip_hash}  {zip_path.name}\n", encoding="utf-8")

    print(f"\n-> ĐÃ ĐÓNG GÓI XONG REVIEW PACK V4:")
    print(f"   Đường dẫn: {zip_path}")
    print(f"   Dung lượng: {len(zip_bytes)} bytes")
    print(f"   SHA-256:   {new_zip_hash}")
    print("\n=== HOÀN TẤT THÀNH CÔNG TOÀN BỘ YÊU CẦU ĐỐI SOÁT CỦA LEAD D CHO BẢN V4 ===")


if __name__ == "__main__":
    main()
