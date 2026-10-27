#!/usr/bin/env python3
"""Deterministic offline translation for Clean Calibration Runway A samples.

Follows Codebook v1.1 Rule R-A09:
- Uses local, offline pinned MarianMT models:
  * Helsinki-NLP/opus-mt-ja-en (revision 0770961a39ba6bd66305b149c3f4110bcafca2e6)
  * Helsinki-NLP/opus-mt-ru-en (revision fbd6dc73284f95536648512cc21d57f19191961a)
- Mathematically lossless chunking (_SENTENCE_BOUNDARY + _CLAUSE_BOUNDARY) <= 200 tokens.
- Deterministic beam search with fixed seed.
- Cryptographically binds output translated_text to source_text_sha256.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.data.run_offline_translation_experiment import (
    OfflineTranslator,
    chunk_text_without_loss,
    verify_no_loss_or_overlap,
)

JA_MODEL_DIR = ROOT / "models/translation/opus-mt-ja-en"
RU_MODEL_DIR = ROOT / "models/translation/opus-mt-ru-en"
VIEW_PATH = ROOT / "data/annotations/clean_calibration_blind_view_24.json"
OUT_TRANSLATIONS = ROOT / "data/restricted/clean_calibration_translations.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate_clean_translations() -> dict:
    if not VIEW_PATH.exists():
        raise FileNotFoundError(f"Missing view at {VIEW_PATH}")

    view = json.loads(VIEW_PATH.read_text(encoding="utf-8"))
    samples = {s["sample_id"]: s for s in view["samples"]}

    print("Initializing JA-EN translator...")
    ja_translator = OfflineTranslator(JA_MODEL_DIR, max_chunk_tokens=200, num_beams=4, num_threads=4)

    print("Initializing RU-EN translator...")
    ru_translator = OfflineTranslator(RU_MODEL_DIR, max_chunk_tokens=200, num_beams=4, num_threads=4)

    targets = [
        ("SMP-007", "ja", ja_translator, "Helsinki-NLP/opus-mt-ja-en", "0770961a39ba6bd66305b149c3f4110bcafca2e6"),
        ("SMP-008", "ja", ja_translator, "Helsinki-NLP/opus-mt-ja-en", "0770961a39ba6bd66305b149c3f4110bcafca2e6"),
        ("SMP-010", "ru", ru_translator, "Helsinki-NLP/opus-mt-ru-en", "fbd6dc73284f95536648512cc21d57f19191961a"),
    ]

    translations = {}
    for sid, lang, translator, repo_id, rev in targets:
        s = samples[sid]
        src_text = s.get("page_text", "")
        src_hash = digest(src_text.encode("utf-8"))
        print(f"Translating {sid} ({lang}, {len(src_text)} chars)...")

        trans_text, meta = translator.translate_sample(src_text)
        trans_hash = digest(trans_text.encode("utf-8"))

        translations[sid] = {
            "sample_id": sid,
            "source_language": lang,
            "source_text_sha256": src_hash,
            "source_char_count": len(src_text),
            "translated_text": trans_text,
            "translated_char_count": len(trans_text),
            "translated_word_count": len(trans_text.split()),
            "translation_tool": "MarianMT",
            "translation_tool_version": f"{repo_id}@{rev[:7]}",
            "translation_sha256": trans_hash,
            "chunks_count": len(meta),
        }
        print(f"  -> Translated {sid}: {len(trans_text)} chars, {len(trans_text.split())} words, SHA: {trans_hash[:16]}...")

    OUT_TRANSLATIONS.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(translations, indent=2, ensure_ascii=False) + "\n"
    OUT_TRANSLATIONS.write_text(payload, encoding="utf-8")
    print(f"Saved translations to {OUT_TRANSLATIONS}")
    return translations


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure") and sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8")
    generate_clean_translations()
