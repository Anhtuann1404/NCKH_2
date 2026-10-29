#!/usr/bin/env python3
"""Build Handover Package & Audit Trail for Calibration Clean Runway A (Pass 1).

Authorized by: Lead D (Anh Tuấn)
Executed by: Member C (Data Pipeline & Blind View)
Recipients: Annotator A (Trần Hồng Khải) & Annotator B (Phùng Tấn Minh)

Operational Rectifications (Lead D directive):
1. Differentiate static SHA-256 hash verification (verify_handover_pass1.py) from runtime preflight (annotate_cli.py).
2. Detail extraction of flat ZIP assets into Git checkout directories (data/annotations/, configs/, docs/).
3. Inquire and record session launch status (started vs pending) without disrupting valid sessions.
4. Raw bytes receipt protocol: calculate initial SHA-256, preserve OS-native line endings (CRLF on Windows / LF on Unix),
   epistemic humility (record provenance and annotator confirmation, not claiming mathematical proof of zero manual tampering).
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

    print("=== TẠO GÓI BÀN GIAO & BIÊN BẢN PHÁT HÀNH PASS 1 CALIBRATION CLEAN (BẢN ĐÍNH CHÍNH) ===")

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

    # 3. Tạo biên bản kiểm kê bàn giao JSON (Audit trail) có cập nhật đính chính vận hành
    audit_data = {
        "handover_id": "HANDOVER-PASS1-CALIBRATION-CLEAN-RUNWAY-A",
        "dataset_id": "CALIBRATION-CLEAN-24",
        "release_version": "1.1.0",
        "session": "Pass 1 (Independent Parallel Annotation)",
        "authorized_by": "Lead D (Anh Tuấn)",
        "authorized_at_utc": "2026-10-29T17:42:00Z",
        "handed_over_by": "Member C (Data Pipeline & Blind View)",
        "handed_over_at_utc": "2026-10-29T17:45:00Z",
        "operational_rectification_at_utc": "2026-10-29T18:10:00Z",
        "governance_flags": {
            "ready_for_annotation": True,
            "training_blocked": True,
            "official_test_used": False,
            "blind_protocol": "double_blind_parallel_pass1"
        },
        "artifacts_manifest": {
            "blind_view": {
                "file_name": "clean_calibration_blind_view_24.json",
                "target_relative_path": "data/annotations/clean_calibration_blind_view_24.json",
                "sample_count": 24,
                "byte_size": len(view_bytes),
                "sha256": EXPECTED_VIEW_SHA256,
                "is_synthetic": False
            },
            "manifest": {
                "file_name": "calibration_clean_a_manifest.json",
                "target_relative_path": "configs/calibration_clean_a_manifest.json",
                "version": "1.1.0",
                "status": "approved",
                "byte_size": len(manifest_bytes),
                "sha256": EXPECTED_MANIFEST_SHA256
            },
            "codebook": {
                "file_name": "CODEBOOK_V1_1.md",
                "target_relative_path": "docs/CODEBOOK_V1_1.md",
                "version": "1.1.0",
                "status": "locked",
                "byte_size": len(codebook_bytes),
                "sha256": EXPECTED_CODEBOOK_SHA256
            },
            "dictionary": {
                "file_name": "dictionary_v1.json",
                "target_relative_path": "configs/dictionary_v1.json",
                "version": "1.0.0",
                "status": "locked",
                "byte_size": len(dict_bytes),
                "sha256": EXPECTED_DICT_SHA256
            }
        },
        "verification_separation": {
            "hash_check_tool": "verify_handover_pass1.py (static SHA-256 integrity check of extracted files)",
            "runtime_preflight_tool": "scripts/annotate_cli.py (validates manifest governance flags, mutual acceptance, locks, and schema prior to sample rendering)"
        },
        "workspace_placement_policy": {
            "zip_structure": "flat",
            "required_environment": "Git checkout on branch feat/c-calibration-v1-1-4-adjudication (containing scripts/annotate_cli.py with pause/resume support)",
            "file_mapping": {
                "clean_calibration_blind_view_24.json": "data/annotations/clean_calibration_blind_view_24.json",
                "calibration_clean_a_manifest.json": "configs/calibration_clean_a_manifest.json",
                "CODEBOOK_V1_1.md": "docs/CODEBOOK_V1_1.md",
                "dictionary_v1.json": "configs/dictionary_v1.json"
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
        "raw_receipt_and_epistemic_humility_protocol": {
            "receiving_channel": "Restricted direct transfer to Member C & Lead D",
            "raw_bytes_preservation": "Calculate initial raw SHA-256 immediately upon receipt before any file read or copy; archive untouched raw bytes in restricted storage",
            "line_endings_policy": "Record natural line endings as written by CLI on annotator OS (Windows CRLF or Unix LF); DO NOT modify or normalize original file",
            "epistemic_humility_statement": "Acknowledge that lack of manual tampering cannot be mathematically proven solely from JSONL content. Evidence consists of cryptographic provenance, sequential timestamps, non-negative seconds_spent, and written confirmation of zero manual tampering from the annotator."
        }
    }

    audit_payload = (json.dumps(audit_data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    AUDIT_OUTPUT_PATH.write_bytes(audit_payload)
    print(f"✅ Ghi nhận biên bản kiểm kê bàn giao đính chính: {AUDIT_OUTPUT_PATH.name}")

    # 4. Tạo hướng dẫn rõ ràng trong README_ANNOTATOR_PASS1.md
    readme_content = """# HƯỚNG DẪN BỐ TRÍ TỆP & GÁN NHÃN PASS 1 - CALIBRATION CLEAN RUNWAY A (24 MẪU)

