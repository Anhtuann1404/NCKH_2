"""Unit tests cho module chuẩn hóa mã tổ chức (org_normalization).

Toàn bộ test sử dụng dữ liệu giả lập (synthetic fixtures), không chứa dữ liệu thật.
"""

from pathlib import Path
import pytest

from phishing.annotation.org_normalization import (
    build_org_alias_mapping,
    compare_org_agreement,
    normalize_primary_org,
    normalize_token,
)


def test_normalize_token_basic():
    assert normalize_token("  Microsoft  ") == "microsoft"
    assert normalize_token("FaceBook!") == "facebook"
    assert normalize_token("\"Google\"") == "google"
    assert normalize_token(None) == ""
    assert normalize_token("  ") == ""


def test_build_org_alias_mapping_and_dictionary_coverage():
    mapping = build_org_alias_mapping()
    assert isinstance(mapping, dict)
    assert len(mapping) > 20

    # Kiểm tra các tổ chức chính trong 14 mã
    assert mapping["microsoft"] == "microsoft"
    assert mapping["google"] == "google"
    assert mapping["facebook"] == "meta"
    assert mapping["instagram"] == "meta"
    assert mapping["whatsapp"] == "meta"
    assert mapping["office 365"] == "microsoft"
    assert mapping["msft"] == "microsoft"
    assert mapping["agoda"] == "booking"
    assert mapping["booking.com"] == "booking"
    assert mapping["twitter"] == "x_twitter"
    assert mapping["x"] == "x_twitter"
    assert mapping["paypal"] == "paypal"
    assert mapping["apple pay"] == "apple"


def test_normalize_primary_org_in_and_outside_catalog():
    mapping = build_org_alias_mapping()

    # 1. In catalog
    norm, status = normalize_primary_org("  Microsoft Corporation  ", mapping)
    assert norm == "microsoft"
    assert status == "in_catalog"

    norm, status = normalize_primary_org("FaceBook", mapping)
    assert norm == "meta"
    assert status == "in_catalog"

    norm, status = normalize_primary_org("Office 365", mapping)
    assert norm == "microsoft"
    assert status == "in_catalog"

    # 2. Outside catalog (không gộp bừa bãi, giữ nguyên định danh độc lập)
    norm, status = normalize_primary_org("Garena", mapping)
    assert norm == "garena"
    assert status == "outside_catalog"

    norm, status = normalize_primary_org("  Coinbase! ", mapping)
    assert norm == "coinbase"
    assert status == "outside_catalog"

    norm, status = normalize_primary_org("Robinhood", mapping)
    assert norm == "robinhood"
    assert status == "outside_catalog"

    # 3. Unknown / Unresolved
    for unk in ["", "unknown", "None", None, "no_clear_target", "null"]:
        norm, status = normalize_primary_org(unk, mapping)
        assert norm == "unknown"
        assert status == "unresolved"


def test_compare_org_agreement_synthetic():
    """Kiểm tra đo lường so sánh kappa thô vs sau chuẩn hóa trên synthetic fixture."""
    mapping = build_org_alias_mapping()

    # Tạo 4 mẫu giả lập
    # Mẫu 1: Đồng thuận ngay từ đầu (microsoft vs microsoft)
    # Mẫu 2: Biến thể cách viết (Facebook vs Meta) -> lệch thô, trùng sau chuẩn hóa
    # Mẫu 3: Bất đồng thật sự (Google vs Apple)
    # Mẫu 4: Cùng outside catalog (Garena vs garena) -> lệch thô (hoa/thường), trùng sau chuẩn hóa
    records_a = [
        {"sample_id": "S1", "primary_org": "microsoft", "class_label": "phishing"},
        {"sample_id": "S2", "primary_org": "Facebook", "class_label": "phishing"},
        {"sample_id": "S3", "primary_org": "google", "class_label": "phishing"},
        {"sample_id": "S4", "primary_org": "Garena", "class_label": "phishing"},
    ]
    records_b = [
        {"sample_id": "S1", "primary_org": "microsoft", "class_label": "phishing"},
        {"sample_id": "S2", "primary_org": "meta", "class_label": "phishing"},
        {"sample_id": "S3", "primary_org": "apple", "class_label": "phishing"},
        {"sample_id": "S4", "primary_org": "garena", "class_label": "phishing"},
    ]

    res = compare_org_agreement(records_a, records_b, mapping, require_provenance=False)

    assert res["sample_count"] == 4
    # Thô: chỉ S1 trùng hoàn toàn (1/4)
    assert res["raw_agreement_count"] == 1
    # Sau chuẩn hóa: S1 (microsoft), S2 (meta), S4 (garena) trùng (3/4)
    assert res["normalized_agreement_count"] == 3
    assert res["resolved_by_normalization_count"] == 2
    assert res["persistent_disagreements_count"] == 1
    assert res["persistent_disagreements"][0]["sample_id"] == "S3"

    # Đảm bảo bản ghi gốc không bị sửa đổi (immutability)
    assert records_a[1]["primary_org"] == "Facebook"
    assert records_a[3]["primary_org"] == "Garena"
