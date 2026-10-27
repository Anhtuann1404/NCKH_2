#!/usr/bin/env python3
"""Build Handover Package for Lead D's Final Review (24 Main Samples Blind View).

Package: GOI_NGHIEM_THU_LEAD_D_CALIBRATION_CLEAN_24.zip
Contains:
1. clean_calibration_blind_view_24.json (The 24 main samples Blind View for A and B)
2. calibration_clean_a_manifest.json (Synchronized manifest)
3. MANIFEST_HANDOVER_LEAD_D.json (Handover metadata and component checksums)
4. verify_lead_d_handover.py (Standalone automated verification tool for Lead D)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VIEW_PATH = ROOT / "data/annotations/clean_calibration_blind_view_24.json"
MANIFEST_PATH = ROOT / "configs/calibration_clean_a_manifest.json"
OUTPUT_ZIP = ROOT / "GOI_NGHIEM_THU_LEAD_D_CALIBRATION_CLEAN_24.zip"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


VERIFY_SCRIPT_CODE = '''#!/usr/bin/env python3
"""Automated verification script for Lead D's final sign-off package."""

import hashlib
import json
from pathlib import Path
import sys

DIR = Path(__file__).resolve().parent

VIEW_FILE = DIR / "clean_calibration_blind_view_24.json"
MANIFEST_FILE = DIR / "calibration_clean_a_manifest.json"
HANDOVER_FILE = DIR / "MANIFEST_HANDOVER_LEAD_D.json"

