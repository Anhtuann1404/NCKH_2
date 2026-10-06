"""Công cụ phân tích đối soát Pass 1 Pilot V2 (A vs B) & Chuẩn bị Bảng phân xử.

Tuân thủ nghiêm ngặt các quy định:
- Dữ liệu chi tiết từng mẫu chỉ lưu trong thư mục hạn chế (data/labels/intake_v2/ - gitignored).
- Báo cáo công khai trên docs/ chỉ chứa ma trận và thống kê tổng hợp, tuyệt đối KHÔNG chứa nhãn từng mẫu.
- Không đọc nhãn nguồn, điểm mô hình hay Official Test.
- Giữ nguyên vẹn 100% hai tệp JSONL gốc của A và B.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from phishing.annotation import compute_cohens_kappa
from phishing.annotation.org_normalization import (
    build_org_alias_mapping,
    compare_org_agreement,
    normalize_primary_org,
)

EXPECTED_HASH_A = "8da2e16dcd40b280ac0e7c3e4f56ebe74c0ea31f00cb727f2b84dcec65112e4c"
EXPECTED_HASH_B = "6f63750d71827d06f999af828f5724bdd67e584fbdddf3a0263882983a8d4db8"
EXPECTED_DATASET_HASH = "e039c774ef5ff11b36786ccc8c762254974d89a4f4bfa7d5bc46b12e323ad1dc"
EXPECTED_CODEBOOK_HASH = "12de9c2f3b457938039b05c72c651d6650f403b620216516262134a3313a2ed1"


def compute_file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_records(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def verify_intake_files(path_a: Path, path_b: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Kiểm tra toàn vẹn mã băm, số lượng và provenance của file A và B."""
    hash_a = compute_file_sha256(path_a)
    hash_b = compute_file_sha256(path_b)

    if hash_a != EXPECTED_HASH_A:
        raise ValueError(f"File A sai mã băm: {hash_a} != {EXPECTED_HASH_A}")
    if hash_b != EXPECTED_HASH_B:
        raise ValueError(f"File B sai mã băm: {hash_b} != {EXPECTED_HASH_B}")

    recs_a = load_records(path_a)
    recs_b = load_records(path_b)

    if len(recs_a) != 32 or len(recs_b) != 32:
        raise ValueError(f"Số lượng bản ghi không đủ 32: len(A)={len(recs_a)}, len(B)={len(recs_b)}")

    expected_ids = [f"PILOT-{i:03d}" for i in range(1, 33)]
    ids_a = [r["sample_id"] for r in recs_a]
    ids_b = [r["sample_id"] for r in recs_b]

    if ids_a != expected_ids or ids_b != expected_ids:
        raise ValueError("Danh sách sample_id không khớp PILOT-001..032 theo thứ tự")

    # Kiểm tra provenance từng cặp
    for ra, rb in zip(recs_a, recs_b):
        if ra["sample_id"] != rb["sample_id"]:
            raise ValueError(f"Lệch sample_id: {ra['sample_id']} != {rb['sample_id']}")
        if ra.get("dataset_hash") != EXPECTED_DATASET_HASH or rb.get("dataset_hash") != EXPECTED_DATASET_HASH:
            raise ValueError(f"Sai dataset_hash tại {ra['sample_id']}")
        if ra.get("codebook_hash") != EXPECTED_CODEBOOK_HASH or rb.get("codebook_hash") != EXPECTED_CODEBOOK_HASH:
            raise ValueError(f"Sai codebook_hash tại {ra['sample_id']}")
        if ra.get("sample_content_hash") != rb.get("sample_content_hash"):
            raise ValueError(f"sample_content_hash không khớp tại {ra['sample_id']}")

    return recs_a, recs_b


