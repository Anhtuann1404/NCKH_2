#!/usr/bin/env python3
"""Propose a seeded calibration reservoir from verified train shards only.

Writes restricted locators and aggregate audit counts; never opens annotation,
approves a codebook, or updates the exclusion registry.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from phishing.data.date_parser import parse_strict_date
from phishing.data.loader import verify_source_file
from build_real_pilot_v2 import (
    file_hash, load_blocked_entities, record_fingerprints, write_json,
)

SHARDS = ("data/train-000.parquet", "data/train-055.parquet")
SEED = 20261008
MAIN_PER_CLASS = 12
RESERVE_PER_CLASS = 4
DATE_START, DATE_END = date(2024, 10, 1), date(2025, 9, 8)


def source_label(value) -> str | None:
    if type(value) is int:
        return {0: "benign", 1: "phish"}.get(value)
    if isinstance(value, str):
        return {"phishing": "phish", "phish": "phish", "benign": "benign"}.get(value.strip().lower())
    return None


def select(candidates: list[tuple[dict, str, dict]], blocked: dict[str, set[str]],
           seed: int = SEED) -> tuple[list[dict], list[dict]]:
    """Choose 12+12 proposed locators, then 4+4 ordered reserves; no labels in output."""
    shuffled = list(candidates)
    random.Random(seed).shuffle(shuffled)
    selected = {"phish": [], "benign": []}
    seen = {key: set() for key in blocked}
    for locator, label, fp in shuffled:
        if label not in selected or len(selected[label]) == MAIN_PER_CLASS + RESERVE_PER_CLASS:
            continue
        if any(fp[key] in blocked[key] or fp[key] in seen[key] for key in blocked):
            continue
        selected[label].append(locator)
        for key in blocked:
            seen[key].add(fp[key])
    if any(len(selected[label]) != MAIN_PER_CLASS + RESERVE_PER_CLASS for label in selected):
        raise ValueError("Không đủ ứng viên/nhóm độc lập cho 24 mẫu và 8 dự phòng")
    main = selected["phish"][:MAIN_PER_CLASS] + selected["benign"][:MAIN_PER_CLASS]
    reserve = selected["phish"][MAIN_PER_CLASS:] + selected["benign"][MAIN_PER_CLASS:]
    random.Random(seed + 1).shuffle(main)
    random.Random(seed + 2).shuffle(reserve)
    return main, reserve


def prepare(source_root: Path, output: Path, seed: int = SEED) -> dict:
    import pyarrow.parquet as pq

    private_root = (ROOT / "data/raw").resolve()
    if not output.resolve().is_relative_to(private_root):
        raise ValueError("Output phải nằm trong data/raw hạn chế")
    if output.exists():
        raise FileExistsError("Không ghi đè đề xuất đã lưu")
    manifest_path = ROOT / "configs/source_manifest.json"
    registry_path = ROOT / "data/exclusion_registry.json"
    evidence_path = ROOT / "data/raw/recovery/pilot-v2-prepare-20261006/prior_evidence.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_id") != "phreshphish" or manifest.get("source_split") != "train":
        raise ValueError("Chỉ dùng PhreshPhish train đã khóa")
    blocked = load_blocked_entities(evidence_path, registry_path)
    counts = Counter()
    candidates = []
    shard_hashes = {}
    for relative in SHARDS:
        path = (source_root / relative).resolve()
        if not path.is_relative_to(source_root.resolve()):
            raise ValueError("Shard vượt khỏi source_root")
        verify_source_file(path, manifest_path, "phreshphish")
        shard_hashes[relative] = file_hash(path)
        offset = 0
        for batch in pq.ParquetFile(path).iter_batches(batch_size=128,
                columns=["url", "html", "label", "date"]):
            for row in batch.to_pylist():
                label = source_label(row["label"])
                observed = parse_strict_date(row["date"])
                if label and observed and DATE_START <= observed <= DATE_END:
                    counts[f"window_{label}"] += 1
                    try:
                        fp = record_fingerprints(row["url"], row["html"])
                    except (ValueError, TypeError, AttributeError):
                        counts["invalid"] += 1
                    else:
                        if any(fp[key] in blocked[key] for key in blocked):
                            counts[f"excluded_{label}"] += 1
                        else:
                            counts[f"eligible_{label}"] += 1
                            candidates.append(({"relative_path": relative, "row_offset": offset}, label, fp))
                offset += 1
    main, reserve = select(candidates, blocked, seed)
    output.mkdir(parents=True)
    selection = {"status": "proposal_only_not_approved", "revision": manifest["revision"],
                 "seed": seed, "main": main, "reserve_ordered": reserve,
                 "difficulty_strata_status": "pending_predefined_rules"}
    write_json(output / "selection.proposal.json", selection)
    audit = {"status": "proposal_only_not_approved", "source_split": "train",
             "source_revision": manifest["revision"], "source_manifest_sha256": file_hash(manifest_path),
             "exclusion_registry_sha256": file_hash(registry_path),
             "prior_evidence_sha256": file_hash(evidence_path), "shards_sha256": shard_hashes,
             "seed": seed, "date_start": DATE_START.isoformat(), "date_end": DATE_END.isoformat(),
             "counts": dict(counts), "main_count": len(main), "reserve_count": len(reserve),
             "selection_sha256": file_hash(output / "selection.proposal.json"),
             "note": "Source labels used for sampling strata only; hard-case rules and v1.1 approval pending."}
    write_json(output / "audit.json", audit)
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.source_root, args.output)
    print(json.dumps({"status": report["status"], "counts": report["counts"],
                      "main_count": report["main_count"], "reserve_count": report["reserve_count"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
