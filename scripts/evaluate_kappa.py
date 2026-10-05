#!/usr/bin/env python3
"""CLI nghiệm thu Pass 1: đo độ đồng thuận giữa Annotator A và Annotator B.

Công cụ đọc hai tệp JSONL (mỗi dòng một bản ghi gán nhãn mù), tính Cohen's Kappa
cho hai trường ``class_label`` và ``primary_org`` thông qua
``phishing.annotation.compute_cohens_kappa``, tổng hợp thời gian gán nhãn
(``seconds_spent``) của từng người, liệt kê các ca bất đồng thuận, rồi xuất báo
cáo Markdown (``--output``) và/hoặc JSON (``--json``).

Nguyên tắc NCKH:
    * Script chỉ *đánh giá* độ đồng thuận, không trích xuất đặc trưng và không
      dùng nhãn nguồn (target/label/metadata) làm đầu vào mô hình.
    * Cảnh báo và từ chối chạy khi tập ``sample_id`` giữa hai rater không khớp
      (chống ghép sai cặp gây sai lệch Kappa).
    * Đầu ra tất định (không gắn timestamp), tái lập được từ cùng đầu vào.

Cách dùng::

    python scripts/evaluate_kappa.py --rater-a a.jsonl --rater-b b.jsonl \
        --output reports/kappa.md --json reports/kappa.json
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any, Sequence

# Đảm bảo mã hóa UTF-8 an toàn trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Thêm src vào sys.path để import phishing
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from phishing.annotation import KappaResult, compute_cohens_kappa

# ---------------------------------------------------------------------------
# Hằng số cấu hình
# ---------------------------------------------------------------------------
PASS_NAME = "pass1"
SAMPLE_ID_FIELD = "sample_id"
CLASS_LABEL_FIELD = "class_label"
PRIMARY_ORG_FIELD = "primary_org"
SECONDS_SPENT_FIELD = "seconds_spent"
EVIDENCE_NOTE_FIELD = "evidence_note"

_DASH = "\u2014"  # em dash cho ô rỗng


# ---------------------------------------------------------------------------
# Đọc & lập chỉ mục dữ liệu
# ---------------------------------------------------------------------------
def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Đọc tệp JSONL, bỏ qua dòng trống, kiểm tra mỗi dòng là JSON object.

    Raises:
        FileNotFoundError: Nếu tệp không tồn tại.
        ValueError: Nếu có dòng không phải JSON object hoặc tệp rỗng.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy tệp JSONL: {path}")

    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for lineno, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno}: JSON không hợp lệ ({exc}).") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{lineno}: mỗi dòng phải là một JSON object.")
            records.append(obj)

    if not records:
        raise ValueError(f"Tệp JSONL không có bản ghi hợp lệ: {path}")
    return records


def index_by_sample_id(
    records: Sequence[dict[str, Any]], source: str
) -> dict[str, dict[str, Any]]:
    """Lập chỉ mục bản ghi theo ``sample_id``, phát hiện thiếu id và trùng lặp."""
    indexed: dict[str, dict[str, Any]] = {}
    for position, record in enumerate(records):
        raw_sid = record.get(SAMPLE_ID_FIELD)
        sid = str(raw_sid).strip() if raw_sid is not None else ""
        if not sid:
            raise ValueError(
                f"{source}: bản ghi #{position} thiếu hoặc rỗng '{SAMPLE_ID_FIELD}'."
            )
        if sid in indexed:
            raise ValueError(f"{source}: trùng lặp '{SAMPLE_ID_FIELD}': {sid!r}.")
        indexed[sid] = record
    return indexed


# ---------------------------------------------------------------------------
# Thống kê thời gian gán nhãn
# ---------------------------------------------------------------------------
def seconds_spent_stats(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Tổng hợp thống kê ``seconds_spent`` (giây) trên một tập bản ghi.

    Giá trị thiếu, không phải số, không hữu hạn hoặc âm được đếm riêng và loại
    khỏi các phép tính mean/median/min/max/total.
    """
    values: list[float] = []
    missing = 0
    invalid = 0

    for record in records:
        raw = record.get(SECONDS_SPENT_FIELD)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            missing += 1
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            invalid += 1
            continue
        if not math.isfinite(value) or value < 0:
            invalid += 1
            continue
        values.append(value)

    if not values:
        return {
            "count": 0,
            "missing": missing,
            "invalid": invalid,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "total": None,
        }

    return {
        "count": len(values),
        "missing": missing,
        "invalid": invalid,
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "total": sum(values),
    }


