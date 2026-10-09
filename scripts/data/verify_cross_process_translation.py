#!/usr/bin/env python3
"""Execute and verify offline translation across independent OS processes.

Strict ARS & Reproducibility Discipline:
- Executes two completely separate Python subprocesses (independent process lifecycle).
- Records process IDs (PIDs), execution start/end timestamps, stdout, and payload hashes.
- Proves inter-process reproducibility (Run 1 PID != Run 2 PID, but SHA-256 matches 100%).
- Exports translation_model_manifest.json and translation_independent_process_receipt.json.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_process(cmd: list[str]) -> dict:
    t_start = datetime.now(timezone.utc)
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        encoding="utf-8",
    )
    stdout, _ = proc.communicate()
    t_end = datetime.now(timezone.utc)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed (exit code {proc.returncode})")

    parsed = {}
    for line in stdout.strip().splitlines():
        if line.strip().startswith("{") and line.strip().endswith("}"):
            try:
                parsed = json.loads(line)
            except Exception:
                pass

    return {
        "command": cmd,
        "pid": parsed.get("pid"),
        "start_utc": t_start.isoformat(),
        "end_utc": t_end.isoformat(),
        "duration_seconds": round((t_end - t_start).total_seconds(), 2),
        "exit_code": proc.returncode,
        "payload_sha256": parsed.get("payload_sha256"),
        "bytes_count": parsed.get("bytes_count"),
        "stdout_summary": stdout.strip(),
    }


def verify_and_record() -> dict:
    experiment_dir = ROOT / "data/raw/recovery/translation_experiment"
    model_dir = ROOT / "models/translation/opus-mt-ja-en"
    experiment_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        p1_out = tmp_path / "proc1_translations.jsonl"
        p2_out = tmp_path / "proc2_translations.jsonl"

        cmd1 = [sys.executable, str(ROOT / "scripts/data/run_offline_translation_experiment.py"), "--single-run-payload", str(p1_out)]
        cmd2 = [sys.executable, str(ROOT / "scripts/data/run_offline_translation_experiment.py"), "--single-run-payload", str(p2_out)]

        print("--- Spawning Process 1 (Independent OS process) ---", flush=True)
        run1 = run_process(cmd1)
        p1_bytes = p1_out.read_bytes()
        p1_sha = digest(p1_bytes)
        print(f"Process 1 completed (PID {run1['pid']}): {p1_sha} ({len(p1_bytes)} bytes)", flush=True)

        print("\n--- Spawning Process 2 (Independent OS process) ---", flush=True)
        run2 = run_process(cmd2)
        p2_bytes = p2_out.read_bytes()
        p2_sha = digest(p2_bytes)
        print(f"Process 2 completed (PID {run2['pid']}): {p2_sha} ({len(p2_bytes)} bytes)", flush=True)

        assert run1["pid"] != run2["pid"], "Processes must have distinct PIDs"
        assert p1_sha == p2_sha, f"Cross-process SHA mismatch! P1: {p1_sha} != P2: {p2_sha}"

        # Copy canonical output
        canonical_out = experiment_dir / "translations_ja_en.jsonl"
        canonical_out.write_bytes(p1_bytes)

    # 1. Export clean translation_model_manifest.json
    raw_model_manifest = json.loads((model_dir / "model_manifest.json").read_text(encoding="utf-8"))
    clean_files = {
        k: v for k, v in sorted(raw_model_manifest["files"].items())
        if not k.startswith(".cache")
    }
    model_export_manifest = {
        "model_repo_id": raw_model_manifest.get("model_repo_id", "Helsinki-NLP/opus-mt-ja-en"),
        "model_pinned_revision": "0770961a39ba6bd66305b149c3f4110bcafca2e6",
        "primary_weight_sha256": raw_model_manifest["primary_weight_sha256"],
        "files_count": len(clean_files),
        "artifacts": clean_files,
    }
    model_manifest_path = experiment_dir / "translation_model_manifest.json"
    model_manifest_path.write_text(json.dumps(model_export_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nExported translation model manifest: {model_manifest_path} (SHA-256: {digest(model_manifest_path.read_bytes())})")

    # 2. Export independent process receipt
    receipt = {
        "status": "independent_processes_reproducibility_verified",
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_repo_id": "Helsinki-NLP/opus-mt-ja-en",
        "model_pinned_revision": "0770961a39ba6bd66305b149c3f4110bcafca2e6",
        "process_1": run1,
        "process_2": run2,
        "inter_process_byte_identical": p1_sha == p2_sha,
        "inter_process_payload_sha256": p1_sha,
        "distinct_pids": [run1["pid"], run2["pid"]],
    }
    receipt_path = experiment_dir / "translation_independent_process_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Exported independent process receipt: {receipt_path} (SHA-256: {digest(receipt_path.read_bytes())})")

    # 3. Update translation_experiment_report.json
    report_path = experiment_dir / "translation_experiment_report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["independent_process_verification"] = {
            "verified": True,
            "receipt_file": str(receipt_path.name),
            "receipt_sha256": digest(receipt_path.read_bytes()),
            "process_1_pid": run1["pid"],
            "process_2_pid": run2["pid"],
            "inter_process_payload_sha256": p1_sha,
        }
        report["model_manifest_file"] = str(model_manifest_path.name)
        report["model_manifest_sha256"] = digest(model_manifest_path.read_bytes())
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Updated translation experiment report: {report_path}")

    return receipt


def main() -> int:
    verify_and_record()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