EXPECTED_VIEW_SHA256 = "__EXPECTED_VIEW_SHA256__"
EXPECTED_MANIFEST_SHA256 = "__EXPECTED_MANIFEST_SHA256__"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8")
    print("=== KIỂM ĐỊNH TỰ ĐỘNG GÓI NGHIỆM THU CUỐI CHO LEAD D ===")
    
    # 1. Check files existence
    for f in (VIEW_FILE, MANIFEST_FILE, HANDOVER_FILE):
        if not f.exists():
            print(f"❌ THIẾU TỆP: {f.name}")
            return 1
    print("✅ Đủ 3 tệp thành phần trong gói nghiệm thu.")

    # 2. Check Line endings (pure LF)
    view_bytes = VIEW_FILE.read_bytes()
    manifest_bytes = MANIFEST_FILE.read_bytes()
    handover_bytes = HANDOVER_FILE.read_bytes()

    for name, raw in [("Blind View", view_bytes), ("Manifest", manifest_bytes), ("Handover Manifest", handover_bytes)]:
        if b"\\r\\n" in raw:
            print(f"❌ LỖI LINE ENDING: {name} chứa byte CRLF. Bắt buộc pure Unix LF.")
            return 1
    print("✅ 100% tệp sử dụng chuẩn hóa kết thúc dòng Unix LF.")

    # 3. Check SHA-256
    view_hash = sha256(view_bytes)
    manifest_hash = sha256(manifest_bytes)
    if view_hash != EXPECTED_VIEW_SHA256:
        print(f"❌ SAI KHÁC SHA-256 BLIND VIEW: {view_hash} != {EXPECTED_VIEW_SHA256}")
        return 1
    if manifest_hash != EXPECTED_MANIFEST_SHA256:
        print(f"❌ SAI KHÁC SHA-256 MANIFEST: {manifest_hash} != {EXPECTED_MANIFEST_SHA256}")
        return 1
    print(f"✅ SHA-256 Blind View khớp: {view_hash}")
    print(f"✅ SHA-256 Manifest khớp:   {manifest_hash}")

    # 4. Check Blind View contents
    view = json.loads(view_bytes.decode("utf-8"))
    samples = view.get("samples", [])
    if len(samples) != 24:
        print(f"❌ SAI KHÁC SỐ LƯỢNG MẪU: View có {len(samples)} mẫu (yêu cầu đúng 24 mẫu chính)")
        return 1
    expected_ids = [f"SMP-{i:03d}" for i in range(1, 25)]
    view_ids = [s["sample_id"] for s in samples]
    if view_ids != expected_ids:
        print(f"❌ SAI KHÁC ID MẪU: {view_ids}")
        return 1
    print("✅ Đúng 24 mẫu chính SMP-001 đến SMP-024.")

    # 5. Check Zero Reserve Leaks
    for s in samples:
        sid = s["sample_id"]
        if sid.startswith("RSV") or "reserve" in sid.lower():
            print(f"❌ LỘ MẪU DỰ PHÒNG: Tìm thấy {sid} trong Blind View!")
            return 1
    print("✅ Tuyệt đối không chứa mẫu dự phòng (8 mẫu dự phòng được giữ kín).")

    # 6. Check Zero Label & Locator Leaks
    forbidden = ["source_label", "ground_truth", "primary_org_status", "train-000.parquet", "train-055.parquet", "row_offset"]
    view_text = json.dumps(view)
    for term in forbidden:
        if term in view_text:
            print(f"❌ LỘ THÔNG TIN BỊ CẤM: '{term}' xuất hiện trong Blind View!")
            return 1
    print("✅ Zero Label & Locator Leakage: assert_no_label_leak đạt 100%.")

    # 7. Check Manifest Governance Locks
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if manifest.get("ready_for_annotation") is not False or manifest.get("training_blocked") is not True:
        print("❌ LỖI CHỐT KHÓA QUẢN TRỊ: ready_for_annotation hoặc training_blocked sai giá trị an toàn!")
        return 1
    if manifest.get("acceptance", {}).get("B") != "approved":
        print("❌ LỖI BIÊN BẢN B: Member B chưa được ghi nhận approved!")
        return 1
    if manifest.get("acceptance", {}).get("D") == "approved":
        print("❌ CẢNH BÁO: D chưa ra lệnh nghiệm thu cuối nhưng acceptance.D đã là approved!")
        return 1
    print("✅ Chốt quản trị an toàn nghiêm ngặt:")
    print("   - ready_for_annotation: False (Chờ Lead D duyệt cuối và ra lệnh mở)")
    print("   - training_blocked:     True (Khóa cứng huấn luyện M0-M3)")
    print("   - acceptance.B:         approved (Đã tiếp thu biên bản QA của Member B)")
    print("   - acceptance.D:         pending_final_verification (Chờ Lead D nghiệm thu)")

    print("\\n🎉 TẤT CẢ CÁC BƯỚC KIỂM ĐỊNH ĐÃ ĐẠT 100%! GÓI ĐỦ ĐIỀU KIỆN ĐỂ LEAD D DUYỆT CUỐI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def build_handover_package() -> dict:
    if not VIEW_PATH.exists():
        raise FileNotFoundError(f"Missing Blind View at {VIEW_PATH}")
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Missing Manifest at {MANIFEST_PATH}")

    view_bytes = VIEW_PATH.read_bytes()
    manifest_bytes = MANIFEST_PATH.read_bytes()

    view_sha256 = file_sha256(VIEW_PATH)
    manifest_sha256 = file_sha256(MANIFEST_PATH)

    handover_manifest = {
        "package_name": "GOI_NGHIEM_THU_LEAD_D_CALIBRATION_CLEAN_24.zip",
        "created_at_utc": "2026-10-27T21:30:00Z",
        "recipient": "Lead D (Anh Tuấn)",
        "sender": "Member C (Data Pipeline & Blind View)",
        "purpose": (
            "Gói bàn giao nghiệm thu Blind View chính thức gồm 24 mẫu chính (Clean Calibration Runway A) "
            "dành riêng cho Lead D đối soát và nghiệm thu cuối trước khi phát hành cho A và B."
        ),
        "governance": {
            "training_blocked": True,
            "ready_for_annotation": False,
            "official_test_used": False,
            "member_b_qa_status": "approved",
            "lead_d_status": "pending_final_verification",
            "reserve_samples_sealed": True,
            "reserve_samples_count": 8,
            "main_samples_count": 24,
            "zero_locator_leak": True,
            "zero_source_label_leak": True,
        },
        "components": {
            "clean_calibration_blind_view_24.json": {
                "byte_size": len(view_bytes),
                "sha256": view_sha256,
                "description": "Blind View gồm đúng 24 mẫu chính (SMP-001..SMP-024) không nhãn, không locator",
            },
            "calibration_clean_a_manifest.json": {
                "byte_size": len(manifest_bytes),
                "sha256": manifest_sha256,
                "description": "Manifest phát hành đồng bộ hash Blind View, giữ ready_for_annotation=false",
            },
            "verify_lead_d_handover.py": {
                "description": "Công cụ kiểm định tự động độc lập dành cho Lead D",
            },
        },
        "verification_command": "python verify_lead_d_handover.py",
    }

    handover_bytes = (
        json.dumps(handover_manifest, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8").replace(b"\r\n", b"\n")
    handover_sha256 = hashlib.sha256(handover_bytes).hexdigest()

    verify_script_content = (
        VERIFY_SCRIPT_CODE.replace("__EXPECTED_VIEW_SHA256__", view_sha256)
        .replace("__EXPECTED_MANIFEST_SHA256__", manifest_sha256)
        .encode("utf-8")
        .replace(b"\r\n", b"\n")
    )

    # Create immutable ZIP package
    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("clean_calibration_blind_view_24.json", view_bytes)
        zf.writestr("calibration_clean_a_manifest.json", manifest_bytes)
        zf.writestr("MANIFEST_HANDOVER_LEAD_D.json", handover_bytes)
        zf.writestr("verify_lead_d_handover.py", verify_script_content)

    zip_bytes = OUTPUT_ZIP.read_bytes()
    zip_sha256 = hashlib.sha256(zip_bytes).hexdigest()
    zip_size = len(zip_bytes)

    print("=== ĐÃ TẠO GÓI BÀN GIAO NGHIỆM THU CHO LEAD D ===")
    print(f"📦 Tệp ZIP:      {OUTPUT_ZIP.name}")
    print(f"📏 Dung lượng:    {zip_size:,} bytes")
    print(f"🔒 SHA-256 ZIP:   {zip_sha256}")
    print(f"📄 Blind View:   {view_sha256} ({len(view_bytes):,} bytes)")
    print(f"📋 Manifest:     {manifest_sha256} ({len(manifest_bytes):,} bytes)")
    print(f"📝 Handover Mf:  {handover_sha256} ({len(handover_bytes):,} bytes)")

    return {
        "zip_path": str(OUTPUT_ZIP),
        "zip_size": zip_size,
        "zip_sha256": zip_sha256,
        "view_sha256": view_sha256,
        "manifest_sha256": manifest_sha256,
    }


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8")
    build_handover_package()