## 1. Lưu ý quan trọng về cấu trúc tệp (Đọc kỹ trước khi thực hiện)
Gói ZIP này có **cấu trúc thư mục phẳng** và **không chứa mã nguồn CLI**. 
Bạn cần làm việc bên trong thư mục gốc của repository Git dự án (`NCKH_2`) đã cập nhật nhánh mới nhất:
```bash
git fetch origin
git checkout feat/c-calibration-v1-1-4-adjudication
git pull origin feat/c-calibration-v1-1-4-adjudication
```

## 2. Bố trí tệp từ ZIP vào đúng thư mục trong repository
Sau khi giải nén ZIP, bạn hãy di chuyển/sao chép các tệp vào đúng thư mục tương ứng trong repo:
- `clean_calibration_blind_view_24.json`  -> `data/annotations/`
- `calibration_clean_a_manifest.json`     -> `configs/`
- `CODEBOOK_V1_1.md`                      -> `docs/`
- `dictionary_v1.json`                   -> `configs/`
- `verify_handover_pass1.py`             -> Thư mục gốc repo (để chạy kiểm tra)

## 3. Bước 1: Kiểm tra tính toàn vẹn mã băm (Hash Check)
Chạy script kiểm tra mã băm tại thư mục gốc repository:
```bash
python verify_handover_pass1.py
```
Script này sẽ đối chiếu mã SHA-256 của 4 tệp. Khi màn hình báo `✅ TOÀN BỘ 4 TỆP KHỚP MÃ BĂM SHA-256`, các tệp đã được bố trí chính xác.
*(Lưu ý: Đây là bước kiểm tra hash tệp tĩnh. Quá trình kiểm tra preflight nghiệp vụ thật sẽ do CLI tự động thực hiện khi khởi chạy).*

## 4. Bước 2: Khởi chạy phiên gán nhãn có bấm giờ tương tác
Khi chạy lệnh dưới đây, CLI sẽ tự động thực thi **Preflight Nghiệm thu Thật** (kiểm tra manifest, trạng thái khóa, số mẫu, mã băm đĩa) trước khi hiển thị mẫu đầu tiên:

- **Dành cho Thành viên A (Trần Hồng Khải):**
  ```bash
  python scripts/annotate_cli.py --annotator A --input data/annotations/clean_calibration_blind_view_24.json --output data/annotations/A/clean_calibration_pass1.jsonl --manifest configs/calibration_clean_a_manifest.json --pass-id 1
  ```
- **Dành cho Thành viên B (Phùng Tấn Minh):**
  ```bash
  python scripts/annotate_cli.py --annotator B --input data/annotations/clean_calibration_blind_view_24.json --output data/annotations/B/clean_calibration_pass1.jsonl --manifest configs/calibration_clean_a_manifest.json --pass-id 1
  ```

