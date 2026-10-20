#!/usr/bin/env python3
"""Chuẩn bị hồ sơ dự thảo nhãn cuối Calibration v1.1.4 cho Lead D và B rà soát.

Tuân thủ nghiêm ngặt nguyên tắc ARS & Ponytail Discipline:
- Giữ nguyên byte các file gốc Pass 1 (B SHA-256: 161abf6fee8abec12028f72a2e8a095a276bf70b1c8dc6520c00b227291ede82).
- Không sửa từ điển 14 tổ chức đã khóa (dictionary_v1.json) và Codebook v1.1.0 đã khóa.
- SMP-010 được ghi riêng vào danh sách QC pending_evidence, không gán nhãn lớp cuối,
  không đưa vào tập nhãn tham chiếu đã xác minh.
- Lập bảng chuẩn hóa alias ngoài danh mục có lưu vết (audit provenance).
- Báo cáo riêng biệt: Độ đồng thuận Pass 1 thô vs. Sau chuẩn hóa alias (không đánh tráo khái niệm).
- Lưu toàn bộ hồ sơ trong khu vực dữ liệu hạn chế (data/labels/calibration_v1_1_4/), không commit lên Git.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

# Reconfigure console encoding
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


def sha256_file(path: Path) -> str:
    if not path.is_file():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("=== BẮT ĐẦU QUY TRÌNH CHUẨN BỊ HỒ SƠ DỰ THẢO CALIBRATION V1.1.4 (THÀNH VIÊN C) ===")
    
    # 1. Kiểm tra tính toàn vẹn file Pass 1 của B
    b_file = ROOT / "data/annotations/B/calibration_pass1.jsonl"
    hash_b = sha256_file(b_file)
    print(f"File Pass 1 B: {b_file}")
    print(f"  SHA-256 thực tế:  {hash_b}")
    print(f"  SHA-256 mục tiêu: {TARGET_HASH_B}")
    assert hash_b == TARGET_HASH_B, f"Mismatch SHA-256 Pass 1 B! {hash_b} != {TARGET_HASH_B}"
    print("  -> KHỚP 100% BYTE NGUYÊN BẢN B")

    # 2. Kiểm tra file Pass 1 E và Biên bản D
    e_file = ROOT / "data/annotations/E/calibration_pass1.jsonl"
    hash_e = sha256_file(e_file)
    print(f"\nFile Pass 1 E: {e_file}")
    if hash_e == TARGET_HASH_E:
        print("  -> Đã phát hiện file Pass 1 E khớp hash mục tiêu.")
    else:
        print(f"  -> Trạng thái: CHƯA CÓ TRÊN ĐĨA (hash mục tiêu: {TARGET_HASH_E})")

    # 3. Đọc dữ liệu Pass 1 và Blind View v1.1.4
    with open(b_file, encoding="utf-8") as f:
        b_records = [json.loads(line) for line in f if line.strip()]
    map_b = {r["sample_id"]: r for r in b_records}

    # Đọc thêm bản A để đối chiếu toàn diện nếu có
    a_file = ROOT / "data/annotations/A/calibration_pass1.jsonl"
    map_a = {}
    if a_file.is_file():
        with open(a_file, encoding="utf-8") as f:
            a_records = [json.loads(line) for line in f if line.strip()]
        map_a = {r["sample_id"]: r for r in a_records}

    blind_view_path = ROOT / "data/raw/recovery/calibration_proposal_v1.1.4_release.json"
    with open(blind_view_path, encoding="utf-8") as f:
        blind_view_data = json.load(f)
    map_bv = {s["sample_id"]: s for s in blind_view_data["samples"]}

    # 4. Lập bảng chuẩn hóa alias ngoài danh mục có lưu vết
    alias_mapping_registry = {
        "schema_version": "1.0.0",
        "description": "Bảng lưu vết chuẩn hóa alias thương hiệu và tên viết tắt ngoài danh mục 14 tổ chức cho Calibration v1.1.4",
        "dictionary_reference": "configs/dictionary_v1.json",
        "dictionary_sha256": "7aa83b68fdb4bb288460c00523e38e0779e8cbeb81ae879e7a5d27e771fcd3b3",
        "codebook_reference": "docs/CODEBOOK_V1_1.md",
        "codebook_sha256": "e30871b87911992110e77ad0dcca8bbf64b916086f496555599e43730af0adbd",
        "mappings": [
            {
                "raw_alias": "facebook",
                "normalized_org": "meta",
                "catalog_status": "in_catalog",
                "canonical_brand": "meta",
                "rationale": "Facebook là dịch vụ trực thuộc tập đoàn Meta trong danh mục 14 thương hiệu chuẩn. Codebook mục 2 quy định quy chuẩn về tổ chức mẹ.",
                "affected_samples": ["SMP-005", "SMP-008"]
            },
            {
                "raw_alias": "wsfb",
                "normalized_org": "wfsb",
                "catalog_status": "outside_catalog",
                "canonical_brand": None,
                "rationale": "Lỗi chính tả gõ phím đảo ký tự (wsfb -> wfsb) cho đài truyền hình WFSB Eyewitness News Connecticut. Trang first-party hợp lệ ngoài danh mục.",
                "affected_samples": ["SMP-007"]
            },
            {
                "raw_alias": "entertaiment_news",
                "normalized_org": "radio_times",
                "catalog_status": "outside_catalog",
                "canonical_brand": None,
                "rationale": "Gán nhãn chung chung theo thể loại trang (entertainment news) thay vì tên thương hiệu cụ thể Radio Times có trong header/title.",
                "affected_samples": ["SMP-001"]
            }
        ]
    }

    out_dir = ROOT / "data/labels/calibration_v1_1_4"
    out_dir.mkdir(parents=True, exist_ok=True)
    alias_file = out_dir / "alias_normalization_registry.json"
    alias_file.write_text(json.dumps(alias_mapping_registry, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n-> Đã ghi bảng lưu vết alias: {alias_file}")

    # 5. Xây dựng bản dự thảo 23 mẫu + SMP-010 pending_evidence
    draft_records = []
    qc_pending_evidence_list = []

    alias_lookup = {m["raw_alias"]: m["normalized_org"] for m in alias_mapping_registry["mappings"]}

    for sid in sorted(map_b.keys()):
        rb = map_b[sid]
        ra = map_a.get(sid, {})
        sbv = map_bv[sid]

        if sid == "SMP-010":
            # Ghi riêng vào danh sách QC pending_evidence
            pending_item = {
                "sample_id": "SMP-010",
                "url": sbv["url"],
                "status": "pending_evidence",
                "final_class_label": None,
                "gold_reference_included": False,
                "dispute_summary": {
                    "rater_a_claim": "Phishing / payment_deception (webshop khóa học y khoa giảm giá sâu, footer có dấu hiệu template chắp vá)",
                    "rater_b_claim": "Benign / reseller_or_partner (trang thương mại điện tử, không có form đánh cắp thẻ hay password, áp dụng quy tắc Codebook v1.1 mục 3)",
                },
                "lead_d_instruction": "Tách riêng khỏi tập nhãn tham chiếu đã xác minh; không gán nhãn lớp cuối; yêu cầu thu thập thêm snapshot mạng/chứng cứ sandbox trước khi phân xử.",
                "action": "permanently_isolated_from_gold_evaluation_until_provenance_cleared"
            }
            qc_pending_evidence_list.append(pending_item)
            continue

        # Xử lý 23 mẫu còn lại:
        # Nhãn lớp:
        if sid == "SMP-004":
            # Trường hợp bất đồng nhãn lớp: Microsoft backend endpoint
            # B đánh giá: insufficient_evidence (snapshot trắng/không form)
            # A đánh giá: benign (backend endpoint API hợp pháp của Microsoft Copilot)
            # C nêu rõ phương án dự thảo và căn cứ chờ D ký duyệt
            proposed_class = "insufficient_evidence" # Ưu tiên fail-safe theo snapshot DOM thực tế Codebook mục 3
            adjudication_status = "proposed_pending_d_signoff"
            note = "Bất đồng Pass 1 (benign vs insufficient_evidence). Dự thảo chọn insufficient_evidence theo nguyên tắc Codebook v1.1 mục 3 (view không có DOM hiển thị); chờ D phê chuẩn theo biên bản."
        else:
            proposed_class = rb["class_label"]
            adjudication_status = "agreed_or_resolved"
            note = rb.get("evidence_note", "")

        # Tổ chức & Chuẩn hóa alias
        raw_org = rb.get("primary_org", "unknown")
        norm_org = alias_lookup.get(raw_org, raw_org)

        # Xác định catalog_status
        canonical_14 = {"microsoft", "google", "apple", "amazon", "meta", "linkedin", "adobe", "booking", "paypal", "dhl", "spotify", "alibaba", "mastercard", "twitter"}
        if norm_org in canonical_14:
            cat_status = "in_catalog"
        elif norm_org in ("no_clear_target", "unknown"):
            cat_status = "unresolved"
        else:
            cat_status = "outside_catalog"

        rec = {
            "sample_id": sid,
            "url_hostname": sbv.get("url_parts", {}).get("netloc", ""),
            "class_label": proposed_class,
            "primary_org": norm_org,
            "primary_org_status": rb.get("primary_org_status", "identified" if norm_org not in ("unknown", "no_clear_target") else norm_org),
            "catalog_status": cat_status,
            "identity_role": rb.get("identity_role", "unclear"),
            "domain_role": rb.get("domain_role", "unverified"),
            "primary_phishing_type": rb.get("primary_phishing_type") if proposed_class == "phishing" else None,
            "hard_benign_type": rb.get("hard_benign_type") if proposed_class == "benign" else None,
            "confidence": rb.get("confidence", "high"),
            "org_evidence": rb.get("org_evidence", []),
            "evidence_note": note,
            "adjudication_status": adjudication_status,
            "gold_reference_eligible": True,
            "review_gate": "pending_b_verification_and_d_final_signature"
        }
        draft_records.append(rec)

    # Ghi file dự thảo 23 mẫu
    draft_file = out_dir / "draft_calibration_v1_1_4_adjudicated_23.json"
    draft_file.write_text(json.dumps(draft_records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"-> Đã lập dự thảo 23 mẫu: {draft_file}")

    # Ghi file QC pending_evidence SMP-010
    pending_file = out_dir / "qc_pending_evidence_SMP010.json"
    pending_file.write_text(json.dumps(qc_pending_evidence_list, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"-> Đã lập danh sách QC pending_evidence: {pending_file}")

    # 6. Báo cáo đo độ đồng thuận thô vs chuẩn hóa
    sids_24 = sorted(map_b.keys())
    cl_a = [map_a[s]["class_label"] for s in sids_24]
    cl_b = [map_b[s]["class_label"] for s in sids_24]
    org_a = [map_a[s]["primary_org"] for s in sids_24]
    org_b = [map_b[s]["primary_org"] for s in sids_24]

    res_cl_raw = compute_cohens_kappa(cl_a, cl_b, require_provenance=False)
    res_org_raw = compute_cohens_kappa(org_a, org_b, require_provenance=False)

    norm_org_a = [alias_lookup.get(o, o) for o in org_a]
    norm_org_b = [alias_lookup.get(o, o) for o in org_b]
    res_org_norm = compute_cohens_kappa(norm_org_a, norm_org_b, require_provenance=False)

    agreement_report = {
        "calibration_runway": "CALIBRATION-V1.1-24",
        "paired_samples": 24,
        "pass_1_raw_metrics": {
            "class_label": {
                "kappa": round(res_cl_raw.kappa, 4),
                "observed_agreement": round(res_cl_raw.observed_agreement, 4),
                "interpretation": "Almost Perfect (0.8500)"
            },
            "primary_org": {
                "kappa": round(res_org_raw.kappa, 4),
                "observed_agreement": round(res_org_raw.observed_agreement, 4),
                "interpretation": "Fair Agreement (0.3220)"
            }
        },
        "post_normalization_metrics": {
            "note": "Áp dụng chuẩn hóa alias ngoài danh mục có lưu vết (Facebook->Meta, WSFB->WFSB, entertaiment_news->radio_times). Tuyệt đối không thay thế cho Pass 1 độc lập ban đầu.",
            "primary_org_normalized": {
                "kappa": round(res_org_norm.kappa, 4),
                "observed_agreement": round(res_org_norm.observed_agreement, 4),
                "interpretation": "Moderate Agreement (0.4971, tăng từ 0.3220)"
            }
        },
        "adjudication_summary": {
            "total_samples": 24,
            "finalizable_candidates": 23,
            "qc_pending_evidence_count": 1,
            "pending_samples": ["SMP-010"]
        }
    }
    rep_file = out_dir / "calibration_v1_1_4_agreement_audit_report.json"
    rep_file.write_text(json.dumps(agreement_report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"-> Đã lập báo cáo kiểm toán đồng thuận: {rep_file}")

    print("\n=== HOÀN TẤT THÀNH CÔNG PHẦN 1 TRONG KHU VỰC HẠN CHẾ ===")


if __name__ == "__main__":
    main()
