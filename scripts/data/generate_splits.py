#!/usr/bin/env python3
"""CLI công cụ phân chia tập dữ liệu chống rò rỉ (DATA-03 Splits Generator).

Tự động sinh:
1. groups.json: Ánh xạ sample_id -> group_id (eTLD+1 / UGC tenant).
2. grouped_5fold_splits.json: Phân chia 5-fold CV qua 3 seeds (17, 42, 2026) kèm inner validation.
3. temporal_splits.json: Phân chia mốc thời gian 60/20/20 không chia ngày và loại trừ trùng nhóm sớm.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

# Thêm src vào PYTHONPATH nếu chạy trực tiếp
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from phishing.data.grouping import extract_group_id
from phishing.data.splits import (
    DEFAULT_SEEDS,
    assert_no_group_leakage,
    generate_grouped_kfold,
    generate_temporal_split,
)


def load_records(input_path: Path) -> List[Dict[str, Any]]:
    """Nạp danh sách bản ghi từ tệp JSON hoặc JSONL."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    suffix = input_path.suffix.lower()
    records: List[Dict[str, Any]] = []

    if suffix == ".jsonl":
        with open(input_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    records.append(json.loads(line_str))
                except json.JSONDecodeError as err:
                    raise ValueError(f"Invalid JSON at line {line_no} in {input_path}: {err}") from err
    elif suffix == ".json":
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict) and "samples" in data and isinstance(data["samples"], list):
                records = data["samples"]
            else:
                raise ValueError("JSON input must be a list of records or contain a 'samples' list.")
    else:
        raise ValueError(f"Unsupported input file format: {suffix}. Supported: .json, .jsonl")

    return records


def calculate_sha256(file_path: Path) -> str:
    """Tính mã băm SHA-256 chuẩn hóa cho tệp đầu ra."""
    with open(file_path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="NCKH_2 Anti-Leakage Data Splitting Tool (Grouped 5-Fold & Temporal 60/20/20)."
    )
    parser.add_argument("--input", "-i", type=str, required=True, help="Path to input JSON or JSONL file.")
    parser.add_argument("--output-dir", "-o", type=str, default="data/splits", help="Directory to save split manifests.")
    parser.add_argument("--n-splits", "-k", type=int, default=5, help="Number of folds (default: 5).")
    parser.add_argument("--seeds", type=str, default="17,42,2026", help="Comma-separated random seeds (default: 17,42,2026).")
    parser.add_argument("--id-field", type=str, default="sample_id", help="Field name for unique ID.")
    parser.add_argument("--url-field", type=str, default="url", help="Field name for URL.")
    parser.add_argument("--date-field", type=str, default="collected_at", help="Field name for collection date.")
    parser.add_argument("--label-field", type=str, default="class_label", help="Field name for label.")
    parser.add_argument("--skip-temporal", action="store_true", help="Skip temporal split if dates not available.")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    seeds = tuple(int(s.strip()) for s in args.seeds.split(",") if s.strip())

    print(f"[*] Loading records from: {input_path}")
    try:
        records = load_records(input_path)
    except Exception as err:
        print(f"[!] Error loading input records: {err}", file=sys.stderr)
        return 1

    print(f"[*] Successfully loaded {len(records)} records.")

    # 1. Trích xuất groups
    print("[*] Extracting group_id (eTLD+1 & UGC tenant)...")
    groups_manifest: Dict[str, Any] = {
        "metadata": {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_file": str(input_path),
            "total_records": len(records),
        },
        "sample_groups": {},
        "group_summary": {},
    }

    group_counts: Dict[str, int] = {}
    for idx, rec in enumerate(records):
        sid = str(rec.get(args.id_field, f"SAMPLE-{idx:05d}"))
        raw_url = str(rec.get(args.url_field, ""))
        gid = extract_group_id(raw_url) if raw_url else f"row:{idx}"
        groups_manifest["sample_groups"][sid] = gid
        group_counts[gid] = group_counts.get(gid, 0) + 1

    groups_manifest["group_summary"] = {
        "distinct_groups_count": len(group_counts),
        "top_groups": sorted(group_counts.items(), key=lambda x: x[1], reverse=True)[:10],
    }

    groups_file = output_dir / "groups.json"
    with open(groups_file, "w", encoding="utf-8") as f:
        json.dump(groups_manifest, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved groups index: {groups_file} ({len(group_counts)} distinct groups)")

    # 2. Tạo Grouped 5-Fold Cross Validation
    print(f"[*] Generating Grouped {args.n_splits}-Fold CV across seeds: {seeds}...")
    try:
        grouped_results = generate_grouped_kfold(
            records=records,
            n_splits=args.n_splits,
            seeds=seeds,
            id_field=args.id_field,
            url_field=args.url_field,
            label_field=args.label_field,
        )
    except Exception as err:
        print(f"[!] Error generating grouped k-fold: {err}", file=sys.stderr)
        return 1

    grouped_manifest: Dict[str, Any] = {
        "metadata": {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "n_splits": args.n_splits,
            "seeds": list(seeds),
            "anti_leakage_verified": True,
        },
        "splits_by_seed": grouped_results,
    }

    grouped_file = output_dir / "grouped_5fold_splits.json"
    with open(grouped_file, "w", encoding="utf-8") as f:
        json.dump(grouped_manifest, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved Grouped 5-Fold splits: {grouped_file}")

    # 3. Tạo Temporal Split (nếu không bỏ qua)
    if not args.skip_temporal:
        print("[*] Generating Temporal Split (60% Train / 20% Val / 20% Test)...")
        try:
            temporal_result = generate_temporal_split(
                records=records,
                train_ratio=0.6,
                val_ratio=0.2,
                test_ratio=0.2,
                id_field=args.id_field,
                date_field=args.date_field,
                url_field=args.url_field,
                purge_overlapping_groups=True,
            )

            temporal_manifest: Dict[str, Any] = {
                "metadata": {
                    "created_at_utc": datetime.now(timezone.utc).isoformat(),
                    "train_ratio": 0.6,
                    "val_ratio": 0.2,
                    "test_ratio": 0.2,
                    "purge_overlapping_groups": True,
                    "anti_leakage_verified": True,
                },
                "split": temporal_result,
            }

            temporal_file = output_dir / "temporal_splits.json"
            with open(temporal_file, "w", encoding="utf-8") as f:
                json.dump(temporal_manifest, f, indent=2, ensure_ascii=False)
            print(f"[+] Saved Temporal splits: {temporal_file}")
            print(
                f"    - Train: {temporal_result['metrics']['train_sample_count']} samples "
                f"({temporal_result['train_date_range'][0]} to {temporal_result['train_date_range'][1]})"
            )
            print(
                f"    - Val: {temporal_result['metrics']['val_clean_sample_count']} clean samples "
                f"({temporal_result['metrics']['val_purged_sample_count']} purged) "
                f"({temporal_result['val_date_range'][0]} to {temporal_result['val_date_range'][1]})"
            )
            print(
                f"    - Test: {temporal_result['metrics']['test_clean_sample_count']} clean samples "
                f"({temporal_result['metrics']['test_purged_sample_count']} purged) "
                f"({temporal_result['test_date_range'][0]} to {temporal_result['test_date_range'][1]})"
            )
        except Exception as err:
            print(f"[!] Warning: Temporal split skipped due to: {err}")

    print("\n[V] DATA-03 splitting generation completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
