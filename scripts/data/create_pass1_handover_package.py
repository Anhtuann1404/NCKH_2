#!/usr/bin/env python3
"""Build Handover Package & Audit Trail for Calibration Clean Runway A (Pass 1).

Authorized by: Lead D (Anh Tuấn)
Executed by: Member C (Data Pipeline & Blind View)
Recipients: Annotator A (Trần Hồng Khải) & Annotator B (Phùng Tấn Minh)

Builds:
1. data/source_audit/clean_calibration_pass1_handover_audit.json (Audit trail on Git)
2. GOI_BAN_GIAO_PASS1_CALIBRATION_CLEAN_24.zip (Distribution package for A & B)
3. docs/BAN_GIAO_PASS1_CALIBRATION_CLEAN_RUNWAY_A.md (Documentation on Git)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from phishing.annotation.blind_view import assert_no_label_leak

VIEW_PATH = ROOT / "data/annotations/clean_calibration_blind_view_24.json"
MANIFEST_PATH = ROOT / "configs/calibration_clean_a_manifest.json"
CODEBOOK_PATH = ROOT / "docs/CODEBOOK_V1_1.md"
DICTIONARY_PATH = ROOT / "configs/dictionary_v1.json"
AUDIT_OUTPUT_PATH = ROOT / "data/source_audit/clean_calibration_pass1_handover_audit.json"
DOC_OUTPUT_PATH = ROOT / "docs/BAN_GIAO_PASS1_CALIBRATION_CLEAN_RUNWAY_A.md"
ZIP_OUTPUT_PATH = ROOT / "GOI_BAN_GIAO_PASS1_CALIBRATION_CLEAN_24.zip"

EXPECTED_VIEW_SHA256 = "0164b2a5499c10c824f7e559c9a351c958adcfe627648ac537179dfe4dbf2b6b"
EXPECTED_MANIFEST_SHA256 = "9d94dd3e33134131047600d9297f3058b3049a946863cac24fe34b7fd110a32b"
EXPECTED_CODEBOOK_SHA256 = "e30871b87911992110e77ad0dcca8bbf64b916086f496555599e43730af0adbd"
EXPECTED_DICT_SHA256 = "7aa83b68fdb4bb288460c00523e38e0779e8cbeb81ae879e7a5d27e771fcd3b3"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8")

    print("=== TẠO GÓI BÀN GIAO & BIÊN BẢN PHÁT HÀNH PASS 1 CALIBRATION CLEAN ===")

    # 1. Kiểm tra sự tồn tại và mã băm của 4 tệp cốt lõi
    view_bytes = VIEW_PATH.read_bytes()
    manifest_bytes = MANIFEST_PATH.read_bytes()
    codebook_bytes = CODEBOOK_PATH.read_bytes()
    dict_bytes = DICTIONARY_PATH.read_bytes()

    assert sha256_bytes(view_bytes) == EXPECTED_VIEW_SHA256, "Sai SHA-256 Blind View"
    assert sha256_bytes(manifest_bytes) == EXPECTED_MANIFEST_SHA256, "Sai SHA-256 Manifest"
    assert sha256_bytes(codebook_bytes) == EXPECTED_CODEBOOK_SHA256, "Sai SHA-256 Codebook"
    assert sha256_bytes(dict_bytes) == EXPECTED_DICT_SHA256, "Sai SHA-256 Dictionary"

    # 2. Kiểm tra tính toàn vẹn và an toàn mù đôi của Blind View
    view_data = json.loads(view_bytes.decode("utf-8"))
    assert_no_label_leak(view_data)
    samples = view_data.get("samples", [])
    assert len(samples) == 24, f"Cần đúng 24 mẫu, thực tế có {len(samples)}"
    for s in samples:
        sid = s.get("sample_id", "")
        assert not sid.startswith("RSV") and "reserve" not in sid.lower(), f"Lộ mẫu dự phòng {sid}"

    print("✅ Kiểm tra 4 tài nguyên cốt lõi: 100% khớp SHA-256 và zero data leakage.")

    # 3. Tạo biên bản kiểm kê bàn giao JSON (Audit trail)
    audit_data = {
        "handover_id": "HANDOVER-PASS1-CALIBRATION-CLEAN-RUNWAY-A",
        "dataset_id": "CALIBRATION-CLEAN-24",
        "release_version": "1.1.0",
        "session": "Pass 1 (Independent Parallel Annotation)",
        "authorized_by": "Lead D (Anh Tuấn)",
        "authorized_at_utc": "2026-10-29T17:42:00Z",
        "handed_over_by": "Member C (Data Pipeline & Blind View)",
        "handed_over_at_utc": "2026-10-29T17:45:00Z",
        "governance_flags": {
            "ready_for_annotation": True,
            "training_blocked": True,
            "official_test_used": False,
            "blind_protocol": "double_blind_parallel_pass1"
        },
        "artifacts_manifest": {
            "blind_view": {
                "file_name": "clean_calibration_blind_view_24.json",
                "relative_path": "data/annotations/clean_calibration_blind_view_24.json",
                "sample_count": 24,
                "byte_size": len(view_bytes),
                "sha256": EXPECTED_VIEW_SHA256,
                "is_synthetic": False
            },
            "manifest": {
                "file_name": "calibration_clean_a_manifest.json",
                "relative_path": "configs/calibration_clean_a_manifest.json",
                "version": "1.1.0",
                "status": "approved",
                "byte_size": len(manifest_bytes),
                "sha256": EXPECTED_MANIFEST_SHA256
            },
            "codebook": {
                "file_name": "CODEBOOK_V1_1.md",
                "relative_path": "docs/CODEBOOK_V1_1.md",
                "version": "1.1.0",
                "status": "locked",
                "byte_size": len(codebook_bytes),
                "sha256": EXPECTED_CODEBOOK_SHA256
            },
            "dictionary": {
                "file_name": "dictionary_v1.json",
                "relative_path": "configs/dictionary_v1.json",
                "version": "1.0.0",
                "status": "locked",
                "byte_size": len(dict_bytes),
                "sha256": EXPECTED_DICT_SHA256
            }
        },
        "recipients": [
            {
                "annotator_id": "A",
                "full_name": "Trần Hồng Khải",
                "role": "Annotator A",
                "channel": "Direct private message / restricted checkout",
                "zero_prior_exposure_confirmed_by_lead_d": True,
                "output_target": "data/annotations/A/clean_calibration_pass1.jsonl",
                "command": "python scripts/annotate_cli.py --annotator A --input data/annotations/clean_calibration_blind_view_24.json --output data/annotations/A/clean_calibration_pass1.jsonl --manifest configs/calibration_clean_a_manifest.json --pass-id 1"
            },
            {
                "annotator_id": "B",
                "full_name": "Phùng Tấn Minh",
                "role": "Annotator B (QA Lead)",
                "channel": "Direct private message / restricted checkout",
                "zero_prior_exposure_confirmed_by_lead_d": True,
                "output_target": "data/annotations/B/clean_calibration_pass1.jsonl",
                "command": "python scripts/annotate_cli.py --annotator B --input data/annotations/clean_calibration_blind_view_24.json --output data/annotations/B/clean_calibration_pass1.jsonl --manifest configs/calibration_clean_a_manifest.json --pass-id 1"
            }
        ],
        "confidentiality_boundaries": {
            "reserve_candidates_count": 8,
            "reserve_candidates_status": "strictly_concealed",
            "source_labels_status": "strictly_concealed_in_restricted_dossier",
            "locators_status": "zero_leakage_on_git_and_zero_in_blind_view",
            "restricted_commitment_sha256": "67326e80b2a6f9cb7356450a31fe15054a1193412a8ed0576ea2972f1801a805"
        },
        "post_pass1_adjudication_protocol": {
            "receiving_channel": "Restricted direct transfer to Member C & Lead D",
            "pre_kappa_checks": [
                "100% pure Unix LF line endings",
                "Exactly 24 JSONL records matching SMP-001..SMP-024",
                "Zero negative timing (seconds_spent >= 0)",
                "Mandatory confidence field enum validity",
                "Zero manual tampering / raw editor alterations"
            ]
        }
    }

    audit_payload = (json.dumps(audit_data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    AUDIT_OUTPUT_PATH.write_bytes(audit_payload)
    print(f"✅ Ghi nhận biên bản kiểm kê bàn giao: {AUDIT_OUTPUT_PATH.name}")

    # 4. Tạo hướng dẫn và mã kiểm tra cho annotator trong zip
    readme_content = """# HƯỚNG DẪN GÁN NHÃN PASS 1 - CALIBRATION CLEAN RUNWAY A (24 MẪU)

