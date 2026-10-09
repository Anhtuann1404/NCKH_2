#!/usr/bin/env python3
"""Offline translation experiment runner for Calibration v1.1.

Strict ARS & Safety Rules:
- 100% offline (Zero network calls, local_files_only=True).
- Deterministic inference with pinned seeds and beam search.
- Two independent runs compared byte-for-byte via SHA-256.
- Mathematical lossless chunking guaranteeing "".join(chunks) == text (no loss, no duplication).
- Every chunk is strictly bounded by max_tokens <= 200 (well below model capacity 512).
- Generates JSONL compatible with attach_offline_translations.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

for p in [r"D:\torch_lib", str(Path(__file__).resolve().parents[2] / ".venv" / "Lib" / "site-packages")]:
    if Path(p).exists() and p not in sys.path:
        sys.path.insert(0, p)

for dll_p in [r"D:\torch_lib\torch\lib", str(Path(__file__).resolve().parents[2] / ".venv" / "Lib" / "site-packages" / "torch" / "lib")]:
    dll_path = Path(dll_p).resolve()
    if hasattr(os, "add_dll_directory") and dll_path.exists():
        try:
            os.add_dll_directory(str(dll_path))
        except Exception:
            pass

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import pyarrow.parquet as pq
import torch
from transformers import MarianMTModel, MarianTokenizer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phishing.annotation.blind_view import extract_safe_view_content


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# Lookbehind regex keeping delimiters attached to the left fragment: "".join(split) == original
_SENTENCE_BOUNDARY = re.compile(r"(?<=[。！？!?\n])")
_CLAUSE_BOUNDARY = re.compile(r"(?<=[、,;:|/])")


def _count_tokens(text: str, tok: MarianTokenizer) -> int:
    if not text:
        return 0
    return len(tok.tokenize(text))


def _max_fitting_prefix_len(text: str, start: int, tok: MarianTokenizer, max_tokens: int) -> int:
    lo, hi = 1, len(text) - start
    best = 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if _count_tokens(text[start : start + mid], tok) <= max_tokens:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    if _count_tokens(text[start : start + best], tok) > max_tokens:
        best = 1
    return best


def _char_split(text: str, tok: MarianTokenizer, max_tokens: int) -> list[str]:
    chunks, cursor, length = [], 0, len(text)
    while cursor < length:
        take = _max_fitting_prefix_len(text, cursor, tok, max_tokens)
        chunks.append(text[cursor : cursor + take])
        cursor += take
    return chunks


def _split_until_fits(piece: str, tok: MarianTokenizer, max_tokens: int) -> list[str]:
    if _count_tokens(piece, tok) <= max_tokens:
        return [piece]
    subparts = [p for p in _CLAUSE_BOUNDARY.split(piece) if p]
    if len(subparts) <= 1:
        return _char_split(piece, tok, max_tokens)
    res = []
    for sp in subparts:
        if _count_tokens(sp, tok) <= max_tokens:
            res.append(sp)
        else:
            res.extend(_char_split(sp, tok, max_tokens))
    return res


def chunk_text_without_loss(text: str, tok: MarianTokenizer, max_tokens: int = 200) -> list[str]:
    """Split text into token-bounded, lossless, non-overlapping chunks.

    Guarantees: ''.join(chunks) == text exactly, and every chunk <= max_tokens.
    """
    if not text:
        return []
    atoms = []
    for s in [frag for frag in _SENTENCE_BOUNDARY.split(text) if frag]:
        atoms.extend(_split_until_fits(s, tok, max_tokens))
    chunks = []
    buf = ""
    for a in atoms:
        cand = buf + a
        if _count_tokens(cand, tok) <= max_tokens:
            buf = cand
        else:
            if buf:
                chunks.append(buf)
            buf = a
    if buf:
        chunks.append(buf)
    return chunks


def verify_no_loss_or_overlap(text: str, chunks: list[str]) -> bool:
    return "".join(chunks) == text


class OfflineTranslator:
    def __init__(self, model_dir: Path, max_chunk_tokens: int = 200, num_beams: int = 4, num_threads: int = 4):
        self.model_dir = model_dir
        self.max_chunk_tokens = max_chunk_tokens
        self.num_beams = num_beams
        self.tokenizer = MarianTokenizer.from_pretrained(str(model_dir), local_files_only=True)
        self.model = MarianMTModel.from_pretrained(str(model_dir), local_files_only=True)
        self.model.eval()
        torch.set_num_threads(num_threads)

    def translate_sample(self, text: str) -> tuple[str, list[dict]]:
        if not text or not text.strip():
            return "", []
        chunks = chunk_text_without_loss(text, self.tokenizer, max_tokens=self.max_chunk_tokens)
        if not verify_no_loss_or_overlap(text, chunks):
            raise RuntimeError("CRITICAL ERROR: Lossless chunk verification failed! Text was lost or overlapping.")

        translated_chunks = []
        chunk_metadata = []
        torch.manual_seed(42)
        with torch.no_grad():
            for idx, c in enumerate(chunks):
                inputs = self.tokenizer(c, return_tensors="pt")
                outputs = self.model.generate(
                    **inputs,
                    num_beams=self.num_beams,
                    do_sample=False,
                    max_new_tokens=256,
                )
                trans = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
                translated_chunks.append(trans)
                chunk_metadata.append({
                    "chunk_index": idx,
                    "source_char_len": len(c),
                    "source_token_count": len(inputs.input_ids[0]),
                    "translated_word_count": len(trans.split()),
                    "translated_snippet": trans[:80],
                })
        return " ".join(translated_chunks), chunk_metadata


def extract_page_text_for_proposal(proposal_path: Path, source_root: Path) -> list[dict]:
    prop = json.loads(proposal_path.read_text(encoding="utf-8"))
    shards = {
        "data/train-000.parquet": pq.read_table(source_root / "train-000.parquet"),
        "data/train-055.parquet": pq.read_table(source_root / "train-055.parquet"),
    }
    results = []
    for idx, loc in enumerate(prop["main"]):
        sample_id = f"SMP-{idx + 1:03d}"
        tab = shards[loc["relative_path"]]
        row = tab.slice(loc["row_offset"], 1).to_pylist()[0]
        url = row["url"]
        html = row.get("html") or ""
        # Apply 2M characters limit as approved by Lead D
        page_text, summary = extract_safe_view_content(html, url, max_html_characters=2_000_000)
        results.append({
            "sample_id": sample_id,
            "locator": loc,
            "url": url,
            "page_text": page_text,
            "source_label": row.get("label"),
            "structure_summary": summary,
        })
    return results


def run_experiment(
    proposal_dir: Path,
    source_root: Path,
    model_dir: Path,
    output_dir: Path,
) -> dict:
    sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)
    samples = extract_page_text_for_proposal(proposal_dir / "selection.proposal.json", source_root)

    # Detect Japanese samples
    ja_samples = []
    for s in samples:
        txt = s["page_text"]
        if bool(re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", txt)):
            ja_samples.append(s)

    print(f"Total main samples: {len(samples)}", flush=True)
    print(f"Japanese samples needing translation: {len(ja_samples)}", flush=True)
    for j in ja_samples:
        print(f"  - {j['sample_id']}: {j['url']} (text chars: {len(j['page_text'])})", flush=True)

    # Read model manifest
    model_manifest = json.loads((model_dir / "model_manifest.json").read_text(encoding="utf-8"))
    primary_weight_sha = model_manifest["primary_weight_sha256"]

    translator = OfflineTranslator(model_dir, max_chunk_tokens=200, num_beams=4, num_threads=4)

    def generate_batch(run_name: str) -> tuple[list[dict], dict[str, list], bytes]:
        rows = []
        sample_chunks_map = {}
        t_start = time.time()
        for idx, s in enumerate(ja_samples):
            t_s = time.time()
            source_txt = s["page_text"]
            source_hash = digest(source_txt.encode("utf-8"))
            translated_txt, chunk_meta = translator.translate_sample(source_txt)
            sample_chunks_map[s["sample_id"]] = chunk_meta
            rows.append({
                "sample_id": s["sample_id"],
                "source_text_sha256": source_hash,
                "translated_text": translated_txt,
                "source_language": "ja",
            })
            print(f"  [{run_name}] {s['sample_id']} translated ({len(chunk_meta)} chunks, {round(time.time() - t_s, 2)}s)", flush=True)
        lines = [json.dumps(r, ensure_ascii=False) for r in rows]
        payload = ("\n".join(lines) + "\n").encode("utf-8")
        print(f"  [{run_name}] Completed all samples in {round(time.time() - t_start, 2)}s, payload SHA-256: {digest(payload)}", flush=True)
        return rows, sample_chunks_map, payload

    # Run A
    print("\n--- Executing Run A (deterministic inference) ---", flush=True)
    rows_a, chunks_map_a, payload_a = generate_batch("Run A")
    sha_a = digest(payload_a)

    # Run B
    print("\n--- Executing Run B (independent deterministic verification) ---", flush=True)
    rows_b, chunks_map_b, payload_b = generate_batch("Run B")
    sha_b = digest(payload_b)

    if sha_a != sha_b:
        raise RuntimeError(f"Deterministic verification FAILED! Run A: {sha_a} != Run B: {sha_b}")
    print(f"\nDeterministic verification PASSED 100%! Byte-for-byte matching SHA-256: {sha_a}", flush=True)

    # Write output translations JSONL
    out_jsonl = output_dir / "translations_ja_en.jsonl"
    out_jsonl.write_bytes(payload_a)

    # QC checks
    qc_results = []
    cta_keywords = ["login", "account", "cart", "shop", "shipping", "payment", "contact", "order", "return", "privacy", "password", "email", "address"]
    for row, orig in zip(rows_a, ja_samples):
        trans = row["translated_text"]
        found_cta = [kw for kw in cta_keywords if kw in trans.lower()]
        token_ratio = len(trans.split()) / max(1, len(orig["page_text"]))
        # Check if any Japanese characters remain untranslated
        untranslated_chars = len(re.findall(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", trans))
        qc_results.append({
            "sample_id": row["sample_id"],
            "url": orig["url"],
            "source_chars": len(orig["page_text"]),
            "chunk_count": len(chunks_map_a[row["sample_id"]]),
            "lossless_verified": True,
            "translated_words": len(trans.split()),
            "token_ratio": round(token_ratio, 3),
            "untranslated_cjk_char_count": untranslated_chars,
            "cta_detected": found_cta,
            "sample_chunks": chunks_map_a[row["sample_id"]][:2],
            "full_snippet": trans[:300] + ("..." if len(trans) > 300 else ""),
        })

    report = {
        "status": "experiment_ready_for_review",
        "model_id": "Helsinki-NLP/opus-mt-ja-en",
        "model_primary_weight_sha256": primary_weight_sha,
        "environment": {
            "torch_version": torch.__version__,
            "sentencepiece_installed": True,
            "offline_mode": True,
            "deterministic_seed": 42,
            "num_beams": 4,
            "max_chunk_tokens": 200,
            "num_threads": 4,
        },
        "chunking_verification": {
            "algorithm": "lossless_zero_overlap_boundary_aware",
            "lossless_verified_all": True,
            "max_tokens_ceiling": 200,
        },
        "deterministic_verification": {
            "run_a_sha256": sha_a,
            "run_b_sha256": sha_b,
            "byte_identical": sha_a == sha_b,
        },
        "batch_file": str(out_jsonl.relative_to(ROOT)).replace("\\", "/"),
        "batch_file_sha256": sha_a,
        "translated_count": len(rows_a),
        "qc_audit": qc_results,
    }

    report_path = output_dir / "translation_experiment_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nSaved experiment report: {report_path}", flush=True)
    return report


def run_single_pass(
    proposal_dir: Path,
    source_root: Path,
    model_dir: Path,
    output_payload_file: Path,
) -> dict:
    import os
    sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
    samples = extract_page_text_for_proposal(proposal_dir / "selection.proposal.json", source_root)
    ja_samples = [s for s in samples if bool(re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", s["page_text"]))]

    translator = OfflineTranslator(model_dir, max_chunk_tokens=200, num_beams=4, num_threads=4)
    rows = []
    for idx, s in enumerate(ja_samples, 1):
        sys.stderr.write(f"[{os.getpid()}] Translating sample {idx}/{len(ja_samples)}: {s['sample_id']}...\n")
        sys.stderr.flush()
        translated_txt, _ = translator.translate_sample(s["page_text"])
        rows.append({
            "sample_id": s["sample_id"],
            "source_text_sha256": digest(s["page_text"].encode("utf-8")),
            "translated_text": translated_txt,
            "source_language": "ja",
        })
    lines = [json.dumps(r, ensure_ascii=False) for r in rows]
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    output_payload_file.parent.mkdir(parents=True, exist_ok=True)
    output_payload_file.write_bytes(payload)
    sha256_hash = digest(payload)
    info = {
        "pid": os.getpid(),
        "payload_sha256": sha256_hash,
        "bytes_count": len(payload),
        "output_file": str(output_payload_file),
    }
    print(json.dumps(info), flush=True)
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal-dir", type=Path, default=ROOT / "data/raw/recovery/calibration-proposed-20261008-v2")
    parser.add_argument("--source-root", type=Path, default=ROOT / "data/raw/phreshphish/data")
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models/translation/opus-mt-ja-en")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/raw/recovery/translation_experiment")
    parser.add_argument("--single-run-payload", type=Path, default=None, help="Run single pass and save payload to file")
    args = parser.parse_args()

    if args.single_run_payload:
        run_single_pass(args.proposal_dir, args.source_root, args.model_dir, args.single_run_payload)
        return 0

    report = run_experiment(args.proposal_dir, args.source_root, args.model_dir, args.output_dir)
    print(json.dumps({
        "status": report["status"],
        "translated_count": report["translated_count"],
        "batch_sha256": report["batch_file_sha256"],
        "byte_identical": report["deterministic_verification"]["byte_identical"],
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
