"""Kịch bản đóng gói MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V3.zip.

Tập hợp đầy đủ các hiện vật cần thiết, tính toán SHA256SUMS.txt và tạo ZIP niêm phong cho Lead D.
"""

import hashlib
import json
from pathlib import Path
import shutil
import zipfile


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def main():
    root = Path(__file__).resolve().parents[2]
    handoff_dir = root / "data" / "restricted" / "main_batch1_lead_d_handoff_v3"
    if handoff_dir.exists():
        shutil.rmtree(handoff_dir)
    handoff_dir.mkdir(parents=True, exist_ok=True)

    # Danh sách các tệp nguồn cần sao chép vào handoff pack
    files_to_copy = {
        "blind_view_a.json": root / "data" / "restricted" / "main_batch1" / "blind_view_a.json",
        "blind_view_b.json": root / "data" / "restricted" / "main_batch1" / "blind_view_b.json",
        "manifest_a.json": root / "data" / "restricted" / "main_batch1" / "manifest_a.json",
        "manifest_b.json": root / "data" / "restricted" / "main_batch1" / "manifest_b.json",
        "release_manifest.json": root / "artifacts" / "main_batch1_release_manifest.json",
        "mapping_restricted.json": root / "data" / "restricted" / "main_batch1" / "mapping_restricted.json",
        "population_1232_sealed.json": root / "data" / "restricted" / "main_batch1" / "population_1232_sealed.json",
        "population_1232_canonical_records_v1.json": root / "data" / "restricted" / "main_batch1" / "population_1232_canonical_records_v1.json",
        "main_annotation_lot_management_ledger.json": root / "data" / "restricted" / "main_annotation_lot_management_ledger.json",
        "seed_salt_specification_restricted.json": root / "data" / "restricted" / "main_batch1" / "seed_salt_specification_restricted.json",
        "provenance_recovery_audit_log.json": root / "data" / "restricted" / "main_batch1" / "provenance_recovery_audit_log.json",
        "INCIDENT_LOG_20261119_MAIN_BATCH1_SALT_EXPOSURE.md": root / "artifacts" / "INCIDENT_LOG_20261119_MAIN_BATCH1_SALT_EXPOSURE.md",
        "exclusion_registry.json": root / "data" / "exclusion_registry.json",
        "pilot_batch1_recovery_dossier_restricted_v4.json": root / "data" / "restricted" / "pilot_batch1_recovery_dossier_restricted_v4.json",
        "clean_calibration_exclusion_mapping_c_32.json": root / "data" / "restricted" / "clean_calibration_exclusion_mapping_c_32.json",
        "verify_population_fingerprint.py": root / "scripts" / "data" / "verify_population_fingerprint.py",
        "verify_provenance_from_parquet.py": root / "scripts" / "data" / "verify_provenance_from_parquet.py",
        "verify_exclusion_audit_standalone.py": root / "scripts" / "data" / "verify_exclusion_audit_standalone.py",
        "test_ledger_migration_proposal.py": root / "tests" / "test_ledger_migration_proposal.py",
    }

    print(f"Sao chép {len(files_to_copy)} tệp vào {handoff_dir}...")
    for target_name, src_path in files_to_copy.items():
        if not src_path.exists():
            raise FileNotFoundError(f"Không tìm thấy tệp: {src_path}")
        dst_path = handoff_dir / target_name
        shutil.copy2(src_path, dst_path)
        print(f"  + {target_name}: {dst_path.stat().st_size} bytes")

    # Tạo SHA256SUMS.txt
    print("\nTạo bảng kiểm kê SHA256SUMS.txt...")
    sums_lines = []
    for item in sorted(handoff_dir.iterdir()):
        if item.is_file() and item.name != "SHA256SUMS.txt":
            sha = compute_sha256(item)
            sums_lines.append(f"{sha}  {item.name}")
            print(f"  {sha}  {item.name} ({item.stat().st_size} bytes)")

    sums_file = handoff_dir / "SHA256SUMS.txt"
    sums_file.write_text("\n".join(sums_lines) + "\n", encoding="utf-8")
    print(f"Đã ghi SHA256SUMS.txt ({len(sums_lines)} mục)")

    # Nén ZIP
    zip_name = "MAIN_BATCH1_RESTRICTED_DATA_PACK_FOR_LEAD_D_V3.zip"
    zip_dest_root = root / zip_name
    zip_dest_restricted = root / "data" / "restricted" / zip_name

    print(f"\nĐóng gói {zip_name}...")
    with zipfile.ZipFile(zip_dest_root, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for item in sorted(handoff_dir.iterdir()):
            if item.is_file():
                zf.write(item, arcname=item.name)

    shutil.copy2(zip_dest_root, zip_dest_restricted)

    zip_size = zip_dest_root.stat().st_size
    zip_sha = compute_sha256(zip_dest_root)
    print("=" * 70)
    print(f"HOÀN TẤT ĐÓNG GÓI GÓI BÀN GIAO V3 THÀNH CÔNG!")
    print(f"File: {zip_name}")
    print(f"Size: {zip_size:,} bytes")
    print(f"SHA-256: {zip_sha}")
    print("=" * 70)


if __name__ == "__main__":
    main()
