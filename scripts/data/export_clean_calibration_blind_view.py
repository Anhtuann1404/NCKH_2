#!/usr/bin/env python3
"""Export Clean Calibration Blind View v1.1 (24 Main Samples only).

Strictly adheres to:
1. Zero Data Peeking & Anti-Leakage Protocol (ARS):
   - Only 24 main samples (SMP-001..SMP-024) are included.
   - 8 reserve samples (RSV-001..RSV-008) remain strictly confidential in restricted storage.
   - 100% free of labels, targets, model scores, or candidate source locators.
2. Ponytail Engineering Discipline:
   - Minimal code diff, pure standard library + pyarrow + existing phishing modules.
   - Pure LF byte serialization matching cryptographic hashes.
3. Preflight & Governance compatibility:
   - Integrates with configs/calibration_clean_a_manifest.json.
   - Maintains ready_for_annotation=false and training_blocked=true until Lead D sign-off.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from phishing.annotation.blind_view import (
    assert_no_label_leak,
    create_blind_sample,
    extract_safe_view_content,
)


def compute_sha256(data: bytes) -> str:
    """Compute hex SHA-256 digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def export_clean_blind_view(
    candidates_path: Path,
    source_root: Path,
    output_path: Path,
    manifest_path: Path | None = None,
    update_manifest: bool = False,
) -> Tuple[Dict[str, Any], bytes, str]:
    """Extract and export 24 main samples as a clean Blind View."""
    if not candidates_path.exists():
        raise FileNotFoundError(f"Missing candidates restricted file: {candidates_path}")

    cand_data = json.loads(candidates_path.read_text(encoding="utf-8"))
    candidates = cand_data.get("candidates", [])

    # Filter strictly main_24 candidates
    main_cands = [c for c in candidates if c.get("role") == "main_24"]
    if len(main_cands) != 24:
        raise ValueError(
            f"Expected exactly 24 main candidates, got {len(main_cands)}"
        )

    # Ensure no reserve candidate leaked into main
    for c in main_cands:
        if c.get("candidate_id", "").startswith("RSV"):
            raise ValueError(
                f"Reserve candidate {c['candidate_id']} detected in main candidates pool!"
            )

    # Load source parquet shards
    shards_cache: Dict[str, Any] = {}
    for c in main_cands:
        rel_path = c["locator"]["relative_path"]
        if rel_path not in shards_cache:
            shard_file = source_root / Path(rel_path).name
            if not shard_file.exists():
                raise FileNotFoundError(f"Missing parquet source shard: {shard_file}")
            shards_cache[rel_path] = pq.read_table(shard_file)

    clean_samples: List[Dict[str, Any]] = []
    for c in main_cands:
        cid = c["candidate_id"]
        loc = c["locator"]
        rel_path = loc["relative_path"]
        offset = loc["row_offset"]

        table = shards_cache[rel_path]
        row = table.slice(offset, 1).to_pylist()[0]
        url = row["url"]
        html_raw = row.get("html") or ""

        # Verify content checksums match candidate record
        url_hash = compute_sha256(url.encode("utf-8"))
        html_hash = compute_sha256(html_raw.encode("utf-8"))
        if url_hash != c["url_sha256"]:
            raise ValueError(f"{cid}: URL hash mismatch with source parquet!")
        if html_hash != c["html_sha256"]:
            raise ValueError(f"{cid}: HTML hash mismatch with source parquet!")

        # Safe view extraction with 2M characters limit
        page_text, summary = extract_safe_view_content(
            html_raw, url, max_html_characters=2_000_000
        )

        blind = create_blind_sample(
            {
                "sample_id": cid,
                "url": url,
                "page_text": page_text,
                "structure_summary": summary,
                "random_subset": True,
                "translation_provided": False,
            },
            codebook_version="1.1.0",
        )
        s_dict = blind.to_dict()
        assert_no_label_leak(s_dict)

        # Defense-in-depth: Ensure no source locator metadata exists in sample
        for forbidden in ("locator", "relative_path", "row_offset", "source_shard", "train-000", "train-055"):
            if forbidden in s_dict:
                raise ValueError(f"Forbidden locator key '{forbidden}' found in sample {cid}")

        clean_samples.append(s_dict)

    # Build top-level Blind View dictionary
    view = {
        "dataset_id": "CALIBRATION-CLEAN-24",
        "dataset_type": "blind_view",
        "version": "1.1.0",
        "status": "ready_for_review_not_yet_released",
        "description": (
            "Gói Blind View gồm đúng 24 mẫu chính đợt Clean Calibration Runway A phục vụ "
            "gán nhãn mù độc lập song song A-B (8 mẫu dự phòng được giữ kín trong hồ sơ hạn chế)."
        ),
        "sample_count": 24,
        "total_samples": 24,
        "sampling_plan_version": "CALIBRATION-CLEAN-PLAN-V1.1-STRATIFIED",
        "codebook_version": "1.1.0",
        "codebook_sha256": "e30871b87911992110e77ad0dcca8bbf64b916086f496555599e43730af0adbd",
        "dictionary_version": "1.0.0",
        "dictionary_sha256": "7aa83b68fdb4bb288460c00523e38e0779e8cbeb81ae879e7a5d27e771fcd3b3",
        "is_synthetic": False,
        "samples": clean_samples,
    }

    # Final zero-leak assert
    assert_no_label_leak(view)

    # Encode with strict Unix LF line endings
    payload = (json.dumps(view, indent=2, ensure_ascii=False) + "\n").encode("utf-8").replace(b"\r\n", b"\n")
    view_hash = compute_sha256(payload)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)

    # Update manifest if requested
    if update_manifest and manifest_path and manifest_path.exists():
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))

        rel_view_path = str(output_path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")

        # Top-level alignment for CLI and tool contracts
        manifest_data["dataset_id"] = "CALIBRATION-CLEAN-24"
        manifest_data["sample_count"] = 24
        manifest_data["sampling_plan_version"] = "CALIBRATION-CLEAN-PLAN-V1.1-STRATIFIED"
        manifest_data["codebook_version"] = "1.1.0"
        manifest_data["codebook_status"] = "locked"
        manifest_data["dictionary_version"] = "1.0.0"
        manifest_data["dictionary_status"] = "locked"
        manifest_data["codebook_sha256"] = view["codebook_sha256"]
        manifest_data["dictionary_sha256"] = view["dictionary_sha256"]
        manifest_data["blind_view_path"] = rel_view_path
        manifest_data["blind_view_sha256"] = view_hash
        manifest_data["blind_view_byte_size"] = len(payload)

        # Ensure top-level governance flags remain strict
        manifest_data["ready_for_annotation"] = False
        manifest_data["training_blocked"] = True
        manifest_data["acceptance"] = {
            "B": "pending_review",
            "D": "pending_review",
        }

        # Update governance section
        gov = manifest_data.setdefault("governance", {})
        gov["blind_view_reference"] = rel_view_path
        gov["blind_view_sha256"] = view_hash
        gov["blind_view_byte_size"] = len(payload)
        gov["ready_for_annotation"] = False
        gov["training_blocked"] = True

        mf_bytes = (json.dumps(manifest_data, indent=2, ensure_ascii=False) + "\n").encode("utf-8").replace(b"\r\n", b"\n")
        manifest_path.write_bytes(mf_bytes)

    return view, payload, view_hash


def verify_clean_blind_view(
    view_path: Path,
    candidates_path: Path,
    manifest_path: Path | None = None,
) -> Dict[str, Any]:
    """Verify an existing Blind View against candidates and manifest."""
    if not view_path.exists():
        raise FileNotFoundError(f"Blind view file not found: {view_path}")

    raw_bytes = view_path.read_bytes()
    if b"\r\n" in raw_bytes:
        raise ValueError(f"Blind view {view_path} contains CRLF! Must be pure LF.")

    view = json.loads(raw_bytes.decode("utf-8"))
    assert_no_label_leak(view)

    samples = view.get("samples", [])
    if len(samples) != 24:
        raise ValueError(f"Expected 24 samples in blind view, found {len(samples)}")

    cand_data = json.loads(candidates_path.read_text(encoding="utf-8"))
    main_cands = [c for c in cand_data["candidates"] if c["role"] == "main_24"]
    main_ids = [c["candidate_id"] for c in main_cands]
    view_ids = [s["sample_id"] for s in samples]

    if view_ids != main_ids:
        raise ValueError(f"Sample IDs mismatch! View: {view_ids}, Main: {main_ids}")

    # Check that no reserve candidates exist
    reserve_ids = {c["candidate_id"] for c in cand_data["candidates"] if c["role"] == "reserve_08"}
    overlap_reserve = set(view_ids) & reserve_ids
    if overlap_reserve:
        raise ValueError(f"Found reserve candidates in blind view: {overlap_reserve}")

    view_hash = compute_sha256(raw_bytes)
    result = {
        "status": "verified_clean",
        "sample_count": 24,
        "view_sha256": view_hash,
        "byte_size": len(raw_bytes),
        "zero_reserve_leak": True,
        "zero_label_leak": True,
    }

    if manifest_path and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("blind_view_sha256") and manifest["blind_view_sha256"] != view_hash:
            raise ValueError(
                f"Blind view SHA-256 ({view_hash}) does not match manifest ({manifest.get('blind_view_sha256')})"
            )
        result["manifest_verified"] = True

    return result


def main() -> int:
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidates",
        type=Path,
        default=ROOT / "data/restricted/clean_calibration_candidates_v2_restricted.json",
        help="Path to restricted candidates pool",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=ROOT / "data/raw/phreshphish/data",
        help="Directory containing train-000.parquet and train-055.parquet",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/annotations/clean_calibration_blind_view_24.json",
        help="Output Blind View path (must be gitignored)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "configs/calibration_clean_a_manifest.json",
        help="Manifest path to synchronize",
    )
    parser.add_argument(
        "--update-manifest",
        action="store_true",
        help="Update manifest with new blind view hash and paths",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing Blind View without re-exporting",
    )

    args = parser.parse_args()

    if args.verify_only:
        res = verify_clean_blind_view(args.output, args.candidates, args.manifest)
        print(f"VERIFICATION SUCCESS: {json.dumps(res, indent=2)}")
        return 0

    print("=== EXPORTING CLEAN CALIBRATION BLIND VIEW (24 MAIN SAMPLES) ===")
    view, payload, view_hash = export_clean_blind_view(
        candidates_path=args.candidates,
        source_root=args.source_root,
        output_path=args.output,
        manifest_path=args.manifest,
        update_manifest=args.update_manifest,
    )

    print(f"✅ Successfully exported {len(view['samples'])} samples to {args.output}")
    print(f"   - File size: {len(payload):,} bytes (Pure Unix LF)")
    print(f"   - SHA-256:   {view_hash}")
    print(f"   - Zero Reserve Leaks: 8 reserve samples remain sealed in restricted storage.")
    print(f"   - Zero Label Leaks: assert_no_label_leak passed.")

    if args.update_manifest:
        mf_hash = compute_sha256(args.manifest.read_bytes())
        print(f"✅ Synchronized manifest at {args.manifest}")
        print(f"   - Manifest SHA-256: {mf_hash}")
        print(f"   - ready_for_annotation=false, training_blocked=true preserved.")

    # Run verification pass
    verify_res = verify_clean_blind_view(args.output, args.candidates, args.manifest if args.update_manifest else None)
    print(f"✅ Independent post-export verification: {verify_res['status']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
