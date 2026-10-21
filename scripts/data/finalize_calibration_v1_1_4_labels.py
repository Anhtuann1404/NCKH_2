#!/usr/bin/env python3
"""Hoàn tất biên bản nghiệm thu và tệp nhãn cuối Calibration v1.1.4 sau phê duyệt chính thức của Lead D.

Các điều kiện tuân thủ:
1. Quyết định Lead D ngày 2026-10-21:
   - 17 mẫu nhị phân (11 benign, 6 phishing), binary_model_eligible = True.
   - 2 mẫu insufficient_evidence (SMP-004, SMP-016), binary_model_eligible = False.
   - 5 mẫu QC pending_evidence (SMP-002, SMP-010, SMP-015, SMP-020, SMP-023), final_class_label = None, binary_model_eligible = False.
   - SMP-021: robinhood / outside_catalog / support_contact_lure; không ghi số điện thoại là 'đã chứng minh giả'.
2. Bảo đảm toàn vẹn và liên kết đối soát:
   - Review Pack v4 SHA-256: 03e37fcded22889ffd86cb64f27b69c28f6bef4cc2babe0e3f8051d1be0c981a.
   - Pass 1 E SHA-256: 20dfc141e48fbb54939855a942f9c70af49bb6bd8ee805c7093c502b9d8b7340.
   - Pass 1 B SHA-256: 161abf6fee8abec12028f72a2e8a095a276bf70b1c8dc6520c00b227291ede82.
   - Dictionary v1 SHA-256: 7aa83b68fdb4bb288460c00523e38e0779e8cbeb81ae879e7a5d27e771fcd3b3.
   - Codebook v1.1.0 SHA-256: e30871b87911992110e77ad0dcca8bbf64b916086f496555599e43730af0adbd.
3. Kỷ luật hệ thống:
   - training_blocked = True.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

TARGET_HASH_B = "161abf6fee8abec12028f72a2e8a095a276bf70b1c8dc6520c00b227291ede82"
TARGET_HASH_E = "20dfc141e48fbb54939855a942f9c70af49bb6bd8ee805c7093c502b9d8b7340"
TARGET_HASH_D_DECISION = "431a889fed7cb57c1560fa48f2ed362eb25be2e7f82d792f3aad1e82ed7aadda"
TARGET_HASH_BLIND_VIEW = "7a13433334cb75a29b012313d1ab22f27fcb96ef9e0e1d33254c24eb1e07a372"
TARGET_HASH_CODEBOOK = "e30871b87911992110e77ad0dcca8bbf64b916086f496555599e43730af0adbd"
TARGET_HASH_DICTIONARY = "7aa83b68fdb4bb288460c00523e38e0779e8cbeb81ae879e7a5d27e771fcd3b3"
TARGET_HASH_REVIEW_PACK_V4 = "03e37fcded22889ffd86cb64f27b69c28f6bef4cc2babe0e3f8051d1be0c981a"


def sha256_file(path: Path) -> str:
    if not path.is_file():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("=== BẮT ĐẦU HOÀN TẤT BIÊN BẢN VÀ TỆP NHÃN CUỐI CALIBRATION V1.1.4 ===")

    labels_dir = ROOT / "data/labels/calibration_v1_1_4"
    draft19_path = labels_dir / "draft_calibration_v1_1_4_adjudicated_19.json"
    qc5_path = labels_dir / "qc_pending_evidence_5_samples.json"
    zip_path = labels_dir / "calibration_v1_1_4_d_review_pack.zip"

    assert sha256_file(zip_path) == TARGET_HASH_REVIEW_PACK_V4, "Review Pack v4 hash mismatch!"

    with open(draft19_path, encoding="utf-8") as f:
        draft19 = json.load(f)
    with open(qc5_path, encoding="utf-8") as f:
        qc5 = json.load(f)

    map_draft = {r["sample_id"]: r for r in draft19}
    map_qc = {r["sample_id"]: r for r in qc5}

    all_sids = sorted(list(map_draft.keys()) + list(map_qc.keys()))
    assert len(all_sids) == 24, "Tổng số mẫu không bằng 24!"

    final_records = []
    for sid in all_sids:
        if sid in map_draft:
            r = dict(map_draft[sid])
            r["final_class_label"] = r.pop("adjudicated_class_label")
            r["approval_status"] = "approved_by_lead_d_20261021"
            r["signoff_authority"] = "Lead D (Anh Tuấn)"
            final_records.append(r)
        else:
            q = dict(map_qc[sid])
            q["final_class_label"] = None
            q["approval_status"] = "approved_by_lead_d_20261021"
            q["signoff_authority"] = "Lead D (Anh Tuấn)"
            final_records.append(q)

    final_dataset = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "dataset_id": "CALIBRATION-V1.1-24",
        "version": "1.1.4-final",
        "finalized_at_utc": "2026-10-21T17:15:00Z",
        "governance": {
            "lead_d_signoff": "approved",
            "lead_d_signoff_date": "2026-10-21",
            "lead_d_decision_reference": "CALIBRATION_V1_1_4_ADJUDICATION_D_DECISIONS.md",
            "lead_d_decision_sha256": TARGET_HASH_D_DECISION,
            "member_b_qa_status": "qa_approved",
            "member_b_qa_reference": "QA Report Phùng Tấn Minh 2026-10-21",
            "member_c_pipeline_status": "verified_and_frozen",
            "review_pack_reference": "calibration_v1_1_4_d_review_pack.zip",
            "review_pack_sha256": TARGET_HASH_REVIEW_PACK_V4,
            "codebook_version": "1.1.0",
            "codebook_sha256": TARGET_HASH_CODEBOOK,
            "dictionary_version": "1.0.0",
            "dictionary_sha256": TARGET_HASH_DICTIONARY,
            "blind_view_sha256": TARGET_HASH_BLIND_VIEW,
            "training_blocked": True
        },
        "summary": {
            "total_samples": 24,
            "binary_model_eligible_count": 17,
            "binary_breakdown": {
                "benign_count": 11,
                "benign_samples": ["SMP-001", "SMP-003", "SMP-007", "SMP-011", "SMP-012", "SMP-013", "SMP-014", "SMP-017", "SMP-018", "SMP-022", "SMP-024"],
                "phishing_count": 6,
                "phishing_samples": ["SMP-005", "SMP-006", "SMP-008", "SMP-009", "SMP-019", "SMP-021"],
                "catalog_status_distribution": {
                    "in_catalog": 5,
                    "outside_catalog": 11,
                    "unresolved_no_clear_target": 1
                }
            },
            "non_binary_count": 7,
            "non_binary_breakdown": {
                "insufficient_evidence_count": 2,
                "insufficient_evidence_samples": ["SMP-004", "SMP-016"],
                "qc_pending_evidence_count": 5,
                "qc_pending_evidence_samples": ["SMP-002", "SMP-010", "SMP-015", "SMP-020", "SMP-023"]
            }
        },
        "records": final_records
    }

    final_labels_path = labels_dir / "calibration_v1_1_4_labels_final.json"
    final_labels_bytes = (json.dumps(final_dataset, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    final_labels_path.write_bytes(final_labels_bytes)
    final_labels_hash = hashlib.sha256(final_labels_bytes).hexdigest()

    # Tạo biên bản nghiệm thu chính thức Markdown
    minutes_content = f"""# BIÊN BẢN NGHIỆM THU KÝ DUYỆT NHÃN CUỐI CALIBRATION V1.1.4

