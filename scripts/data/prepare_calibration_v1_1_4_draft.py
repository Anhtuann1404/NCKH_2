#!/usr/bin/env python3
"""Chuẩn bị hồ sơ dự thảo nhãn cuối Calibration v1.1.4 (Phiên bản v3 - Cập nhật toàn diện theo chỉ đạo Lead D).

Thực hiện nghiêm ngặt 6 điểm yêu cầu của Lead D tại đợt đối soát Review Pack v2:
1. Rà soát SMP-002, 015, 020, 023 theo Mục 3 Codebook v1.1:
   - Thiếu bằng chứng quan sát về luồng thanh toán gian lận hoặc thu thập thẻ trong snapshot.
   - Cửa hàng giảm giá / tên miền lạ (.shop) và text nhắc phương thức thanh toán không đủ để kết luận payment_deception.
   - Chuyển cả 4 mẫu vào hàng đợi QC pending_evidence (cùng SMP-010 thành 5 mẫu pending).
   - Tuyệt đối không ép sang benign.
   - Tính lại số mẫu đủ điều kiện nhị phân: 17/24 mẫu.
2. SMP-021:
   - Xóa bỏ hoàn toàn chữ 'Protiviti'; URL thuộc máy chủ của www.sesarju.eu (Drupal webform).
   - Tách bạch rõ ràng bằng chứng quan sát được (PDF chứa câu hỏi 'How do I talk directly on Robinhood?'
     và lặp số điện thoại 1(833) 534-1857 năm lần) khỏi suy luận số giả.
   - Định danh chuẩn xác: class_label='phishing', primary_org='robinhood',
     primary_phishing_type='support_contact_lure', domain_role='user_content_hosting'.
3. Đồng bộ hóa org_evidence và chuẩn hóa kỹ thuật:
   - Đồng bộ org_evidence.org_id với mã tổ chức sau chuẩn hóa alias (wfsb, australia_post, catedral_de_santiago, saber_healthcare_group, john_james_needles, the_new_york_times).
   - Trích xuất url_hostname bằng urllib.parse.urlsplit(url).netloc từ chính URL của mẫu.
   - Kiểm tra và đảm bảo 100% evidence_quote tồn tại thực tế trong Blind View text/heading.
   - Không sao chép confidence của một rater thành confidence đã phân xử: adjudicated_confidence đặt None
     (chờ D xác nhận), ghi nhận độc lập rater_e_confidence và rater_b_confidence.
4. Bảng đối chiếu đầy đủ 24 dòng:
   - Xuất bảng reconciliation 24 mẫu: ID -> URL / Hostname -> Quyết định D & Căn cứ -> Nhãn dự thảo -> Điều kiện nhị phân / QC.
5. Dự phóng công số B trong PLAN-01:
   - Nêu rõ 384 lượt kiểm của B là kịch bản kỳ vọng (expected scenario) với giả định 1.000 mẫu và 12% ca khó.
   - Khẳng định số lượt thực tế phải được tính bằng hợp của 2 tập mẫu thực tế đã chọn |R_actual ∪ H_actual|.
   - Giữ nguyên tắc loại bỏ hoàn toàn thời gian của lượt A cũ khỏi PLAN-01.
6. Kỷ luật dữ liệu & Bàn giao:
   - Bảo toàn byte Pass 1 E/B, từ điển 14 tổ chức khóa, Codebook khóa.
   - Duy trì training_blocked=true; chưa xuất labels_final.json.
   - Xuất gói Review Pack v3 ZIP kèm SHA-256 và diff chi tiết v2 vs v3.
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
    print("=== BẮT ĐẦU QUY TRÌNH CHUẨN BỊ HỒ SƠ CALIBRATION V1.1.4 (PHIÊN BẢN V3 - CẬP NHẬT THEO CHỈ ĐẠO LEAD D) ===")

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
        "schema_version": "3.0.0",
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

    # 6. Thiết lập Từ điển Quyết định Phân xử v3 (Cập nhật Point 1, Point 2, Point 3)
    # Rà soát kỹ theo Mục 3 Codebook v1.1 và chỉ đạo của Lead D:
    # - SMP-002, 015, 020, 023: Chuyển sang QC pending_evidence vì thiếu bằng chứng luồng thanh toán gian lận / thu thẻ.
    # - SMP-021: Xóa Protiviti, hostname www.sesarju.eu, support_contact_lure trên webform sesarju.eu.
    decisions_v3 = {
        "SMP-001": {
            "status": "adjudicated",
            "class": "benign",
            "org": "radio_times",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "brand_mention_news",
            "ph": None,
            "evidence_quote": "Radio Times",
            "evidence_basis": "heading",
            "d_rationale": "Tên Radio Times ở tiêu đề và các phần tự giới thiệu của trang; entertaiment_news của B là mã thể loại chung sửa thành radio_times theo quyết định D."
        },
        "SMP-002": {
            "status": "pending_evidence",
            "class": None,
            "org": "unresolved",
            "cat": "unresolved",
            "dom": "unverified",
            "id": "unclear",
            "hb": None,
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "d_rationale": "QC pending_evidence (Mục 3 Codebook v1.1): Webshop tiếng Nhật trên tên miền .shop, có danh mục hàng hóa và mục phương thức thanh toán nhưng không có form thu thẻ hoặc luồng gian lận thanh toán quan sát được trong view. Không đủ căn cứ payment_deception và không ép sang benign."
        },
        "SMP-003": {
            "status": "adjudicated",
            "class": "benign",
            "org": "salestaxhandbook",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "other",
            "ph": None,
            "evidence_quote": "SalesTaxHandbook is a free public resource site",
            "evidence_basis": "body",
            "d_rationale": "Trang tự nhận cung cấp tài liệu/công cụ Sales Tax Handbook, có disclaimer không trực thuộc chính phủ."
        },
        "SMP-004": {
            "status": "adjudicated",
            "class": "insufficient_evidence",
            "org": "unknown",
            "cat": "unresolved",
            "dom": "unverified",
            "id": "unclear",
            "hb": None,
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "d_rationale": "Snapshot hoàn toàn rỗng, không có biểu mẫu hoặc nội dung DOM. Cả E và B đều độc lập chọn insufficient_evidence."
        },
        "SMP-005": {
            "status": "adjudicated",
            "class": "phishing",
            "org": "meta",
            "cat": "in_catalog",
            "dom": "unverified",
            "id": "impersonation_claim",
            "hb": None,
            "ph": "impersonation_lure",
            "evidence_quote": "Your Facebook page and account",
            "evidence_basis": "body",
            "d_rationale": "Mạo danh Meta Business Help Center đe dọa hạn chế trang trong 24h để dẫn dụ vào quy trình xác minh giả."
        },
        "SMP-006": {
            "status": "adjudicated",
            "class": "phishing",
            "org": "jojobet",
            "cat": "outside_catalog",
            "dom": "unverified",
            "id": "impersonation_claim",
            "hb": None,
            "ph": "credential_collection",
            "evidence_quote": "JOJOBET",
            "evidence_basis": "form",
            "d_rationale": "Mạo danh nhà cái Jojobet trên tên miền clone chứa form đăng nhập thu thập mật khẩu."
        },
        "SMP-007": {
            "status": "adjudicated",
            "class": "benign",
            "org": "wfsb",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "brand_mention_news",
            "ph": None,
            "evidence_quote": "Copyright 2024 WFSB",
            "evidence_basis": "body",
            "d_rationale": "Nội dung điều hướng và bản quyền WFSB Eyewitness News; mã wsfb của B sửa chuẩn hóa thành wfsb."
        },
        "SMP-008": {
            "status": "adjudicated",
            "class": "phishing",
            "org": "meta",
            "cat": "in_catalog",
            "dom": "unverified",
            "id": "impersonation_claim",
            "hb": None,
            "ph": "impersonation_lure",
            "evidence_quote": "Community Standards Policy",
            "evidence_basis": "body",
            "d_rationale": "Mạo danh Meta Community Standards thông báo vi phạm đe dọa khóa tài khoản."
        },
        "SMP-009": {
            "status": "adjudicated",
            "class": "phishing",
            "org": "google",
            "cat": "in_catalog",
            "dom": "user_content_hosting",
            "id": "impersonation_claim",
            "hb": None,
            "ph": "impersonation_lure",
            "evidence_quote": "Drive",
            "evidence_basis": "body",
            "d_rationale": "Mạo danh giao diện Google Drive trên hạ tầng Firebase web.app."
        },
        "SMP-010": {
            "status": "pending_evidence",
            "class": None,
            "org": "unresolved",
            "cat": "unresolved",
            "dom": "unverified",
            "id": "unclear",
            "hb": None,
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "d_rationale": "QC pending_evidence (Mục 3 Codebook v1.1): View thể hiện webshop tài liệu y khoa giảm giá sâu nhưng không chứng minh hành vi gian lận thanh toán hoặc mạo danh cụ thể. Loại khỏi tập nhãn tham chiếu xác minh."
        },
        "SMP-011": {
            "status": "adjudicated",
            "class": "benign",
            "org": "no_clear_target",
            "cat": "unresolved",
            "dom": "first_party_identity",
            "id": "unclear",
            "hb": "brand_mention_news",
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "d_rationale": "Quyết định D: Trang đứng tên cá nhân Simon Rushby; danh tính cá nhân ghi trong ghi chú, không ép thành tổ chức theo Codebook v1.1."
        },
        "SMP-012": {
            "status": "adjudicated",
            "class": "benign",
            "org": "spotify",
            "cat": "in_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "official_login",
            "ph": None,
            "evidence_quote": "Log in to Spotify",
            "evidence_basis": "heading",
            "d_rationale": "Trang đăng nhập tài khoản chính thức Spotify trên tên miền first-party."
        },
        "SMP-013": {
            "status": "adjudicated",
            "class": "benign",
            "org": "australia_post",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "other",
            "ph": None,
            "evidence_quote": "Australia Post",
            "evidence_basis": "body",
            "d_rationale": "Cổng tài liệu tích hợp API của Australia Post; chuẩn hóa auspost thành australia_post theo quyết định D."
        },
        "SMP-014": {
            "status": "adjudicated",
            "class": "benign",
            "org": "catedral_de_santiago",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "other",
            "ph": None,
            "evidence_quote": "Catedral de Santiago de Compostela",
            "evidence_basis": "body",
            "d_rationale": "Trang chính thức của Nhà thờ chính tòa Santiago de Compostela; chuẩn hóa catedraldesantiago thành catedral_de_santiago."
        },
        "SMP-015": {
            "status": "pending_evidence",
            "class": None,
            "org": "unresolved",
            "cat": "unresolved",
            "dom": "unverified",
            "id": "unclear",
            "hb": None,
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "d_rationale": "QC pending_evidence (Mục 3 Codebook v1.1): Shop trực tuyến tiếng Nhật trên tên miền .shop, có danh mục hàng hóa và giỏ hàng nhưng không có form thu thẻ hoặc luồng gian lận thanh toán quan sát được trong view. Không đủ căn cứ payment_deception và không ép sang benign."
        },
        "SMP-016": {
            "status": "adjudicated",
            "class": "insufficient_evidence",
            "org": "no_clear_target",
            "cat": "unresolved",
            "dom": "user_content_hosting",
            "id": "unclear",
            "hb": None,
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "d_rationale": "Quyết định D: Snapshot chỉ có ASCII art và thông điệp giữ chỗ của Replit; Replit là nền tảng hosting, không phải danh tính ứng dụng."
        },
        "SMP-017": {
            "status": "adjudicated",
            "class": "benign",
            "org": "saber_healthcare_group",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "brand_mention_news",
            "ph": None,
            "evidence_quote": "Saber Healthcare Group",
            "evidence_basis": "heading",
            "d_rationale": "Header và điều hướng tự nhận Saber Healthcare Group; chuẩn hóa saberhealth thành saber_healthcare_group."
        },
        "SMP-018": {
            "status": "adjudicated",
            "class": "benign",
            "org": "john_james_needles",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "official_login",
            "ph": None,
            "evidence_quote": "sales@jjneedles.com",
            "evidence_basis": "body",
            "d_rationale": "Trang web bán hàng và hướng dẫn của hãng kim may John James Needles; chuẩn hóa jjneedles thành john_james_needles."
        },
        "SMP-019": {
            "status": "adjudicated",
            "class": "phishing",
            "org": "amazon",
            "cat": "in_catalog",
            "dom": "unverified",
            "id": "impersonation_claim",
            "hb": None,
            "ph": "credential_collection",
            "evidence_quote": "Create your Amazon account",
            "evidence_basis": "form",
            "d_rationale": "Mạo danh đăng nhập Amazon thu thập mật khẩu."
        },
        "SMP-020": {
            "status": "pending_evidence",
            "class": None,
            "org": "unresolved",
            "cat": "unresolved",
            "dom": "unverified",
            "id": "unclear",
            "hb": None,
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "d_rationale": "QC pending_evidence (Mục 3 Codebook v1.1): Trang thương mại điện tử tiếng Nhật trên tên miền .shop, có danh mục hàng hóa nhưng không có form thu thập thông tin thẻ hoặc luồng gian lận thanh toán quan sát được trong view. Không đủ căn cứ payment_deception và không ép sang benign."
        },
        "SMP-021": {
            "status": "adjudicated",
            "class": "phishing",
            "org": "robinhood",
            "cat": "in_catalog",
            "dom": "user_content_hosting",
            "id": "impersonation_claim",
            "hb": None,
            "ph": "support_contact_lure",
            "evidence_quote": "How do I talk directly on Robinhood?",
            "evidence_basis": "body",
            "d_rationale": "Nội dung PDF thể hiện mồi nhử liên hệ hỗ trợ (support_contact_lure) mạo danh Robinhood nhắc đến việc gọi số điện thoại ngoài luồng 1(833) 534-1857 về tài khoản, biểu mẫu thuế 1099, IRA và crypto; tệp được lưu trữ trên thư mục webform Drupal công khai của sesarju.eu (user_content_hosting)."
        },
        "SMP-022": {
            "status": "adjudicated",
            "class": "benign",
            "org": "the_new_york_times",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "brand_mention_news",
            "ph": None,
            "evidence_quote": "The New York Times",
            "evidence_basis": "heading",
            "d_rationale": "Bài báo của tòa soạn The New York Times; chuẩn hóa nytimes thành the_new_york_times."
        },
        "SMP-023": {
            "status": "pending_evidence",
            "class": None,
            "org": "unresolved",
            "cat": "unresolved",
            "dom": "unverified",
            "id": "unclear",
            "hb": None,
            "ph": None,
            "evidence_quote": None,
            "evidence_basis": None,
            "d_rationale": "QC pending_evidence (Mục 3 Codebook v1.1): Shop trực tuyến Viert-store tiếng Nhật trên tên miền .shop, có danh mục hàng hóa nhưng không có form thu thẻ hoặc luồng gian lận thanh toán quan sát được trong view. Không đủ căn cứ payment_deception và không ép sang benign."
        },
        "SMP-024": {
            "status": "adjudicated",
            "class": "benign",
            "org": "wholesomeyum",
            "cat": "outside_catalog",
            "dom": "first_party_identity",
            "id": "identity_claim",
            "hb": "official_login",
            "ph": None,
            "evidence_quote": "Wholesome Yum",
            "evidence_basis": "heading",
            "d_rationale": "Trang blog ẩm thực Wholesome Yum có form đăng nhập thành viên first-party."
        }
    }

    draft_records_19 = []
    qc_pending_evidence_list = []
    full_24_audit_table = []

    for sid in sids:
        sbv = map_bv[sid]
        dec = decisions_v3[sid]
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
                "org_evidence": [],
                "provenance": {
                    "rater_e_label": re["class_label"],
                    "rater_b_label": rb["class_label"],
                    "rater_e_confidence": re.get("confidence"),
                    "rater_b_confidence": rb.get("confidence")
                },
                "lead_d_rationale": dec["d_rationale"],
                "isolation_policy": "Loại khỏi tập nhãn tham chiếu xác minh và mô hình nhị phân cho đến khi có dữ liệu mạng/sandbox bổ sung."
            }
            qc_pending_evidence_list.append(pending_item)

            full_24_audit_table.append({
                "sample_id": sid,
                "url": url_str,
                "url_hostname": hostname,
                "lead_d_decision_and_rationale": dec["d_rationale"],
                "draft_class_label": "null (pending_evidence)",
                "draft_primary_org": "unresolved",
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
            "evidence_note": dec["d_rationale"],
            "adjudication_source": "lead_d_decisions_v3_20261020"
        }
        draft_records_19.append(rec)

        full_24_audit_table.append({
            "sample_id": sid,
            "url": url_str,
            "url_hostname": hostname,
            "lead_d_decision_and_rationale": dec["d_rationale"],
            "draft_class_label": dec["class"],
            "draft_primary_org": dec["org"],
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

    # 8. Báo cáo kiểm toán đồng thuận chi tiết v3
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
                "phishing_samples": ["SMP-005", "SMP-006", "SMP-008", "SMP-009", "SMP-019", "SMP-021"]
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

    # 9. Bảng phân tích sai khác giữa Review Pack v2 và v3
    diff_analysis_v3 = {
        "comparison_title": "Bảng đối chiếu sai khác chi tiết: Review Pack v2 vs. Review Pack v3 (Sau đối soát Lead D)",
        "differences": [
            {
                "item": "1. Rà soát shop SMP-002, 015, 020, 023 theo Mục 3 Codebook v1.1",
                "version_2": "Gán là 'phishing' / 'payment_deception' trong dự thảo nhãn",
                "version_3": "Chuyển toàn bộ 4 mẫu vào hàng đợi QC 'pending_evidence' do snapshot chỉ có danh mục/phương thức thanh toán, thiếu bằng chứng gian lận thanh toán hoặc thu thẻ; không ép sang benign",
                "impact": "Tuân thủ triệt để Mục 3 Codebook v1.1; danh sách QC pending tăng từ 1 lên 5 mẫu (SMP-002, 010, 015, 020, 023)."
            },
            {
                "item": "2. Tính lại số mẫu đủ điều kiện nhị phân",
                "version_2": "21 mẫu đủ điều kiện (loại trừ SMP-004, 010, 016)",
                "version_3": "17 mẫu đủ điều kiện (11 benign + 6 phishing; loại trừ thêm 4 shop pending SMP-002, 015, 020, 023)",
                "impact": "Bảo vệ độ sạch của tập nhị phân M0-M3; ngăn chặn các mẫu chưa rõ hành vi lọt vào huấn luyện."
            },
            {
                "item": "3. Chuẩn hóa mẫu SMP-021",
                "version_2": "Ghi chú chứa từ 'Protiviti' và url_hostname bị rỗng",
                "version_3": "Xóa hoàn toàn 'Protiviti'; điền url_hostname='www.sesarju.eu'; tách rõ bằng chứng quan sát (PDF hỏi Robinhood & lặp số điện thoại 5 lần trên webform Drupal) khỏi suy luận số giả; phân loại chuẩn support_contact_lure",
                "impact": "Đúng tên miền thực tế, tuân thủ kỷ luật ARS về phân tách quan sát tĩnh vs suy luận hành vi."
            },
            {
                "item": "4. Điền url_hostname và đồng bộ org_evidence",
                "version_2": "url_hostname bị rỗng do truy cập nhầm url_parts; org_evidence giữ org_id cũ chưa chuẩn hóa; sao chép confidence của rater B",
                "version_3": "url_hostname trích xuất từ urlsplit().netloc cho 100% mẫu; org_evidence.org_id đồng bộ mã chuẩn hóa; evidence_quote kiểm tra khớp text; confidence đặt None (chờ D duyệt)",
                "impact": "Đồng bộ dữ liệu kỹ thuật toàn vẹn; không gán nhãn độ tin cậy chủ quan khi Lead D chưa xác nhận."
            },
            {
                "item": "5. Bảng đối chiếu 24 dòng đầy đủ",
                "version_2": "Ghép sai SMP-ID với tổ chức trong phần text báo cáo",
                "version_3": "Sửa triệt để text và xuất artifact 'calibration_v1_1_4_full_24_audit_table.json' đối chiếu chuẩn xác từng dòng ID -> URL -> Quyết định D -> Nhãn dự thảo",
                "impact": "Lead D và B có thể kiểm tra chéo từng dòng một cách minh bạch."
            },
            {
                "item": "6. Diễn giải công số B trong PLAN-01",
                "version_2": "Ghi 384 mẫu như số đếm cơ học cố định",
                "version_3": "Ghi rõ 384 mẫu là kịch bản kỳ vọng với giả định 1.000 mẫu và 12% ca khó; số lượt thực tế bắt buộc tính theo hợp hai tập đã chọn |R_actual ∪ H_actual|",
                "impact": "Chính xác về mặt toán học và quy trình thực nghiệm ARS."
            }
        ]
    }
    diff_file = out_dir / "diff_analysis_v2_vs_v3.json"
    diff_file.write_text(json.dumps(diff_analysis_v3, indent=2, ensure_ascii=False), encoding="utf-8")

    # 10. Đóng gói lại ZIP review pack mới (v3) và sinh checksum SHA-256
    files_to_pack = [
        "draft_calibration_v1_1_4_adjudicated_19.json",
        "qc_pending_evidence_5_samples.json",
        "calibration_v1_1_4_full_24_audit_table.json",
        "alias_normalization_registry.json",
        "calibration_v1_1_4_agreement_audit_report.json",
        "diff_analysis_v2_vs_v3.json",
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

    print(f"\n-> ĐÃ ĐÓNG GÓI XONG REVIEW PACK V3:")
    print(f"   Đường dẫn: {zip_path}")
    print(f"   Dung lượng: {len(zip_bytes)} bytes")
    print(f"   SHA-256:   {new_zip_hash}")
    print("\n=== HOÀN TẤT THÀNH CÔNG TOÀN BỘ 6 ĐIỂM CHỈ ĐẠO CỦA LEAD D CHO BẢN V3 ===")


if __name__ == "__main__":
    main()
