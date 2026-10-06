"""Module chuẩn hóa mã tổ chức (primary_org) theo CODEBOOK_V1.md và dictionary_v1.json.

Tuân thủ nguyên tắc Academic Research Skills (ARS) và Ponytail Discipline:
- Quy tắc chuẩn hóa cố định: trim whitespace, chuẩn hóa Unicode (NFC), chữ thường (lowercase).
- Ánh xạ các tên gọi, bí danh (aliases), dịch vụ con (service_names) của 14 tổ chức về org_id chuẩn.
- Các tổ chức ngoài danh mục (outside_catalog) được giữ nguyên định danh độc lập, KHÔNG tự ý gộp.
- Áp dụng trên bản sao phân tích, tuyệt đối không sửa đổi JSONL gốc của annotators.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Sequence
import unicodedata

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DICTIONARY_PATH = PROJECT_ROOT / "configs" / "dictionary_v1.json"


def normalize_token(text: str | None) -> str:
    """Chuẩn hóa ký tự: strip whitespace, chuẩn hóa Unicode NFC, lowercase, bỏ dấu câu viền."""
    if text is None:
        return ""
    # Unicode NFC normalization
    norm = unicodedata.normalize("NFC", str(text)).strip().lower()
    # Loại bỏ dấu câu/ngoặc thừa ở đầu và cuối chuỗi
    norm = norm.strip("\"'.,;:!?-()[]{}")
    return norm


def build_org_alias_mapping(dictionary_path: Path = DEFAULT_DICTIONARY_PATH) -> dict[str, str]:
    """Xây dựng bảng tra cứu bí danh từ configs/dictionary_v1.json đã khóa.
    
    Trả về dict ánh xạ từ token chuẩn hóa -> org_id chính thức (1 trong 14 mã).
    """
    if not dictionary_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy tệp từ điển: {dictionary_path}")

    data = json.loads(dictionary_path.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}

    for org in data.get("organizations", []):
        org_id = org["org_id"]
        # 1. Bản thân org_id
        mapping[normalize_token(org_id)] = org_id

        # 2. display_name
        if "display_name" in org and org["display_name"]:
            mapping[normalize_token(org["display_name"])] = org_id

        # 3. aliases
        for alias in org.get("aliases", []):
            tok = normalize_token(alias)
            if tok:
                mapping[tok] = org_id

        # 4. service_names
        for svc in org.get("service_names", []):
            tok = normalize_token(svc)
            if tok:
                mapping[tok] = org_id

    return mapping


def normalize_primary_org(
    raw_org: str | None,
    alias_mapping: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Chuẩn hóa một nhãn tổ chức.
    
    Returns:
        tuple[normalized_org, catalog_status]:
            - (org_id, "in_catalog") nếu thuộc 14 tổ chức trong từ điển
            - (token, "outside_catalog") nếu là tổ chức ngoài danh mục
            - ("unknown", "unresolved") nếu rỗng, unknown, none, null
    """
    token = normalize_token(raw_org)

    if not token or token in {"unknown", "none", "null", "unresolved", "no_clear_target"}:
        return "unknown", "unresolved"

    if token == "multi_target":
        return "multi_target", "unresolved"

    if alias_mapping is not None and token in alias_mapping:
        return alias_mapping[token], "in_catalog"

    return token, "outside_catalog"


def compare_org_agreement(
    records_a: Sequence[dict[str, Any]],
    records_b: Sequence[dict[str, Any]],
    alias_mapping: dict[str, str] | None = None,
    require_provenance: bool = True,
) -> dict[str, Any]:
    """So sánh độ đồng thuận primary_org thô và sau chuẩn hóa giữa hai annotator.
    
    Không làm biến đổi bản ghi gốc.
    """
    from phishing.annotation import compute_cohens_kappa

    if alias_mapping is None:
        alias_mapping = build_org_alias_mapping()

    idx_a = {r["sample_id"]: r for r in records_a if not r.get("is_dry_run")}
    idx_b = {r["sample_id"]: r for r in records_b if not r.get("is_dry_run")}
    shared_ids = sorted(set(idx_a) & set(idx_b))

    raw_matches = 0
    normalized_matches = 0
    resolved_by_normalization: list[dict[str, Any]] = []
    persistent_disagreements: list[dict[str, Any]] = []

    clean_recs_a: list[dict[str, Any]] = []
    clean_recs_b: list[dict[str, Any]] = []

    for sid in shared_ids:
        ra = idx_a[sid]
        rb = idx_b[sid]

        raw_a = str(ra.get("primary_org", "unknown"))
        raw_b = str(rb.get("primary_org", "unknown"))

        norm_a, status_a = normalize_primary_org(raw_a, alias_mapping)
        norm_b, status_b = normalize_primary_org(raw_b, alias_mapping)

        # Bản sao để tính kappa chuẩn hóa
        copy_a = copy.deepcopy(ra)
        copy_a["primary_org"] = norm_a
        clean_recs_a.append(copy_a)

        copy_b = copy.deepcopy(rb)
        copy_b["primary_org"] = norm_b
        clean_recs_b.append(copy_b)

        raw_eq = (raw_a == raw_b)
        norm_eq = (norm_a == norm_b)

        if raw_eq:
            raw_matches += 1
        if norm_eq:
            normalized_matches += 1

        if not raw_eq and norm_eq:
            resolved_by_normalization.append({
                "sample_id": sid,
                "raw_a": raw_a,
                "raw_b": raw_b,
                "normalized": norm_a,
                "status": status_a,
            })
        elif not norm_eq:
            persistent_disagreements.append({
                "sample_id": sid,
                "raw_a": raw_a,
                "raw_b": raw_b,
                "norm_a": norm_a,
                "norm_b": norm_b,
                "status_a": status_a,
                "status_b": status_b,
            })

    # Tính Cohen's Kappa thô và sau chuẩn hóa
    kappa_raw = compute_cohens_kappa(
        records_a,
        records_b,
        label_field="primary_org",
        require_provenance=require_provenance,
    )
    kappa_norm = compute_cohens_kappa(
        clean_recs_a,
        clean_recs_b,
        label_field="primary_org",
        require_provenance=require_provenance,
    )

    return {
        "sample_count": len(shared_ids),
        "raw_agreement_count": raw_matches,
        "raw_observed_agreement": raw_matches / len(shared_ids) if shared_ids else 0.0,
        "raw_kappa": kappa_raw.kappa,
        "normalized_agreement_count": normalized_matches,
        "normalized_observed_agreement": normalized_matches / len(shared_ids) if shared_ids else 0.0,
        "normalized_kappa": kappa_norm.kappa,
        "resolved_by_normalization_count": len(resolved_by_normalization),
        "resolved_pairs": resolved_by_normalization,
        "persistent_disagreements_count": len(persistent_disagreements),
        "persistent_disagreements": persistent_disagreements,
    }
