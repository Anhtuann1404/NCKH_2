"""No network/model needed to verify translation provenance and blind fields."""

import hashlib

import pytest

from phishing.annotation.blind_view import create_blind_sample, compute_sample_content_hash
from scripts.data.attach_offline_translations import attach


def _view():
    sample = create_blind_sample(
        {"sample_id": "SMP-301", "url": "https://example.test/", "page_text": "Anmeldung"},
        codebook_version="1.1.0",
    ).to_dict()
    return {"dataset_id": "CAL-PROPOSAL", "is_synthetic": False, "samples": [sample]}


def _row(source="Anmeldung"):
    return {"sample_id": "SMP-301", "source_text_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "translated_text": "Đăng nhập", "source_language": "de"}


def test_attach_binds_exact_source_text_and_keeps_original():
    view = _view()
    original_hash = compute_sample_content_hash(view["samples"][0])
    result = attach(view, [_row()], "offline-tool", "1.0")
    sample = result["samples"][0]
    assert sample["page_text"] == "Anmeldung"
    assert sample["translated_text"] == "Đăng nhập"
    assert sample["translation_sha256"] == hashlib.sha256("Đăng nhập".encode()).hexdigest()
    assert compute_sample_content_hash(sample) != original_hash
    assert view["samples"][0]["translation_provided"] is False


def test_attach_rejects_stale_source_and_label_leak():
    with pytest.raises(ValueError, match="không khớp page_text"):
        attach(_view(), [_row("Old text")], "offline-tool", "1.0")
    leaky = _view()
    leaky["samples"][0]["source_label"] = "phishing"
    with pytest.raises(ValueError, match="RÒ RỈ"):
        attach(leaky, [_row()], "offline-tool", "1.0")


def test_attach_rejects_extra_ids_and_empty_source():
    row = _row()
    row["sample_id"] = "SMP-999"
    with pytest.raises(ValueError, match="ngoài view"):
        attach(_view(), [row], "offline-tool", "1.0")
    view = _view()
    view["samples"][0]["page_text"] = ""
    with pytest.raises(ValueError, match="page_text rỗng"):
        attach(view, [_row("")], "offline-tool", "1.0")