# ---------------------------------------------------------------------------
# Kappa & bất đồng thuận
# ---------------------------------------------------------------------------
def kappa_result_to_dict(result: KappaResult) -> dict[str, Any]:
    """Chuyển ``KappaResult`` (dataclass) thành dict JSON-serializable."""
    return {
        "kappa": result.kappa,
        "observed_agreement": result.observed_agreement,
        "expected_agreement": result.expected_agreement,
        "status": result.status,
        "sample_count": result.sample_count,
        "categories": list(result.categories),
    }


def _normalize(value: Any) -> str | None:
    """Chuẩn hóa giá trị về chuỗi đã strip; trả ``None`` nếu rỗng/thiếu."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def collect_disagreements(
    index_a: dict[str, dict[str, Any]],
    index_b: dict[str, dict[str, Any]],
    shared_ids: Sequence[str],
) -> list[dict[str, Any]]:
    """Liệt kê các ca bất đồng thuận theo thứ tự ``sample_id`` đã sắp xếp."""
    disagreements: list[dict[str, Any]] = []

    for sid in shared_ids:
        rec_a = index_a[sid]
        rec_b = index_b[sid]

        label_a = _normalize(rec_a.get(CLASS_LABEL_FIELD))
        label_b = _normalize(rec_b.get(CLASS_LABEL_FIELD))
        org_a = _normalize(rec_a.get(PRIMARY_ORG_FIELD))
        org_b = _normalize(rec_b.get(PRIMARY_ORG_FIELD))

        fields: list[str] = []
        if label_a != label_b:
            fields.append(CLASS_LABEL_FIELD)
        if org_a != org_b:
            fields.append(PRIMARY_ORG_FIELD)
        if not fields:
            continue

        disagreements.append(
            {
                "sample_id": sid,
                "label_a": label_a,
                "label_b": label_b,
                "org_a": org_a,
                "org_b": org_b,
                "disagreement_fields": fields,
                "evidence_note_a": _normalize(rec_a.get(EVIDENCE_NOTE_FIELD)),
                "evidence_note_b": _normalize(rec_b.get(EVIDENCE_NOTE_FIELD)),
            }
        )

    return disagreements


# ---------------------------------------------------------------------------
# Luồng đánh giá chính
# ---------------------------------------------------------------------------
def _preview(items: Sequence[str], limit: int = 5) -> str:
    """Rút gọn danh sách id để đưa vào thông báo lỗi."""
    head = list(items[:limit])
    if not head:
        return _DASH
    suffix = ", ..." if len(items) > limit else ""
    return ", ".join(head) + suffix


def evaluate(
    rater_a_path: Path,
    rater_b_path: Path,
    *,
    require_provenance: bool = True,
) -> dict[str, Any]:
    """Chạy toàn bộ nghiệm thu Pass 1 và trả về payload kết quả."""
    records_a = load_jsonl(rater_a_path)
    records_b = load_jsonl(rater_b_path)

    index_a = index_by_sample_id(records_a, str(rater_a_path))
    index_b = index_by_sample_id(records_b, str(rater_b_path))

    ids_a = set(index_a)
    ids_b = set(index_b)
    if ids_a != ids_b:
        only_a = sorted(ids_a - ids_b)
        only_b = sorted(ids_b - ids_a)
        raise ValueError(
            "Tập sample_id giữa hai rater không khớp: "
            f"{len(only_a)} chỉ có ở A ({_preview(only_a)}), "
            f"{len(only_b)} chỉ có ở B ({_preview(only_b)})."
        )
    shared_ids = sorted(ids_a)

    kappa_class = compute_cohens_kappa(
        records_a,
        records_b,
        label_field=CLASS_LABEL_FIELD,
        require_provenance=require_provenance,
    )
    kappa_org = compute_cohens_kappa(
        records_a,
        records_b,
        label_field=PRIMARY_ORG_FIELD,
        require_provenance=require_provenance,
    )

    disagreements = collect_disagreements(index_a, index_b, shared_ids)

    return {
        "pass": PASS_NAME,
        "rater_a": {"file": str(rater_a_path), "record_count": len(records_a)},
        "rater_b": {"file": str(rater_b_path), "record_count": len(records_b)},
        "paired_sample_count": len(shared_ids),
        "kappa": {
            CLASS_LABEL_FIELD: kappa_result_to_dict(kappa_class),
            PRIMARY_ORG_FIELD: kappa_result_to_dict(kappa_org),
        },
        "seconds_spent": {
            "rater_a": seconds_spent_stats(records_a),
            "rater_b": seconds_spent_stats(records_b),
        },
        "disagreement_count": len(disagreements),
        "disagreements": disagreements,
    }


# ---------------------------------------------------------------------------
# Kết xuất báo cáo
# ---------------------------------------------------------------------------
def _fmt_float(value: Any, digits: int) -> str:
    """Định dạng số thực với số chữ số cố định; trả dấu gạch nếu thiếu."""
    if value is None:
        return _DASH
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return _md_cell(value)
    number = float(value)
    if not math.isfinite(number):
        return _DASH
    return f"{number:.{digits}f}"


def _md_cell(value: Any) -> str:
    """Chuẩn hóa một ô bảng Markdown (thoát pipe, gộp dòng)."""
    if value is None:
        return _DASH
    text = str(value).replace("|", "\\|").replace("\n", " ").strip()
    return text or _DASH


def build_markdown(payload: dict[str, Any]) -> str:
    """Sinh báo cáo Markdown từ payload kết quả."""
    rater_a = payload["rater_a"]
    rater_b = payload["rater_b"]

    out: list[str] = []
    out.append("# Nghiệm thu Pass 1 \u2014 Đồng thuận liên đánh giá viên")
    out.append("")
    out.append(f"- **Rater A**: `{rater_a['file']}` \u2014 {rater_a['record_count']} bản ghi")
    out.append(f"- **Rater B**: `{rater_b['file']}` \u2014 {rater_b['record_count']} bản ghi")
    out.append(f"- **Số mẫu ghép cặp**: {payload['paired_sample_count']}")
    out.append(f"- **Số ca bất đồng thuận**: {payload['disagreement_count']}")
    out.append("")

    for field_key in (CLASS_LABEL_FIELD, PRIMARY_ORG_FIELD):
        block = payload["kappa"][field_key]
        categories = ", ".join(block["categories"]) if block["categories"] else _DASH
        out.append(f"## Cohen's Kappa \u2014 `{field_key}`")
        out.append("")
        out.append("| Chỉ số | Giá trị |")
        out.append("| --- | --- |")
        out.append(f"| Kappa | {_fmt_float(block['kappa'], 4)} |")
        out.append(f"| P_o (đồng thuận quan sát) | {_fmt_float(block['observed_agreement'], 4)} |")
        out.append(f"| P_e (kỳ vọng ngẫu nhiên) | {_fmt_float(block['expected_agreement'], 4)} |")
        out.append(f"| Trạng thái | {_md_cell(block['status'])} |")
        out.append(f"| Số mẫu | {block['sample_count']} |")
        out.append(f"| Danh mục | {_md_cell(categories)} |")
        out.append("")

    out.append("## Thời gian gán nhãn (`seconds_spent`, giây)")
    out.append("")
    out.append("| Rater | N hợp lệ | Thiếu | Không hợp lệ | Mean | Median | Min | Max | Total |")
    out.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for display_name, key in (("A", "rater_a"), ("B", "rater_b")):
        stats = payload["seconds_spent"][key]
        out.append(
            "| {name} | {count} | {missing} | {invalid} | {mean} | {median} | {min} | {max} | {total} |".format(
                name=display_name,
                count=stats["count"],
                missing=stats["missing"],
                invalid=stats["invalid"],
                mean=_fmt_float(stats["mean"], 2),
                median=_fmt_float(stats["median"], 2),
                min=_fmt_float(stats["min"], 2),
                max=_fmt_float(stats["max"], 2),
                total=_fmt_float(stats["total"], 2),
            )
        )
    out.append("")

    out.append(f"## Bất đồng thuận ({payload['disagreement_count']})")
    out.append("")
    if not payload["disagreements"]:
        out.append("_Không có ca bất đồng thuận nào._")
        out.append("")
        return "\n".join(out).rstrip() + "\n"

    out.append(
        "| sample_id | Nhãn A | Nhãn B | Tổ chức A | Tổ chức B | Trường lệch | Evidence A | Evidence B |"
    )
    out.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for item in payload["disagreements"]:
        fields = ", ".join(item["disagreement_fields"])
        out.append(
            "| {sid} | {la} | {lb} | {oa} | {ob} | {fields} | {ea} | {eb} |".format(
                sid=_md_cell(item["sample_id"]),
                la=_md_cell(item["label_a"]),
                lb=_md_cell(item["label_b"]),
                oa=_md_cell(item["org_a"]),
                ob=_md_cell(item["org_b"]),
                fields=_md_cell(fields),
                ea=_md_cell(item["evidence_note_a"]),
                eb=_md_cell(item["evidence_note_b"]),
            )
        )
    out.append("")
    return "\n".join(out).rstrip() + "\n"


def _write_text(path: Path, content: str) -> None:
    """Ghi nội dung văn bản, tự tạo thư mục cha nếu cần."""
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Khởi tạo bộ phân tích tham số dòng lệnh."""
    parser = argparse.ArgumentParser(
        prog="evaluate_kappa.py",
        description=(
            "Nghiệm thu Pass 1: tính Cohen's Kappa (class_label, primary_org), "
            "thống kê seconds_spent và liệt kê bất đồng thuận giữa Annotator A và B."
        ),
    )
    parser.add_argument(
        "--rater-a",
        required=True,
        type=Path,
        help="Tệp JSONL nhãn của Annotator A.",
    )
    parser.add_argument(
        "--rater-b",
        required=True,
        type=Path,
        help="Tệp JSONL nhãn của Annotator B.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Đường dẫn tệp báo cáo Markdown (tùy chọn).",
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        type=Path,
        default=None,
        help="Đường dẫn tệp JSON kết quả (tùy chọn).",
    )
    parser.add_argument(
        "--require-provenance",
        dest="require_provenance",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Bắt buộc đầy đủ 6 trường provenance khi tính Kappa "
            "(mặc định: bật; dùng --no-require-provenance để tắt)."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Điểm vào CLI. Trả về mã thoát (0 thành công, 2 lỗi đầu vào)."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload = evaluate(
            args.rater_a,
            args.rater_b,
            require_provenance=args.require_provenance,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"[evaluate_kappa] LỖI: {exc}", file=sys.stderr)
        return 2

    markdown = build_markdown(payload)

    if args.output is not None:
        _write_text(args.output, markdown)
    if args.json_path is not None:
        _write_text(
            args.json_path,
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        )

    if args.output is None and args.json_path is None:
        print(markdown, end="")
    else:
        print(
            "[evaluate_kappa] Hoàn tất: "
            f"{payload['paired_sample_count']} mẫu ghép cặp, "
            f"{payload['disagreement_count']} ca bất đồng thuận."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())