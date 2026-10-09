"""Module data: Quản lý nạp dữ liệu, kiểm tra tính toàn vẹn (SHA-256), chuẩn hóa URL và eTLD+1."""

from typing import Dict, Any

from phishing.data.grouping import extract_group_id
from phishing.data.loader import (
    CorpusRecord,
    build_corpus_index,
    extract_labels_vault,
    load_phishvn_records,
    load_phreshphish_shard,
    normalize_record_url,
)
from phishing.data.difficulty_strata import (
    DIFFICULTY_RULES,
    count_surface_cooccurrences,
    evaluate_difficulty_flags,
    has_cooccurring_surface_indicators,
    is_composite_ambiguous_case,
    is_hard_case,
)
from phishing.data.splits import (
    DEFAULT_SEEDS,
    assert_no_group_leakage,
    assert_strict_temporal_order,
    generate_grouped_kfold,
    generate_temporal_split,
)

__all__ = [
    "DIFFICULTY_RULES",
    "evaluate_difficulty_flags",
    "is_hard_case",
    "is_composite_ambiguous_case",
    "count_surface_cooccurrences",
    "has_cooccurring_surface_indicators",
    "verify_sha256",
    "extract_group_id",
    "generate_grouped_kfold",
    "generate_temporal_split",
    "assert_no_group_leakage",
    "assert_strict_temporal_order",
    "DEFAULT_SEEDS",
    "CorpusRecord",
    "normalize_record_url",
    "load_phreshphish_shard",
    "load_phishvn_records",
    "build_corpus_index",
    "extract_labels_vault",
]


def verify_sha256(file_path: str, expected_hash: str, *, normalize_newlines: bool = True) -> bool:
    """Xác thực mã băm SHA-256 của một file dữ liệu.

    Với các tệp cấu hình JSON/văn bản, chuẩn hóa ký tự xuống dòng (LF) để đảm bảo
    mã băm bất biến trên đa nền tảng (Windows CRLF vs Linux/macOS LF).
    """
    import hashlib
    with open(file_path, "rb") as f:
        data = f.read()
    if normalize_newlines and file_path.endswith((".json", ".txt", ".md", ".py")):
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest().lower() == expected_hash.lower()
