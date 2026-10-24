import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def create_restricted_package():
    zip_name = "GOI_RA_SOAT_HAN_CHE_CALIBRATION_CLEAN_32_V2.zip"
    zip_path = ROOT / zip_name

    # Danh sách các tệp đưa vào gói rà soát hạn chế
    files_map = {
        "candidates_restricted.json": ROOT / "data/restricted/clean_calibration_candidates_v2_restricted.json",
        "clean_calibration_selection_inspection_report.json": ROOT / "data/source_audit/clean_calibration_selection_inspection_report.json",
        "clean_calibration_exclusion_audit_report.json": ROOT / "data/source_audit/clean_calibration_exclusion_audit_report.json",
        "clean_calibration_git_leak_audit.json": ROOT / "data/source_audit/clean_calibration_git_leak_audit.json",
        "calibration_clean_a_manifest.json": ROOT / "configs/calibration_clean_a_manifest.json",
    }

    manifest_entries = {}
    for arc_name, p in files_map.items():
        assert p.exists(), f"Thiếu tệp: {p}"
        manifest_entries[arc_name] = {
            "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p),
            "source_repo_path": str(p.relative_to(ROOT)),
        }

    pkg_manifest = {
        "package_id": "PKG-RESTRICTED-CALIBRATION-CLEAN-32-V2",
        "created_at_utc": "2026-10-24T01:05:00Z",
        "purpose": "Gói rà soát hạn chế ngoài Git dành riêng cho Lead D (kiểm tra nguồn raw) và Member B (kiểm định kỹ thuật mù) trước khi mở Pass 1",
        "governance": {
            "ready_for_annotation": False,
            "training_blocked": True,
            "blind_view_released_to_ab": False,
            "status": "pending_lead_d_and_member_b_review",
        },
        "contents": manifest_entries,
    }

    manifest_bytes = (json.dumps(pkg_manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for arc_name, p in files_map.items():
            zf.write(p, arcname=arc_name)
        zf.writestr("MANIFEST_RESTRICTED.json", manifest_bytes)

    zip_hash = sha256_file(zip_path)
    zip_size = zip_path.stat().st_size

    print(f"ZIP_NAME: {zip_name}")
    print(f"ZIP_SIZE: {zip_size} bytes")
    print(f"ZIP_SHA256: {zip_hash}")
    print("\nFILES IN PACKAGE:")
    for arc_name, meta in manifest_entries.items():
        print(f"  {arc_name}: {meta['sha256']} ({meta['size_bytes']} bytes)")


if __name__ == "__main__":
    create_restricted_package()
