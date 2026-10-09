#!/usr/bin/env python3
"""Export baseline un-translated Blind View v1.1 for Calibration Proposal v2.

Uses max_html_characters=2_000_000 as approved by Lead D.
All samples have translation_provided=False, codebook_version='1.1.0'.
Guarantees zero label leakage (no labels, no targets, no scores).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phishing.annotation.blind_view import (
    assert_no_label_leak,
    create_blind_sample,
    extract_safe_view_content,
)


def export_base_view(
    proposal_path: Path,
    source_root: Path,
    output_path: Path,
) -> dict:
    private_root = (ROOT / "data/raw").resolve()
    if not output_path.resolve().is_relative_to(private_root):
        raise ValueError("Output phải nằm trong data/raw hạn chế")

    prop = json.loads(proposal_path.read_text(encoding="utf-8"))
    shards = {
        "data/train-000.parquet": pq.read_table(source_root / "train-000.parquet"),
        "data/train-055.parquet": pq.read_table(source_root / "train-055.parquet"),
    }

    clean_samples = []
    for idx, loc in enumerate(prop["main"]):
        sample_id = f"SMP-{idx + 1:03d}"
        tab = shards[loc["relative_path"]]
        row = tab.slice(loc["row_offset"], 1).to_pylist()[0]
        url = row["url"]
        html = row.get("html") or ""

        # Safe extraction with 2M characters limit
        page_text, summary = extract_safe_view_content(html, url, max_html_characters=2_000_000)

        blind = create_blind_sample(
            {
                "sample_id": sample_id,
                "url": url,
                "page_text": page_text,
                "structure_summary": summary,
            },
            codebook_version="1.1.0",
        )
        sample_dict = blind.to_dict()
        assert_no_label_leak(sample_dict)
        clean_samples.append(sample_dict)

    view = {
        "dataset_id": "CALIBRATION-PROPOSAL-V2",
        "version": "1.1.0",
        "status": "proposal_only_not_approved",
        "description": "Gói Blind View đề xuất v1.1 trước khi gắn bản dịch (hạn chế data/raw)",
        "is_synthetic": False,
        "samples": clean_samples,
    }

    assert_no_label_leak(view)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(view, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Exported base view with {len(clean_samples)} samples to {output_path}")
    return view


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--proposal",
        type=Path,
        default=ROOT / "data/raw/recovery/calibration-proposed-20261008-v2/selection.proposal.json",
    )
    parser.add_argument("--source-root", type=Path, default=ROOT / "data/raw/phreshphish/data")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/raw/recovery/calibration_proposal_v1.1_base.json",
    )
    args = parser.parse_args()

    export_base_view(args.proposal, args.source_root, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
