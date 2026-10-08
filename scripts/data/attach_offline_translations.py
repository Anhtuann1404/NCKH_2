#!/usr/bin/env python3
"""Attach already-produced offline translations to a proposed v1.1 blind view.

This tool does not translate, call a service, approve a manifest, or open annotation.
Inputs and outputs stay in the restricted data/raw area.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phishing.annotation.blind_view import assert_no_label_leak


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def attach(view: dict, translations: list[dict], tool: str, version: str) -> dict:
    """Return a copy; bind each translation to the exact final page_text bytes."""
    if not tool.strip() or not version.strip():
        raise ValueError("Cần tên và phiên bản công cụ dịch ngoại tuyến")
    assert_no_label_leak(view)
    samples = view.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ValueError("View phải có danh sách mẫu không rỗng")
    ids = [s.get("sample_id") for s in samples]
    if len(set(ids)) != len(ids):
        raise ValueError("View có sample_id trùng")
    if any(s.get("codebook_version") != "1.1.0" or s.get("translation_provided") is not False
           for s in samples):
        raise ValueError("Chỉ nhận view v1.1 chưa có bản dịch")
    by_id = {}
    for row in translations:
        if set(row) != {"sample_id", "source_text_sha256", "translated_text", "source_language"}:
            raise ValueError("Dòng dịch phải có đúng bốn trường đã định")
        sid = row["sample_id"]
        if sid in by_id:
            raise ValueError("Trùng sample_id trong bảng dịch")
        if not all(isinstance(row[key], str) and row[key].strip()
                   for key in ("sample_id", "source_text_sha256", "translated_text", "source_language")):
            raise ValueError("Bảng dịch chứa trường rỗng hoặc sai kiểu")
        by_id[sid] = row
    if not set(by_id) <= set(ids):
        raise ValueError("Bảng dịch có sample_id ngoài view")
    output = dict(view)
    output["samples"] = []
    for sample in samples:
        new = dict(sample)
        row = by_id.get(sample["sample_id"])
        if row:
            source = sample.get("page_text")
            if not isinstance(source, str) or not source.strip():
                raise ValueError("Không được dịch page_text rỗng")
            if digest(source.encode("utf-8")) != row["source_text_sha256"]:
                raise ValueError(f"{sample['sample_id']}: bản dịch không khớp page_text đã lọc")
            new.update({
                "translation_provided": True,
                "translated_text": row["translated_text"],
                "translation_source_language": row["source_language"],
                "translation_tool": tool,
                "translation_tool_version": version,
                "translation_sha256": digest(row["translated_text"].encode("utf-8")),
            })
        output["samples"].append(new)
    assert_no_label_leak(output)
    return output


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("Bảng dịch phải là JSONL object")
            rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--view", type=Path, required=True)
    parser.add_argument("--translations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tool", required=True)
    parser.add_argument("--tool-version", required=True)
    parser.add_argument("--tool-artifact-sha256", required=True)
    args = parser.parse_args()
    private_root = (ROOT / "data/raw").resolve()
    for path in (args.view, args.translations, args.output):
        if not path.resolve().is_relative_to(private_root):
            raise ValueError("View, bảng dịch và output phải nằm trong data/raw hạn chế")
    if args.output.exists():
        raise FileExistsError("Không ghi đè gói đã chuẩn bị")
    if len(args.tool_artifact_sha256) != 64 or any(c not in "0123456789abcdef" for c in args.tool_artifact_sha256):
        raise ValueError("Cần SHA-256 hex của công cụ/model dịch ngoại tuyến")
    view_bytes = args.view.read_bytes()
    translation_bytes = args.translations.read_bytes()
    result = attach(json.loads(view_bytes), read_jsonl(args.translations), args.tool, args.tool_version)
    payload = (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    receipt = {
        "status": "proposal_only_not_approved",
        "source_view_sha256": digest(view_bytes),
        "translation_batch_sha256": digest(translation_bytes),
        "output_view_sha256": digest(payload),
        "tool": args.tool,
        "tool_version": args.tool_version,
        "tool_artifact_sha256": args.tool_artifact_sha256,
        "translated_count": sum(s["translation_provided"] for s in result["samples"]),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as handle:
        handle.write(payload)
    args.output.with_suffix(args.output.suffix + ".receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