## 5. Báo cáo thông số khởi chạy cho Lead D & Member C
Khi vừa khởi chạy thành công (mẫu 1 xuất hiện), vui lòng gửi tin nhắn ngắn báo lại:
1. Commit hash CLI: `git rev-parse --short HEAD`
2. Kết quả kiểm tra hash (output của `verify_handover_pass1.py`)
3. Dòng thông báo Preflight thành công của CLI

## 6. Quy chuẩn bắt buộc trong phiên gán nhãn
1. **Độc lập mù đôi:** Tuyệt đối không trao đổi ý kiến, nhãn hay bằng chứng với người còn lại cho đến khi cả hai hoàn thành và nộp file.
2. **Không dùng AI / Người thứ ba:** 100% quyết định nhãn do chính bạn quan sát và đánh giá độc lập.
3. **Bấm giờ thực tế & Tạm dừng (Pause / Resume):**
   - Khi cần nghỉ giải lao, hãy dùng phím tạm dừng trong CLI để `seconds_spent` phản ánh chính xác thời gian thao tác thực tế.
4. **Trường confidence:** Bắt buộc nhập mức tự tin (`low`, `medium`, `high`) theo Codebook v1.1.
5. **Gán đủ 24 mẫu:** Hoàn thành đủ 24 mẫu chính (SMP-001 đến SMP-024). Nếu gián đoạn, chạy lại lệnh trên để CLI tự động resume.
"""

    verify_script = f'''#!/usr/bin/env python3
"""Kiểm tra mã băm SHA-256 các tệp bàn giao Pass 1 sau khi bố trí vào repository."""

import hashlib
from pathlib import Path
import sys

VIEW_SHA256 = "{EXPECTED_VIEW_SHA256}"
MANIFEST_SHA256 = "{EXPECTED_MANIFEST_SHA256}"
CODEBOOK_SHA256 = "{EXPECTED_CODEBOOK_SHA256}"
DICT_SHA256 = "{EXPECTED_DICT_SHA256}"

def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8")
    print("=== KIỂM TRA MÃ BĂM TĨNH GÓI BÀN GIAO PASS 1 (HASH CHECK) ===")
    print("Mục đích: Xác minh tính toàn vẹn 4 tệp sau khi bố trí vào đúng thư mục repo.")
    print("Lưu ý: Preflight thật sẽ do scripts/annotate_cli.py thực hiện khi khởi chạy.\\n")
    
    files = [
        ("Blind View 24 mẫu", Path("data/annotations/clean_calibration_blind_view_24.json"), Path("clean_calibration_blind_view_24.json"), VIEW_SHA256),
        ("Manifest đã duyệt", Path("configs/calibration_clean_a_manifest.json"), Path("calibration_clean_a_manifest.json"), MANIFEST_SHA256),
        ("Codebook v1.1", Path("docs/CODEBOOK_V1_1.md"), Path("CODEBOOK_V1_1.md"), CODEBOOK_SHA256),
        ("Từ điển 14 tổ chức", Path("configs/dictionary_v1.json"), Path("dictionary_v1.json"), DICT_SHA256),
    ]
    
    all_ok = True
    for desc, repo_p, local_p, expected in files:
        target_p = repo_p if repo_p.exists() else local_p
        if not target_p.exists():
            print(f"❌ THIẾU TỆP: {{desc}} (không tìm thấy tại {{repo_p}} hoặc {{local_p}})")
            all_ok = False
            continue
        h = sha256_file(target_p)
        if h == expected:
            print(f"✅ KHỚP HASH: {{desc}} ({{target_p}})")
        else:
            print(f"❌ SAI HASH: {{desc}} ({{target_p}}): {{h}} != {{expected}}")
            all_ok = False
            
    print("-" * 65)
    if all_ok:
        print("✅ TOÀN BỘ 4 TỆP KHỚP MÃ BĂM SHA-256.")
        print("👉 Bạn đã sẵn sàng khởi chạy scripts/annotate_cli.py để bắt đầu phiên gán nhãn.")
        return 0
    else:
        print("❌ CÓ TỆP CHƯA ĐÚNG VỊ TRÍ HOẶC SAI MÃ BĂM. Vui lòng đối soát lại theo README.")
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
    print(f"✅ Tạo gói ZIP bàn giao cập nhật: {ZIP_OUTPUT_PATH.name} ({len(zip_bytes):,} bytes, SHA-256: {zip_sha256})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
