import hashlib
import json
import zipfile
from pathlib import Path


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    root = Path.cwd()
    files_to_pack = [
        "src/phishing/annotation/__init__.py",
        "src/phishing/annotation/timer.py",
        "src/phishing/annotation/blind_view.py",
        "scripts/annotate_cli.py",
        "tests/test_annotate_cli_timer_pause.py",
        "DIFF_TASK_CLI_TIMER_PAUSE_CUMULATIVE.patch",
        "DIFF_DELTA_FROM_2246CB6.patch",
    ]

    file_meta = {}
    for rel in files_to_pack:
        p = root / rel
        file_meta[rel] = {
            "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        }

    manifest = {
        "task_id": "TASK-CLI-TIMER-PAUSE",
        "head_commit": "fefb89e",
        "base_commit": "9789fc0",
        "previous_commit": "2246cb6",
        "branch": "feat/c-calibration-v1-1-4-adjudication",
        "ready_for_annotation": False,
        "training_blocked": True,
        "included_files": file_meta,
        "test_summary": {
            "timer_unit_integration_regression_tests": "13/13 passed",
            "calibration_release_guards_and_selection_tests": "33/33 passed (23 guards + 10 selection)",
            "full_non_integration_suite": "297/297 passed (19 deselected, 0 failed)",
        },
        "contract_rules_v1_1": {
            "pause_count": "Strictly int, non-negative, reject bool, reject float (1.9), mandatory in v1.1",
            "paused_seconds": "Strictly float/int, non-negative, finite (reject NaN, Inf, -Inf), reject bool, mandatory in v1.1",
            "seconds_spent": "Strictly float/int, non-negative, finite (reject NaN, Inf, -Inf), reject bool",
        },
    }

    manifest_path = root / "MANIFEST_TASK_CLI_TIMER_PAUSE.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest_meta = {
        "size_bytes": manifest_path.stat().st_size,
        "sha256": sha256_file(manifest_path),
    }

    zip_name = "TASK_CLI_TIMER_PAUSE_HANDOVER.zip"
    zip_path = root / zip_name
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in files_to_pack:
            zf.write(root / rel, arcname=rel)
        zf.write(manifest_path, arcname="MANIFEST_TASK_CLI_TIMER_PAUSE.json")

    zip_hash = sha256_file(zip_path)
    zip_size = zip_path.stat().st_size

    print(f"ZIP_NAME: {zip_name}")
    print(f"ZIP_SIZE: {zip_size} bytes")
    print(f"ZIP_SHA256: {zip_hash}")
    print("\nFILES:")
    for rel in files_to_pack:
        print(f"  {rel}: {file_meta[rel]['sha256']} ({file_meta[rel]['size_bytes']} bytes)")
    print(f"  MANIFEST_TASK_CLI_TIMER_PAUSE.json: {manifest_meta['sha256']} ({manifest_meta['size_bytes']} bytes)")


if __name__ == "__main__":
    main()