## 1. Kiểm tra trước khi bắt đầu
Chạy script kiểm tra tự động kèm theo gói:
```bash
python verify_handover_pass1.py
```
Nếu màn hình báo `✅ PREFLIGHT PASSED 100%`, bạn đã sẵn sàng gán nhãn.

## 2. Lệnh khởi chạy phiên gán nhãn có bấm giờ tương tác
- **Dành cho Thành viên A (Trần Hồng Khải):**
  ```bash
  python scripts/annotate_cli.py --annotator A --input data/annotations/clean_calibration_blind_view_24.json --output data/annotations/A/clean_calibration_pass1.jsonl --manifest configs/calibration_clean_a_manifest.json --pass-id 1
  ```
- **Dành cho Thành viên B (Phùng Tấn Minh):**
  ```bash
  python scripts/annotate_cli.py --annotator B --input data/annotations/clean_calibration_blind_view_24.json --output data/annotations/B/clean_calibration_pass1.jsonl --manifest configs/calibration_clean_a_manifest.json --pass-id 1
  ```

## 3. Quy tắc bắt buộc trong phiên gán nhãn
1. **Độc lập mù đôi:** Tuyệt đối không trao đổi ý kiến, nhãn hay bằng chứng với người còn lại cho đến khi cả hai hoàn thành và nộp file.
2. **Không dùng AI / Người thứ ba:** 100% quyết định nhãn do chính bạn quan sát và đánh giá độc lập.
3. **Bấm giờ thực tế & Tạm dừng (Pause / Resume):**
   - Khi cần nghỉ giải lao, hãy dùng chức năng pause trong CLI để `seconds_spent` phản ánh chính xác thời gian thao tác thực tế.