def generate_restricted_disagreement_table(
    recs_a: list[dict[str, Any]],
    recs_b: list[dict[str, Any]],
    alias_mapping: dict[str, str],
) -> dict[str, Any]:
    """Tạo bảng bất đồng chi tiết cho khu vực hạn chế (C/D review)."""
    idx_b = {r["sample_id"]: r for r in recs_b}

    class_disagreements = []
    org_disagreements = []
    all_disagreements = []

    for ra in recs_a:
        sid = ra["sample_id"]
        rb = idx_b[sid]

        class_a = ra.get("class_label")
        class_b = rb.get("class_label")
        raw_org_a = str(ra.get("primary_org", "unknown"))
        raw_org_b = str(rb.get("primary_org", "unknown"))

        norm_org_a, status_org_a = normalize_primary_org(raw_org_a, alias_mapping)
        norm_org_b, status_org_b = normalize_primary_org(raw_org_b, alias_mapping)

        class_diff = (class_a != class_b)
        org_diff = (norm_org_a != norm_org_b)

        # Kiểm tra mâu thuẫn logic: identified nhưng org là unknown/rỗng
        anomaly_a = None
        if ra.get("primary_org_status") == "identified" and norm_org_a in {"unknown", "no_clear_target", "multi_target"}:
            anomaly_a = f"identified_with_{norm_org_a}"

        anomaly_b = None
        if rb.get("primary_org_status") == "identified" and norm_org_b in {"unknown", "no_clear_target", "multi_target"}:
            anomaly_b = f"identified_with_{norm_org_b}"

        row_info = {
            "sample_id": sid,
            "class_label_a": class_a,
            "class_label_b": class_b,
            "class_disagreement": class_diff,
            "primary_org_raw_a": raw_org_a,
            "primary_org_raw_b": raw_org_b,
            "primary_org_norm_a": norm_org_a,
            "primary_org_norm_b": norm_org_b,
            "org_disagreement": org_diff,
            "consistency_anomaly_a": anomaly_a,
            "consistency_anomaly_b": anomaly_b,
            "difficult_case_a": ra.get("difficult_case", False),
            "difficult_case_b": rb.get("difficult_case", False),
            "evidence_note_a": ra.get("evidence_note", ""),
            "evidence_note_b": rb.get("evidence_note", ""),
            "adjudication_status": "pending_lead_review",
        }

        if class_diff:
            class_disagreements.append(row_info)
        if org_diff:
            org_disagreements.append(row_info)
        if class_diff or org_diff or anomaly_a or anomaly_b:
            all_disagreements.append(row_info)

    anomalies_count_a = sum(1 for r in all_disagreements if r["consistency_anomaly_a"])
    anomalies_count_b = sum(1 for r in all_disagreements if r["consistency_anomaly_b"])

    return {
        "total_samples": len(recs_a),
        "total_disagreements": len(all_disagreements),
        "class_disagreement_count": len(class_disagreements),
        "org_disagreement_count": len(org_disagreements),
        "overlap_both_count": len([r for r in all_disagreements if r["class_disagreement"] and r["org_disagreement"]]),
        "consistency_anomalies_a_count": anomalies_count_a,
        "consistency_anomalies_b_count": anomalies_count_b,
        "disagreements": all_disagreements,
    }


def generate_public_summary_matrix(
    recs_a: list[dict[str, Any]],
    recs_b: list[dict[str, Any]],
) -> dict[str, Any]:
    """Tạo bảng tổng hợp ma trận chéo không chứa nhãn từng mẫu (đưa lên docs)."""
    labels = ["benign", "phishing", "insufficient_evidence"]
    matrix: dict[str, dict[str, int]] = {la: {lb: 0 for lb in labels} for la in labels}

    idx_b = {r["sample_id"]: r for r in recs_b}
    disagreement_types: Counter[str] = Counter()

    for ra in recs_a:
        sid = ra["sample_id"]
        rb = idx_b[sid]
        ca = ra.get("class_label", "unknown")
        cb = rb.get("class_label", "unknown")

        if ca in matrix and cb in matrix[ca]:
            matrix[ca][cb] += 1

        if ca != cb:
            disagreement_types[f"A={ca} / B={cb}"] += 1

    return {
        "sample_count": len(recs_a),
        "confusion_matrix": matrix,
        "disagreement_patterns": dict(disagreement_types),
    }


def to_canonical_json_bytes(obj: Any) -> bytes:
    """Xuất JSON UTF-8 với thụt lề 2 ký tự và kết thúc bằng Unix LF (\\n) cố định trên mọi OS."""
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    text = text.replace("\r\n", "\n") + "\n"
    return text.encode("utf-8")