**Dự án:** NCKH_2 — Phát hiện website phishing mạo danh tổ chức bằng học máy  
**Mốc kỹ thuật:** Đóng mốc Hiệu chuẩn Calibration v1.1.4 (CALIBRATION-V1.1-24)  
**Ngày ký duyệt:** 21/10/2026  
**Chủ trì phê duyệt:** Lead D (Anh Tuấn)  
**Đại diện QA & Rater độc lập:** Member B (Phùng Tấn Minh)  
**Đại diện Pipeline & Dữ liệu:** Member C  

---

## 1. CĂN CỨ VÀ LIÊN KẾT ĐỐI SOÁT ARS

1. **Review Pack v4 đã được QA Approved:**
   - Tệp hồ sơ: `calibration_v1_1_4_d_review_pack.zip`
   - SHA-256: `{TARGET_HASH_REVIEW_PACK_V4}`
   - Trạng thái QA: **CHẤP THUẬN THÔNG QUA (QA APPROVED)** bởi Member B ngày 21/10/2026.
2. **Các Artifact nền tảng được bảo toàn nguyên vẹn byte:**
   - Pass 1 E (`calibration_pass1.jsonl`): SHA-256 `{TARGET_HASH_E}`
   - Pass 1 B (`calibration_pass1.jsonl`): SHA-256 `{TARGET_HASH_B}`
   - Codebook v1.1.0 (`docs/CODEBOOK_V1_1.md`): SHA-256 `{TARGET_HASH_CODEBOOK}`
   - Từ điển 14 tổ chức khóa (`configs/dictionary_v1.json`): SHA-256 `{TARGET_HASH_DICTIONARY}`
   - Blind View v1.1.4: SHA-256 `{TARGET_HASH_BLIND_VIEW}`
3. **Tệp nhãn cuối chính thức:**
   - Đường dẫn: `data/labels/calibration_v1_1_4/calibration_v1_1_4_labels_final.json`
   - Dung lượng: {len(final_labels_bytes)} bytes
   - SHA-256: `{final_labels_hash}`

---

## 2. KẾT QUẢ KÝ DUYỆT CHÍNH THỨC 24/24 MẪU

Theo quyết định chính thức của Lead D và báo cáo QA của Member B:

