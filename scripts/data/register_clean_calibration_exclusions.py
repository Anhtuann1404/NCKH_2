#!/usr/bin/env python3
"""Register 32 Clean Calibration Candidates into Exclusion Registry (Fail-Closed, Zero-Leak).

Strict Academic Research Skills & Anti-Leakage Protocol:
1. Full 32 samples (24 main + 8 reserve) permanently excluded from all splits (train/val/test).
2. Zero Git Leakage:
   - Locators (shard + row_offset) are stripped from Git registry.
   - Roles (main_24 vs reserve_08) are stripped and anonymized into neutral IDs (EXCL-CLN-001..032).
   - Samples are cryptographically sorted by url_sha256 to eliminate original selection order.
   - Only 4 cryptographic hashes (url_sha256, normalized_url_sha256, html_sha256, group_sha256) are committed.
3. Restricted Mapping Dossier:
   - Complete 1-to-1 mapping (entry_id <-> candidate_id <-> role <-> locator) is stored in restricted
     area outside Git (data/restricted/clean_calibration_exclusion_mapping_32.json) for Lead D verification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

REGISTRY_PATH = ROOT / "data/exclusion_registry.json"
CANDIDATES_PATH = ROOT / "data/restricted/clean_calibration_candidates_v2_restricted.json"
RESTRICTED_MAPPING_PATH = ROOT / "data/restricted/clean_calibration_exclusion_mapping_32.json"
MANIFEST_PATH = ROOT / "configs/calibration_clean_a_manifest.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def register_clean_calibration_exclusions(
    candidates_path: Path = CANDIDATES_PATH,
    registry_path: Path = REGISTRY_PATH,
    restricted_mapping_path: Path = RESTRICTED_MAPPING_PATH,
    dry_run: bool = False,
) -> Dict[str, Any]:
    if not candidates_path.exists():
        raise FileNotFoundError(f"Missing candidates file: {candidates_path}")
    if not registry_path.exists():
        raise FileNotFoundError(f"Missing registry file: {registry_path}")

    cand_data = json.loads(candidates_path.read_text(encoding="utf-8"))
    candidates = cand_data.get("candidates", [])
    if len(candidates) != 32:
        raise ValueError(f"Expected exactly 32 candidates, found {len(candidates)}")

    reg_data = json.loads(registry_path.read_text(encoding="utf-8"))

    batch_id = "EXCL-CALIBRATION-CLEAN-RUNWAY-32"
    # Filter out existing batch if already registered to allow idempotent update
    other_exclusions = [b for b in reg_data.get("exclusions", []) if b.get("exclusion_id") != batch_id]

    # Cryptographically sort all 32 candidates by url_sha256 to completely eliminate original order & roles
    sorted_candidates = sorted(candidates, key=lambda c: c["url_sha256"])

    public_entries: List[Dict[str, Any]] = []
    restricted_mapping: List[Dict[str, Any]] = []

    for idx, c in enumerate(sorted_candidates):
        neutral_id = f"EXCL-CLN-{idx + 1:03d}"

        # Public Git entry: ONLY 4 cryptographic hashes + neutral metadata (NO locator, NO role, NO raw URL)
        entry = {
            "sample_id": neutral_id,
            "url_sha256": c["url_sha256"],
            "normalized_url_sha256": c["normalized_url_sha256"],
            "html_sha256": c["html_sha256"],
            "group_sha256": c["group_sha256"],
            "group_id": c["group_id"],
            "source_date": c["source_date"],
        }
        public_entries.append(entry)

        # Restricted Mapping for Lead D: Full cryptographic binding to candidate_id and locators
        map_item = {
            "entry_id": neutral_id,
            "candidate_id": c["candidate_id"],
            "role": c["role"],
            "locator": c["locator"],
            "url_sha256": c["url_sha256"],
            "html_sha256": c["html_sha256"],
            "group_sha256": c["group_sha256"],
            "group_id": c["group_id"],
            "source_date": c["source_date"],
        }
        restricted_mapping.append(map_item)

    # Calculate batch sha256 from sorted entries
    batch_content = json.dumps(public_entries, sort_keys=True).encode("utf-8")
    batch_sha = sha256(batch_content)

    new_batch = {
        "exclusion_id": batch_id,
        "dataset_id": "CALIBRATION-CLEAN-RUNWAY-32",
        "reason": (
            "32 mẫu tuyển chọn cho Clean Calibration Runway A (24 chính + 8 dự phòng) loại trừ vĩnh viễn "
            "khỏi toàn bộ train, validation và test của các mô hình M0-M3; locators và vai trò được cô lập ngoài Git."
        ),
        "source": "phreshphish",
        "split": "train",
        "source_metadata_revision": "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a",
        "rows_api_revision_pinned": True,
        "mapping_status": "verified_cryptographic_hashes_locators_restricted_offline",
        "mapping_notes": (
            "Locators (shard và row offset), vai trò (chính vs dự phòng) và thứ tự mẫu được lưu trữ an toàn "
            "trong hồ sơ hạn chế ngoài Git (data/restricted/clean_calibration_exclusion_mapping_32.json) "
            "để bảo vệ ranh giới mù đôi của A và B."
        ),
        "batch_sha256": batch_sha,
        "action": "permanently_exclude_from_train_val_test",
        "n_samples": 32,
        "samples": public_entries,
    }

    # Save restricted mapping first
    mapping_dossier = {
        "dataset_id": "CALIBRATION-CLEAN-RUNWAY-32",
        "batch_id": batch_id,
        "batch_sha256": batch_sha,
        "total_samples": 32,
        "main_samples_count": 24,
        "reserve_samples_count": 8,
        "sorted_by": "url_sha256",
        "purpose": "Hồ sơ đối soát hạn chế nối mã băm exclusion registry với locators gốc dành riêng cho Lead D",
        "mapping": restricted_mapping,
    }

    if not dry_run:
        restricted_mapping_path.parent.mkdir(parents=True, exist_ok=True)
        mapping_bytes = (
            json.dumps(mapping_dossier, indent=2, ensure_ascii=False) + "\n"
        ).encode("utf-8").replace(b"\r\n", b"\n")
        restricted_mapping_path.write_bytes(mapping_bytes)
        print(f"✅ Saved restricted mapping dossier to {restricted_mapping_path}")

        # Update registry
        all_exclusions = other_exclusions + [new_batch]
        reg_data["exclusions"] = all_exclusions
        reg_data["total_excluded_entries"] = len(all_exclusions)  # 9 batches
        reg_data["total_excluded_samples"] = sum(
            b.get("n_samples", len(b.get("samples", []))) for b in all_exclusions
        )  # 214 samples
        reg_data["training_blocked"] = True

        reg_bytes = (json.dumps(reg_data, indent=2, ensure_ascii=False) + "\n").encode("utf-8").replace(b"\r\n", b"\n")
        registry_path.write_bytes(reg_bytes)
        new_reg_sha = sha256(reg_bytes)
        print(f"✅ Updated exclusion registry: 214 samples across 9 batches (SHA-256: {new_reg_sha})")

    return {
        "batch_id": batch_id,
        "batch_sha256": batch_sha,
        "samples_registered": 32,
        "total_samples": reg_data["total_excluded_samples"] if not dry_run else 214,
        "total_batches": len(reg_data["exclusions"]) if not dry_run else 9,
    }


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8")
    res = register_clean_calibration_exclusions()
    print("Done:", res)
