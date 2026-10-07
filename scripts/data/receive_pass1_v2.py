#!/usr/bin/env python3
"""Receive one V2 Pass 1 JSONL without changing its bytes or evaluating labels."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_kappa import index_by_sample_id, load_jsonl, validate_session_records
from phishing.annotation.blind_view import (
    assert_pilot_review_status,
    compute_sample_content_hash,
    validate_annotation_record,
)

MANIFEST = ROOT / "configs/pilot_manifest_v2.json"
REGISTRY = ROOT / "data/exclusion_registry.json"
OUT_ROOT = ROOT / "data/labels/intake_v2"
RELEASE_MANIFEST_SHA256 = "63f50697d6acbe75183237860f33a063a0f6e054f31f4ad4b5b0401a894c86f7"
RELEASE_VIEW_SHA256 = "e039c774ef5ff11b36786ccc8c762254974d89a4f4bfa7d5bc46b12e323ad1dc"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(records: list[dict], annotator: str, manifest_path: Path = MANIFEST) -> dict:
    """Check one complete human pass against the approved blind view."""
    if manifest_path == MANIFEST and sha256(manifest_path) != RELEASE_MANIFEST_SHA256:
        raise ValueError("Manifest V2 khác bản Pass 1 đã phát hành")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert_pilot_review_status(manifest)
    if (manifest.get("dataset_id") != "REAL-PILOT-32-V2"
            or manifest.get("ready_for_annotation") is not True
            or manifest.get("acceptance") != {"B": "approved", "D": "approved"}):
        raise ValueError("V2 manifest chưa được duyệt/mở Pass 1")
    view_path = ROOT / manifest["blind_view_path"]
    if manifest_path == MANIFEST and manifest["blind_view_sha256"] != RELEASE_VIEW_SHA256:
        raise ValueError("Blind view V2 khác bản Pass 1 đã phát hành")
    if sha256(view_path) != manifest["blind_view_sha256"]:
        raise ValueError("Blind view không khớp SHA-256 trong manifest")
    view = json.loads(view_path.read_text(encoding="utf-8"))
    if view.get("dataset_id") != manifest["dataset_id"] or view.get("is_synthetic") is not False:
        raise ValueError("Blind view sai gói hoặc không phải gói thật")
    samples = {s["sample_id"]: s for s in view["samples"]}
    expected_ids = {f"PILOT-{i:03d}" for i in range(1, 33)}
    if len(view["samples"]) != 32 or set(samples) != expected_ids:
        raise ValueError("Blind view phải có đúng 32 ID duy nhất")
    if len(records) != 32:
        raise ValueError("File kết quả phải có đúng 32 bản ghi")
    validate_session_records(records, Path(f"{annotator}.jsonl"), expected_annotator=annotator)
    indexed = index_by_sample_id(records, annotator)
    if set(indexed) != expected_ids:
        raise ValueError("Tập sample_id không khớp blind view V2")
    expected = {
        "dataset_id": manifest["dataset_id"],
        "dataset_hash": manifest["blind_view_sha256"],
        "codebook_version": manifest["codebook_version"],
        "codebook_hash": manifest["codebook_sha256"],
        "sampling_plan_version": manifest["sampling_plan_version"],
    }
    for sid, record in indexed.items():
        if record.get("is_dry_run") is not False or record.get("is_synthetic") is not False:
            raise ValueError(f"{sid}: chỉ nhận lượt gán thật, không nhận dry-run/synthetic")
        for field, value in expected.items():
            if record.get(field) != value:
                raise ValueError(f"{sid}: {field} không khớp manifest V2")
        if record.get("sample_content_hash") != compute_sample_content_hash(samples[sid]):
            raise ValueError(f"{sid}: nội dung mẫu không khớp blind view V2")
        if record.get("random_subset") is not samples[sid]["random_subset"]:
            raise ValueError(f"{sid}: random_subset không khớp kế hoạch đã khóa")
        if type(record.get("seconds_spent")) not in (int, float) or not math.isfinite(record["seconds_spent"]) or record["seconds_spent"] < 0:
            raise ValueError(f"{sid}: seconds_spent phải là số hữu hạn không âm")
        validate_annotation_record(record)
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if sha256(REGISTRY) != manifest["exclusion_registry_sha256"] or registry.get("training_blocked") is not True:
        raise ValueError("Registry loại trừ đã đổi hoặc chốt training bị mở")
    return {"annotator": annotator, "sample_count": 32,
            "manifest_sha256": sha256(manifest_path), "blind_view_sha256": sha256(view_path)}


def receive(input_path: Path, annotator: str, out_root: Path = OUT_ROOT,
            manifest_path: Path = MANIFEST) -> dict:
    """Preserve the original even when validation fails; never replace a prior receipt."""
    if annotator not in {"A", "B", "D", "E"}:
        raise ValueError("annotator phải là A, B, D hoặc E")
    raw = input_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    directory = out_root / annotator
    directory.mkdir(parents=True, exist_ok=True)
    saved = directory / f"{digest}.jsonl"
    if not saved.exists():
        with saved.open("xb") as handle:
            handle.write(raw)
    elif saved.read_bytes() != raw:
        raise ValueError("Trùng SHA-256 nhưng bytes khác nhau")
    receipt = {"annotator": annotator, "file_sha256": digest, "saved_path": str(saved)}
    try:
        receipt.update(verify(load_jsonl(saved), annotator, manifest_path))
        prior = [p for p in directory.glob("*.receipt.json") if p.stem.split(".")[0] != digest
                 and json.loads(p.read_text(encoding="utf-8")).get("status") == "accepted"]
        if prior:
            raise ValueError("Đã có file hợp lệ khác của cùng annotator; cần Lead D xử lý xung đột")
        receipt["status"] = "accepted"
    except (ValueError, FileNotFoundError, KeyError, TypeError, UnicodeError) as exc:
        receipt["status"] = "rejected"
        receipt["reason"] = str(exc)
    (directory / f"{digest}.receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotator", choices=("A", "B", "E"), required=True)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    receipt = receive(args.input, args.annotator)
    print(f"{receipt['status']}: {args.annotator}, SHA-256={receipt['file_sha256']}, lưu tại {receipt['saved_path']}")
    if receipt["status"] != "accepted":
        print(f"Lý do: {receipt['reason']}", file=sys.stderr)
        return 1
    print("Chỉ mới nhận một file; chưa tính Kappa/thời gian hoặc mở huấn luyện.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
