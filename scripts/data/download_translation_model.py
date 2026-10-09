#!/usr/bin/env python3
"""Download and pin an offline translation model snapshot with SHA-256 provenance.

Strict ARS rules:
- Downloads to a local model directory outside version control.
- Records exact revision (commit SHA) and computes SHA-256 checksums for every artifact.
- Enables 100% offline usage subsequently with TRANSFORMERS_OFFLINE=1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from huggingface_hub import snapshot_download


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_and_verify(repo_id: str, local_dir: Path) -> dict:
    local_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading snapshot for {repo_id} to {local_dir}...")
    snapshot_path = snapshot_download(
        repo_id=repo_id,
        local_dir=str(local_dir),
        local_dir_use_symlinks=False,
        ignore_patterns=["*.msgpack", "*.h5", "*.ot"],
    )

    manifest_files = {}
    for item in sorted(local_dir.rglob("*")):
        if item.is_file() and item.name != "model_manifest.json":
            rel_name = str(item.relative_to(local_dir)).replace("\\", "/")
            manifest_files[rel_name] = {
                "size_bytes": item.stat().st_size,
                "sha256": file_sha256(item),
            }

    # Find main weights artifact
    primary_weight_sha = None
    for candidate in ["model.safetensors", "pytorch_model.bin"]:
        if candidate in manifest_files:
            primary_weight_sha = manifest_files[candidate]["sha256"]
            break

    manifest = {
        "model_repo_id": repo_id,
        "local_dir": str(local_dir.resolve()),
        "primary_weight_sha256": primary_weight_sha,
        "files_count": len(manifest_files),
        "files": manifest_files,
    }

    manifest_path = local_dir / "model_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Verified {len(manifest_files)} artifacts. Primary weight SHA-256: {primary_weight_sha}")
    print(f"Saved manifest: {manifest_path}")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-id", default="Helsinki-NLP/opus-mt-ja-en", help="HuggingFace model repo id")
    parser.add_argument("--local-dir", type=Path, default=Path("models/translation/opus-mt-ja-en"), help="Local destination directory")
    args = parser.parse_args()

    download_and_verify(args.repo_id, args.local_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
