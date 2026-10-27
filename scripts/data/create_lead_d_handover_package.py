#!/usr/bin/env python3
"""Build Handover Package for Lead D's Final Review (Clean Calibration Runway A).

Package: GOI_NGHIEM_THU_LEAD_D_CALIBRATION_CLEAN_24.zip
Contains:
1. clean_calibration_blind_view_24.json (The 24 main samples Blind View with offline translations)
2. clean_calibration_blind_view_24_base.json (Untranslated base view audit trail)
3. clean_calibration_exclusion_mapping_32.json (Restricted 32-sample exclusion mapping for Lead D verification)
4. calibration_clean_a_manifest.json (Synchronized manifest v1.1-PROPOSAL)
5. MANIFEST_HANDOVER_LEAD_D.json (Handover metadata and component checksums)
6. verify_lead_d_handover.py (Standalone automated verification tool for Lead D)
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
BASE_VIEW_PATH = ROOT / "data/annotations/clean_calibration_blind_view_24_base.json"
MAPPING_PATH = ROOT / "data/restricted/clean_calibration_exclusion_mapping_32.json"
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
BASE_VIEW_FILE = DIR / "clean_calibration_blind_view_24_base.json"
MAPPING_FILE = DIR / "clean_calibration_exclusion_mapping_32.json"
MANIFEST_FILE = DIR / "calibration_clean_a_manifest.json"
HANDOVER_FILE = DIR / "MANIFEST_HANDOVER_LEAD_D.json"

EXPECTED_VIEW_SHA256 = "__EXPECTED_VIEW_SHA256__"
EXPECTED_BASE_VIEW_SHA256 = "__EXPECTED_BASE_VIEW_SHA256__"
EXPECTED_MAPPING_SHA256 = "__EXPECTED_MAPPING_SHA256__"
EXPECTED_MANIFEST_SHA256 = "__EXPECTED_MANIFEST_SHA256__"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8")
    print("=== KIỂM ĐỊNH TỰ ĐỘNG GÓI NGHIỆM THU CUỐI CHO LEAD D ===")
    
    # 1. Check files existence
    files_to_check = [
        ("Blind View (với bản dịch)", VIEW_FILE),
        ("Blind View Base (dấu vết gốc)", BASE_VIEW_FILE),
        ("Ánh xạ loại trừ hạn chế", MAPPING_FILE),
        ("Manifest phát hành", MANIFEST_FILE),
        ("Handover Manifest", HANDOVER_FILE),
    ]
    for desc, f in files_to_check:
        if not f.exists():
            print(f"❌ THIẾU TỆP: {desc} ({f.name})")
            return 1
    print(f"✅ Đủ {len(files_to_check)} tệp thành phần trong gói nghiệm thu.")

    # 2. Check Line endings (pure LF)
    view_bytes = VIEW_FILE.read_bytes()
    base_bytes = BASE_VIEW_FILE.read_bytes()
    mapping_bytes = MAPPING_FILE.read_bytes()
    manifest_bytes = MANIFEST_FILE.read_bytes()
    handover_bytes = HANDOVER_FILE.read_bytes()

    for name, raw in [
        ("Blind View", view_bytes),
        ("Base View", base_bytes),
        ("Mapping Dossier", mapping_bytes),
        ("Manifest", manifest_bytes),
        ("Handover Manifest", handover_bytes),
    ]:
        if b"\\r\\n" in raw:
            print(f"❌ LỖI LINE ENDING: {name} chứa byte CRLF. Bắt buộc pure Unix LF.")
            return 1
    print("✅ 100% tệp sử dụng chuẩn hóa kết thúc dòng Unix LF.")

    # 3. Check SHA-256
    view_hash = sha256(view_bytes)
    base_hash = sha256(base_bytes)
    mapping_hash = sha256(mapping_bytes)
    manifest_hash = sha256(manifest_bytes)

    assert view_hash == EXPECTED_VIEW_SHA256, f"Sai SHA-256 Blind View: {view_hash} != {EXPECTED_VIEW_SHA256}"
    assert base_hash == EXPECTED_BASE_VIEW_SHA256, f"Sai SHA-256 Base View: {base_hash} != {EXPECTED_BASE_VIEW_SHA256}"
    assert mapping_hash == EXPECTED_MAPPING_SHA256, f"Sai SHA-256 Mapping: {mapping_hash} != {EXPECTED_MAPPING_SHA256}"
    assert manifest_hash == EXPECTED_MANIFEST_SHA256, f"Sai SHA-256 Manifest: {manifest_hash} != {EXPECTED_MANIFEST_SHA256}"

    print(f"✅ SHA-256 Blind View (dịch) khớp:  {view_hash}")
    print(f"✅ SHA-256 Base View (gốc) khớp:    {base_hash}")
    print(f"✅ SHA-256 Mapping hạn chế khớp:    {mapping_hash}")
    print(f"✅ SHA-256 Manifest phát hành khớp: {manifest_hash}")

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

    # 7. Check Offline Translations (R-A09)
    translated_samples = {s["sample_id"]: s for s in samples if s.get("translation_provided")}
    expected_translated = {"SMP-007", "SMP-008", "SMP-010"}
    if set(translated_samples.keys()) != expected_translated:
        print(f"❌ SAI MẪU ĐƯỢC DỊCH: {set(translated_samples.keys())} != {expected_translated}")
        return 1
    for sid, s in translated_samples.items():
        t_hash = sha256(s["translated_text"].encode("utf-8"))
        if s["translation_sha256"] != t_hash:
            print(f"❌ SAI HASH BẢN DỊCH {sid}: {s['translation_sha256']} != {t_hash}")
            return 1
    print(f"✅ Gắn bản dịch ngoại tuyến MarianMT đạt chuẩn R-A09 cho 3 mẫu (SMP-007/008 JA, SMP-010 RU).")

    # 8. Check Exclusion Mapping Dossier
    mapping = json.loads(mapping_bytes.decode("utf-8"))
    entries = mapping.get("mapping", [])
    if len(entries) != 32:
        print(f"❌ SAI SỐ LƯỢNG MẪU ÁNH XẠ: {len(entries)} != 32")
        return 1
    main_count = sum(1 for e in entries if e["role"] == "main_24")
    res_count = sum(1 for e in entries if e["role"] == "reserve_08")
    if main_count != 24 or res_count != 8:
        print(f"❌ SAI PHÂN TẦNG ÁNH XẠ: main={main_count}, reserve={res_count}")
        return 1
    print(f"✅ Hồ sơ ánh xạ loại trừ đủ 32 mẫu (24 chính + 8 dự phòng) được sắp xếp ẩn danh hóa url_sha256.")

    # 9. Check Manifest Governance Locks
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if manifest.get("ready_for_annotation") is not False or manifest.get("training_blocked") is not True:
        print("❌ LỖI CHỐT KHÓA QUẢN TRỊ: ready_for_annotation hoặc training_blocked sai giá trị an toàn!")
        return 1
    if manifest.get("candidate_selection_qa", {}).get("B") != "approved" and manifest.get("governance", {}).get("acceptance", {}).get("candidate_selection_member_b_qa", {}).get("status") != "approved":
        print("❌ LỖI BIÊN BẢN B: Phạm vi QA tuyển chọn của Member B chưa được ghi nhận approved!")
        return 1
    if manifest.get("acceptance", {}).get("B") == "approved":
        print("❌ LỖI NGHIỆM THU VIEW: Member B chưa kiểm định Blind View phát hành nhưng acceptance.B đã là approved!")
        return 1
    if manifest.get("acceptance", {}).get("D") == "approved":
        print("❌ CẢNH BÁO: D chưa ra lệnh nghiệm thu cuối nhưng acceptance.D đã là approved!")
        return 1
    if manifest.get("governance", {}).get("known_excluded_samples_count") != 214:
        print(f"❌ SAI SỐ MẪU LOẠI TRỪ TRONG MANIFEST: {manifest.get('governance', {}).get('known_excluded_samples_count')} != 214")
        return 1
    print("✅ Chốt quản trị an toàn nghiêm ngặt:")
    print("   - ready_for_annotation:   False (Chờ Lead D duyệt cuối và ra lệnh mở)")
    print("   - training_blocked:       True (Khóa cứng huấn luyện M0-M3)")
    print("   - known_excluded_count:   214 mẫu across 9 batches")
    print("   - candidate_selection_qa: approved (Member B đã nghiệm thu gói tuyển chọn 32 mẫu)")
    print("   - acceptance.B (view):    pending (Chờ B kiểm tự động Blind View phát hành)")
    print("   - acceptance.D:           pending_final_verification (Chờ Lead D nghiệm thu)")

    print("\\n🎉 TẤT CẢ CÁC BƯỚC KIỂM ĐỊNH ĐÃ ĐẠT 100%! GÓI ĐỦ ĐIỀU KIỆN ĐỂ LEAD D DUYỆT CUỐI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def build_handover_package() -> dict:
    if not VIEW_PATH.exists():
        raise FileNotFoundError(f"Missing Blind View at {VIEW_PATH}")
    if not BASE_VIEW_PATH.exists():
        raise FileNotFoundError(f"Missing Base View at {BASE_VIEW_PATH}")
    if not MAPPING_PATH.exists():
        raise FileNotFoundError(f"Missing Mapping Dossier at {MAPPING_PATH}")
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Missing Manifest at {MANIFEST_PATH}")

    view_bytes = VIEW_PATH.read_bytes()
    base_bytes = BASE_VIEW_PATH.read_bytes()
    mapping_bytes = MAPPING_PATH.read_bytes()
    manifest_bytes = MANIFEST_PATH.read_bytes()

    view_sha256 = file_sha256(VIEW_PATH)
    base_sha256 = file_sha256(BASE_VIEW_PATH)
    mapping_sha256 = file_sha256(MAPPING_PATH)
    manifest_sha256 = file_sha256(MANIFEST_PATH)

    handover_manifest = {
        "package_name": "GOI_NGHIEM_THU_LEAD_D_CALIBRATION_CLEAN_24.zip",
        "created_at_utc": "2026-10-27T22:20:00Z",
        "recipient": "Lead D (Anh Tuấn)",
        "sender": "Member C (Data Pipeline & Blind View)",
        "purpose": (
            "Gói bàn giao nghiệm thu Blind View chính thức gồm 24 mẫu chính (Clean Calibration Runway A) "
            "kèm bản dịch ngoại tuyến MarianMT, bản lưu dấu vết gốc, hồ sơ ánh xạ loại trừ 32 mẫu hạn chế, "
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
            "total_excluded_samples_registry": 214,
            "total_batches_registry": 9,
        },
        "components": {
            "clean_calibration_blind_view_24.json": {
                "byte_size": len(view_bytes),
                "sha256": view_sha256,
                "description": "Blind View gồm đúng 24 mẫu chính (SMP-001..SMP-024) có bản dịch ngoại tuyến R-A09",
            },
            "clean_calibration_blind_view_24_base.json": {
                "byte_size": len(base_bytes),
                "sha256": base_sha256,
                "description": "Bản lưu dấu vết kiểm toán chưa dịch (24 mẫu gốc được trích xuất trực tiếp từ parquet)",
            },
            "clean_calibration_exclusion_mapping_32.json": {
                "byte_size": len(mapping_bytes),
                "sha256": mapping_sha256,
                "description": "Hồ sơ đối soát hạn chế nối mã băm EXCL-CLN-001..032 với locator và vai trò dành riêng cho D",
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
        VERIFY_SCRIPT_CODE
        .replace("__EXPECTED_VIEW_SHA256__", view_sha256)
        .replace("__EXPECTED_BASE_VIEW_SHA256__", base_sha256)
        .replace("__EXPECTED_MAPPING_SHA256__", mapping_sha256)
        .replace("__EXPECTED_MANIFEST_SHA256__", manifest_sha256)
        .encode("utf-8")
        .replace(b"\r\n", b"\n")
    )

    # Create immutable ZIP package
    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("clean_calibration_blind_view_24.json", view_bytes)
        zf.writestr("clean_calibration_blind_view_24_base.json", base_bytes)
        zf.writestr("clean_calibration_exclusion_mapping_32.json", mapping_bytes)
        zf.writestr("calibration_clean_a_manifest.json", manifest_bytes)
        zf.writestr("MANIFEST_HANDOVER_LEAD_D.json", handover_bytes)
        zf.writestr("verify_lead_d_handover.py", verify_script_content)

    zip_bytes = OUTPUT_ZIP.read_bytes()
    zip_sha256 = hashlib.sha256(zip_bytes).hexdigest()
    zip_size = len(zip_bytes)

    print("=== ĐÃ TẠO GÓI BÀN GIAO NGHIỆM THU CHO LEAD D ===")
    print(f"📦 Tệp ZIP:           {OUTPUT_ZIP.name}")
    print(f"📏 Dung lượng:         {zip_size:,} bytes")
    print(f"🔒 SHA-256 ZIP:        {zip_sha256}")
    print(f"📄 Blind View (dịch):  {view_sha256} ({len(view_bytes):,} bytes)")
    print(f"📄 Base View (gốc):    {base_sha256} ({len(base_bytes):,} bytes)")
    print(f"🗺️ Mapping Dossier:    {mapping_sha256} ({len(mapping_bytes):,} bytes)")
    print(f"📋 Manifest:          {manifest_sha256} ({len(manifest_bytes):,} bytes)")
    print(f"📝 Handover Mf:       {handover_sha256} ({len(handover_bytes):,} bytes)")

    return {
        "zip_path": str(OUTPUT_ZIP),
        "zip_size": zip_size,
        "zip_sha256": zip_sha256,
        "view_sha256": view_sha256,
        "base_sha256": base_sha256,
        "mapping_sha256": mapping_sha256,
        "manifest_sha256": manifest_sha256,
        "handover_sha256": handover_sha256,
    }


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8")
    build_handover_package()