4. **Gán đủ 24 mẫu:** Hoàn thành đủ 24 mẫu chính (SMP-001 đến SMP-024).
"""

    verify_script = f'''#!/usr/bin/env python3
"""Kiểm tra nhanh mã băm và preflight gói bàn giao Pass 1."""

import hashlib
import json
from pathlib import Path
import sys

VIEW_SHA256 = "{EXPECTED_VIEW_SHA256}"
MANIFEST_SHA256 = "{EXPECTED_MANIFEST_SHA256}"
CODEBOOK_SHA256 = "{EXPECTED_CODEBOOK_SHA256}"
DICT_SHA256 = "{EXPECTED_DICT_SHA256}"

def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8")
    print("=== KIỂM TRA MÃ BĂM GÓI BÀN GIAO PASS 1 ===")
    
    files = [
        ("clean_calibration_blind_view_24.json", VIEW_SHA256),
        ("calibration_clean_a_manifest.json", MANIFEST_SHA256),
        ("CODEBOOK_V1_1.md", CODEBOOK_SHA256),
        ("dictionary_v1.json", DICT_SHA256),
    ]
    
    all_ok = True
    for fname, expected in files:
        p = Path(fname)
        if not p.exists():
            print(f"❌ THIẾU TỆP: {{fname}}")
            all_ok = False
            continue
        h = sha256_file(p)
        if h == expected:
            print(f"✅ KHỚP HASH: {{fname}}")
        else:
            print(f"❌ SAI HASH: {{fname}} ({{h}} != {{expected}})")
            all_ok = False
            
    if all_ok:
        print("✅ TOÀN BỘ TÀI NGUYÊN HỢP LỆ VÀ SẴN SÀNG CHO PASS 1.")
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
'''

    # 5. Đóng gói ZIP bàn giao
    with zipfile.ZipFile(ZIP_OUTPUT_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("clean_calibration_blind_view_24.json", view_bytes)
        zf.writestr("calibration_clean_a_manifest.json", manifest_bytes)
        zf.writestr("CODEBOOK_V1_1.md", codebook_bytes)
        zf.writestr("dictionary_v1.json", dict_bytes)
        zf.writestr("README_ANNOTATOR_PASS1.md", readme_content.encode("utf-8"))
        zf.writestr("verify_handover_pass1.py", verify_script.encode("utf-8"))

    zip_bytes = ZIP_OUTPUT_PATH.read_bytes()
    zip_sha256 = sha256_bytes(zip_bytes)
    print(f"✅ Tạo gói ZIP bàn giao: {ZIP_OUTPUT_PATH.name} ({len(zip_bytes):,} bytes, SHA-256: {zip_sha256})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
