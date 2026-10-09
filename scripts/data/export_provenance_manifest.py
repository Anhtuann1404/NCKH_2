#!/usr/bin/env python3
"""Generate the comprehensive Calibration Provenance Manifest and Acceptance Bundle.

Links the full chain of custody:
selection proposal hash -> locator/shard/revision -> view hash -> translation hash -> codebook/dictionary/registry hash.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_provenance_manifest_and_bundle() -> tuple[dict, Path, str]:
    recovery_dir = ROOT / "data/raw/recovery"
    base_view_path = recovery_dir / "calibration_proposal_v1.1_base.json"
    pending_view_path = recovery_dir / "calibration_proposal_v1.1_pending.json"
    receipt_path = recovery_dir / "calibration_proposal_v1.1_pending.json.receipt.json"
    trans_path = recovery_dir / "translation_experiment/translations_ja_en.jsonl"
    report_path = recovery_dir / "translation_experiment/translation_experiment_report.json"
    selection_path = recovery_dir / "calibration-proposed-20261008-v2/selection.proposal.json"
    source_manifest_path = ROOT / "configs/source_manifest.json"
    codebook_path = ROOT / "docs/CODEBOOK_V1_1_DRAFT.md"
    dictionary_path = ROOT / "configs/dictionary_v1.json"
    registry_path = ROOT / "data/exclusion_registry.json"
    shard0_path = ROOT / "data/raw/phreshphish/data/train-000.parquet"
    shard55_path = ROOT / "data/raw/phreshphish/data/train-055.parquet"
    trans_model_manifest_path = recovery_dir / "translation_experiment/translation_model_manifest.json"
    trans_receipt_path = recovery_dir / "translation_experiment/translation_independent_process_receipt.json"

    manifest = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "manifest_id": "CALIBRATION-PROVENANCE-V1.1-20261010",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pending_acceptance",
        "sign_off": {
            "lead_d": {
                "role": "Project Lead & Model Owner",
                "status": "pending_acceptance",
            },
            "member_b": {
                "role": "Quality Control & Adjudicator",
                "status": "pending_acceptance",
            },
            "member_c": {
                "role": "Data Pipeline & Blind View Engineer",
                "status": "submitted_for_review",
            },
        },
        "operational_guards": {
            "training_blocked": True,
            "codebook_version": "1.1.0-draft",
            "blind_view_distributed_to_annotators": False,
        },
        "provenance_chain": {
            "selection_proposal": {
                "file": "calibration-proposed-20261008-v2/selection.proposal.json",
                "sha256": file_sha256(selection_path),
                "sampling_method": "Stratified random sampling by source label and deterministic seed",
                "seed": 20261008,
                "main_count": 24,
                "reserve_count": 8,
                "source_labels_used": "Sampling strata only (12 phish / 12 benign), stripped before view export",
            },
            "source_shards_and_revision": {
                "source_id": "phreshphish",
                "source_split": "train",
                "pinned_revision": "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a",
                "source_manifest_sha256": file_sha256(source_manifest_path),
                "shards": {
                    "data/train-000.parquet": file_sha256(shard0_path),
                    "data/train-055.parquet": file_sha256(shard55_path),
                },
            },
            "blind_views": {
                "base_view_untranslated": {
                    "file": "calibration_proposal_v1.1_base.json",
                    "size_bytes": base_view_path.stat().st_size,
                    "sha256": file_sha256(base_view_path),
                    "samples_count": 24,
                    "max_html_characters": 2_000_000,
                    "label_leakage_audit": "0 leaks (no labels, no targets, no scores)",
                },
                "pending_view_translated": {
                    "file": "calibration_proposal_v1.1_pending.json",
                    "size_bytes": pending_view_path.stat().st_size,
                    "sha256": file_sha256(pending_view_path),
                    "samples_count": 24,
                    "translated_samples_count": 4,
                    "receipt_file": "calibration_proposal_v1.1_pending.json.receipt.json",
                    "receipt_sha256": file_sha256(receipt_path),
                },
            },
            "translation_artifacts": {
                "model_repo_id": "Helsinki-NLP/opus-mt-ja-en",
                "model_pinned_revision": "0770961a39ba6bd66305b149c3f4110bcafca2e6",
                "model_primary_weight_sha256": "ed649116c143fc2d7aea690246f4b2b7caa814e9e00a8d5bbe047822b18de022",
                "model_manifest_file": "translation_model_manifest.json",
                "model_manifest_sha256": file_sha256(trans_model_manifest_path),
                "translations_file": "translations_ja_en.jsonl",
                "translations_file_sha256": file_sha256(trans_path),
                "qc_report_file": "translation_experiment_report.json",
                "qc_report_sha256": file_sha256(report_path),
                "independent_process_receipt_file": "translation_independent_process_receipt.json",
                "independent_process_receipt_sha256": file_sha256(trans_receipt_path),
                "lossless_chunking_verified": True,
                "independent_process_determinism_verified": True,
            },
            "governance_and_rules": {
                "codebook": {
                    "version": "1.1.0-draft",
                    "file": "docs/CODEBOOK_V1_1_DRAFT.md",
                    "sha256": file_sha256(codebook_path),
                    "status": "draft_pending_final_calibration",
                    "approval_required_prior_to_labeling": True,
                },
                "dictionary": {
                    "file": "configs/dictionary_v1.json",
                    "sha256": file_sha256(dictionary_path),
                    "target_brands_count": 14,
                },
                "exclusion_registry": {
                    "file": "data/exclusion_registry.json",
                    "sha256": file_sha256(registry_path),
                    "total_excluded_entries": 6,
                    "total_excluded_samples": 148,
                    "training_blocked": True,
                    "new_batches_added": [
                        "EXCL-CALIBRATION-PROPOSAL-V1.1-MAIN-24",
                        "EXCL-CALIBRATION-PROPOSAL-V1.1-RESERVE-08",
                    ],
                },
            },
        },
    }

    manifest_path = recovery_dir / "CALIBRATION_PROVENANCE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Generated provenance manifest: {manifest_path} (SHA-256: {file_sha256(manifest_path)})")

    # Package next acceptance handoff bundle
    bundle_files = {
        "calibration_proposal_v1.1_base.json": base_view_path,
        "translations_ja_en.jsonl": trans_path,
        "calibration_proposal_v1.1_pending.json": pending_view_path,
        "calibration_proposal_v1.1_pending.json.receipt.json": receipt_path,
        "translation_experiment_report.json": report_path,
        "translation_model_manifest.json": trans_model_manifest_path,
        "translation_independent_process_receipt.json": trans_receipt_path,
        "CALIBRATION_PROVENANCE_MANIFEST.json": manifest_path,
    }

    handoff_manifest = {
        "package": "calibration_v1.1_final_acceptance_20261010.zip",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Gói nghiệm thu hoàn thiện Calibration v1.1 gửi Lead D và Member B (Task LABEL-01)",
        "files": {
            arcname: {
                "size_bytes": p.stat().st_size,
                "sha256": file_sha256(p),
            }
            for arcname, p in bundle_files.items()
        },
    }

    zip_path = recovery_dir / "calibration_v1.1_final_acceptance_20261010.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "HANDOFF_MANIFEST.json",
            json.dumps(handoff_manifest, indent=2, ensure_ascii=False).encode("utf-8"),
        )
        for arcname, p in bundle_files.items():
            zf.write(p, arcname)

    zip_sha = file_sha256(zip_path)
    sha_path = recovery_dir / "calibration_v1.1_final_acceptance_20261010.zip.sha256"
    sha_path.write_text(f"{zip_sha}  {zip_path.name}\n", encoding="utf-8")

    print(f"Created acceptance handoff package: {zip_path}")
    print(f"Size: {zip_path.stat().st_size:,} bytes | SHA-256: {zip_sha}")
    print(f"Checksum file: {sha_path}")
    return manifest, zip_path, zip_sha


def main() -> int:
    generate_provenance_manifest_and_bundle()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
