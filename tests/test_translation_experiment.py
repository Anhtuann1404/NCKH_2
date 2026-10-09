"""Unit tests for offline translation chunking and verification logic."""

from __future__ import annotations

import os
from pathlib import Path
import sys

for p in [r"D:\torch_lib", str(Path(__file__).resolve().parents[1] / ".venv" / "Lib" / "site-packages")]:
    if Path(p).exists() and p not in sys.path:
        sys.path.insert(0, p)

for dll_p in [r"D:\torch_lib\torch\lib", str(Path(__file__).resolve().parents[1] / ".venv" / "Lib" / "site-packages" / "torch" / "lib")]:
    dll_path = Path(dll_p).resolve()
    if hasattr(os, "add_dll_directory") and dll_path.exists():
        try:
            os.add_dll_directory(str(dll_path))
        except Exception:
            pass

import pytest
from transformers import MarianTokenizer

from scripts.data.run_offline_translation_experiment import (
    chunk_text_without_loss,
    verify_no_loss_or_overlap,
)


@pytest.fixture(scope="module")
def tokenizer():
    # Load from local downloaded artifact
    return MarianTokenizer.from_pretrained("models/translation/opus-mt-ja-en", local_files_only=True)


def test_chunk_empty_text(tokenizer):
    assert chunk_text_without_loss("", tokenizer) == []
    assert verify_no_loss_or_overlap("", []) is True


def test_chunk_short_sentence(tokenizer):
    text = "これはテストメッセージです。"
    chunks = chunk_text_without_loss(text, tokenizer, max_tokens=50)
    assert chunks == [text]
    assert verify_no_loss_or_overlap(text, chunks) is True


def test_chunk_multi_sentence_lossless(tokenizer):
    text = "第1文です。第2文です！第3文ですか？第4文。"
    chunks = chunk_text_without_loss(text, tokenizer, max_tokens=8)
    assert verify_no_loss_or_overlap(text, chunks) is True
    assert len(chunks) >= 2
    for c in chunks:
        assert len(tokenizer.tokenize(c)) <= 8


def test_chunk_unpunctuated_long_string_lossless(tokenizer):
    # Long repetition without any punctuation
    text = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん" * 5
    chunks = chunk_text_without_loss(text, tokenizer, max_tokens=30)
    assert verify_no_loss_or_overlap(text, chunks) is True
    assert len(chunks) > 1
    for c in chunks:
        assert len(tokenizer.tokenize(c)) <= 30


def test_verify_no_loss_or_overlap_detects_tampering():
    original = "こんにちは世界"
    valid_chunks = ["こんにちは", "世界"]
    assert verify_no_loss_or_overlap(original, valid_chunks) is True

    # Loss
    loss_chunks = ["こんにちは"]
    assert verify_no_loss_or_overlap(original, loss_chunks) is False

    # Duplication
    dupe_chunks = ["こんにちは", "世界", "世界"]
    assert verify_no_loss_or_overlap(original, dupe_chunks) is False

    # Out of order
    shuffled_chunks = ["世界", "こんにちは"]
    assert verify_no_loss_or_overlap(original, shuffled_chunks) is False