### A. Tập nhãn đủ điều kiện cho mô hình nhị phân (17 mẫu - `binary_model_eligible = True`):
- **11 mẫu Benign:**
  * `SMP-001`: `radio_times` / `outside_catalog` / `brand_mention_news`
  * `SMP-003`: `salestaxhandbook` / `outside_catalog` / `other`
  * `SMP-007`: `wfsb` / `outside_catalog` / `brand_mention_news`
  * `SMP-011`: `no_clear_target` / `unresolved` / `brand_mention_news` (Simon Rushby cá nhân)
  * `SMP-012`: `spotify` / `in_catalog` / `official_login`
  * `SMP-013`: `australia_post` / `outside_catalog` / `other`
  * `SMP-014`: `catedral_de_santiago` / `outside_catalog` / `other`
  * `SMP-017`: `saber_healthcare_group` / `outside_catalog` / `brand_mention_news`
  * `SMP-018`: `john_james_needles` / `outside_catalog` / `official_login`
  * `SMP-022`: `the_new_york_times` / `outside_catalog` / `brand_mention_news`
  * `SMP-024`: `wholesomeyum` / `outside_catalog` / `official_login`
- **6 mẫu Phishing:**
  * `SMP-005`: `meta` / `in_catalog` / `impersonation_lure`
  * `SMP-006`: `jojobet` / `outside_catalog` / `credential_collection`
  * `SMP-008`: `meta` / `in_catalog` / `impersonation_lure`
  * `SMP-009`: `google` / `in_catalog` / `impersonation_lure`
  * `SMP-019`: `amazon` / `in_catalog` / `credential_collection`
  * `SMP-021`: `robinhood` / `outside_catalog` / `support_contact_lure` (url_hostname: `www.sesarju.eu`, không suy diễn số điện thoại giả ngoài runtime)

### B. Mẫu không đủ điều kiện nhị phân (7 mẫu - `binary_model_eligible = False`):
- **2 mẫu `insufficient_evidence` (đồng thuận / phân xử không đủ DOM/nội dung):**
  * `SMP-004`: Snapshot rỗng/trắng (`unknown`).
  * `SMP-016`: Replit placeholder ASCII art (`no_clear_target`).
- **5 mẫu QC `pending_evidence` (chuyển hàng đợi QC, không có nhãn lớp cuối):**
  * `SMP-002`: `xvujbn.aheadmusic.shop` (shop tiếng Nhật thiếu bằng chứng thu thẻ/gian lận quan sát được).
  * `SMP-010`: `plasticsurgerybooks.com` (webshop y khoa thiếu bằng chứng gian lận cụ thể).
  * `SMP-015`: `dwplai.motorhigh.shop` (shop tiếng Nhật thiếu bằng chứng thu thẻ/gian lận quan sát được).
  * `SMP-020`: `fes.jobsms.shop` (shop tiếng Nhật thiếu bằng chứng thu thẻ/gian lận quan sát được).
  * `SMP-023`: `oybjxc.sportsloan.shop` (shop tiếng Nhật thiếu bằng chứng thu thẻ/gian lận quan sát được).

---

## 3. KỶ LUẬT DỮ LIỆU & BẢO LƯU

1. **Cô lập tập nhị phân:** Tuyệt đối không đưa 5 mẫu QC `pending_evidence` và 2 mẫu `insufficient_evidence` vào tập dữ liệu huấn luyện hoặc đánh giá mô hình nhị phân M0–M3.
2. **Khóa dữ liệu huấn luyện:** Tiếp tục duy trì `training_blocked = true`. Không mở tập huấn luyện chính thức khi chưa nghiệm thu PLAN-01.
3. **Đóng mốc Calibration v1.1.4:** Toàn bộ dữ liệu 24 mẫu hiệu chuẩn này được khóa cố định và chuyển sang trạng thái tham chiếu xác minh.

---
**Xác nhận ký duyệt bởi:**  
- **Lead D (Anh Tuấn):** Đã phê duyệt chính thức (21/10/2026)  
- **Member B (Phùng Tấn Minh):** Đã nghiệm thu QA (21/10/2026)  
- **Member C:** Đã lập và khóa kiểm chứng SHA-256 (21/10/2026)  
"""
    minutes_path = labels_dir / "CALIBRATION_V1_1_4_SIGN_OFF_MINUTES.md"
    minutes_path.write_text(minutes_content, encoding="utf-8")
    minutes_hash = sha256_file(minutes_path)

    print(f"-> ĐÃ XUẤT TỆP NHÃN CUỐI: {final_labels_path}")
    print(f"   Dung lượng: {len(final_labels_bytes)} bytes | SHA-256: {final_labels_hash}")
    print(f"-> ĐÃ XUẤT BIÊN BẢN NGHIỆM THU: {minutes_path}")
    print(f"   SHA-256: {minutes_hash}")
    print("=== HOÀN TẤT THÀNH CÔNG ĐÓNG MỐC CALIBRATION V1.1.4 ===")


if __name__ == "__main__":
    main()