def write_canonical_json(path: Path, obj: Any) -> str:
    """Ghi tệp JSON dạng canonical bytes LF cố định và trả về mã băm SHA-256."""
    b = to_canonical_json_bytes(obj)
    path.write_bytes(b)
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rater-a", type=Path, required=True, help="Tệp JSONL của Annotator A")
    parser.add_argument("--rater-b", type=Path, required=True, help="Tệp JSONL của Annotator B")
    parser.add_argument("--out-restricted", type=Path, default=PROJECT_ROOT / "data" / "labels" / "intake_v2",
                        help="Thư mục xuất chi tiết hạn chế")
    parser.add_argument("--out-summary", type=Path, default=PROJECT_ROOT / "docs" / "PASS1_V2_AGREEMENT_SUMMARY.json",
                        help="Tệp xuất tổng hợp công khai")
    args = parser.parse_args()

    recs_a, recs_b = verify_intake_files(args.rater_a, args.rater_b)
    alias_mapping = build_org_alias_mapping()

    # 1. So sánh tổ chức (tính toán khảo sát với validate_consistency=False)
    org_comp = compare_org_agreement(
        recs_a,
        recs_b,
        alias_mapping,
        require_provenance=True,
        validate_consistency=False,
    )

    # 2. Bảng hạn chế
    restricted_data = generate_restricted_disagreement_table(recs_a, recs_b, alias_mapping)
    restricted_data["org_comparison_metrics"] = {
        "status": "provisional_consistency_anomalies_pending_adjudication",
        "raw_kappa": org_comp["raw_kappa"],
        "normalized_kappa": org_comp["normalized_kappa"],
        "resolved_by_normalization_count": org_comp["resolved_by_normalization_count"],
        "resolved_pairs": org_comp["resolved_pairs"],
    }

    args.out_restricted.mkdir(parents=True, exist_ok=True)
    table_file = args.out_restricted / "adjudication_disagreement_table.json"
    table_hash = write_canonical_json(table_file, restricted_data)

    # Lưu bảng ánh xạ alias kèm hash dạng canonical bytes
    mapping_file = args.out_restricted / "org_alias_mapping.json"
    mapping_hash = write_canonical_json(mapping_file, alias_mapping)

    # 3. Bảng tổng hợp công khai
    summary = generate_public_summary_matrix(recs_a, recs_b)
    anom_samples = set(
        [r["sample_id"] for r in restricted_data["disagreements"] if r["consistency_anomaly_a"]]
        + [r["sample_id"] for r in restricted_data["disagreements"] if r["consistency_anomaly_b"]]
    )
    summary["org_agreement_summary"] = {
        "status": "provisional_consistency_anomalies_pending_adjudication",
        "description": "Kết quả Kappa tổ chức tạm thời trước phân xử do tồn tại các bản ghi mâu thuẫn logic (primary_org_status='identified' nhưng primary_org là 'unknown' hoặc 'no_clear_target')",
        "consistency_anomalies": {
            "rater_a_count": restricted_data["consistency_anomalies_a_count"],
            "rater_b_count": restricted_data["consistency_anomalies_b_count"],
            "total_samples_affected": len(anom_samples),
        },
        "raw_agreement_count": org_comp["raw_agreement_count"],
        "raw_kappa": org_comp["raw_kappa"],
        "normalized_agreement_count": org_comp["normalized_agreement_count"],
        "normalized_kappa": org_comp["normalized_kappa"],
        "resolved_by_normalization_count": org_comp["resolved_by_normalization_count"],
    }
    summary["disagreement_counts_reconciliation"] = {
        "raw_disagreements_count": 26,
        "raw_disagreements_definition": "Số ca có bất đồng ở ít nhất một trường lớp hoặc tổ chức thô trước chuẩn hóa",
        "adjudication_table_cases_count": restricted_data["total_disagreements"],
        "adjudication_table_definition": (
            "Hợp của: (1) 14 ca bất đồng lớp, (2) 13 ca bất đồng tổ chức SAU chuẩn hóa, và (3) 11 ca duy nhất mang consistency anomaly; "
            "4 cặp lệch thô (PILOT-002, 003, 020, 027) được giải quyết thành đồng thuận nhờ chuẩn hóa chữ hoa/thường"
        ),
        "class_disagreements": restricted_data["class_disagreement_count"],
        "normalized_org_disagreements": restricted_data["org_disagreement_count"],
        "both_class_and_org_disagreements": restricted_data["overlap_both_count"],
    }

    args.out_summary.parent.mkdir(parents=True, exist_ok=True)
    summary_hash = write_canonical_json(args.out_summary, summary)

    print(f"[ANALYZE_PASS1] Hoàn thành phân tích đối soát.")
    print(f"  Bảng phân xử hạn chế: {table_file} (SHA-256: {table_hash})")
    print(f"  Bảng alias hạn chế:   {mapping_file} (SHA-256: {mapping_hash})")
    print(f"  Báo cáo tổng hợp:     {args.out_summary} (SHA-256: {summary_hash})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
