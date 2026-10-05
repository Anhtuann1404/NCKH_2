#!/usr/bin/env python3
"""CLI nghiệm thu Pass 1: đo độ đồng thuận giữa Annotator A và Annotator B.

Công cụ đọc hai tệp JSONL (mỗi dòng một bản ghi gán nhãn mù), tính Cohen's Kappa
cho hai trường ``class_label`` và ``primary_org`` thông qua
``phishing.annotation.compute_cohens_kappa``, tổng hợp thời gian gán nhãn
(``seconds_spent``) của từng người (phân tách riêng phishing vs benign phục vụ PLAN-01),
liệt kê các ca bất đồng thuận, xác thực phiên gán nhãn/annotator/pass_id, rồi xuất báo
cáo Markdown (``--output``) và/hoặc JSON (``--json``).

Nguyên tắc NCKH:
    * Loại bỏ triệt để bản ghi mô phỏng/dry-run khỏi Kappa, thời gian và bất đồng thuận.
    * Không loại ca khó thật khỏi thống kê công sức chỉ vì không thuộc mẫu Kappa.
    * Xác thực phiên: annotator A và B phải phân biệt, pass_id=1, kiểm tra độ đầy đủ 32 ID
      khi nghiệm thu REAL-PILOT-32-V1.
    * Báo riêng thời gian phishing và benign để phục vụ chốt cỡ mẫu PLAN-01.
    * Đầu ra tất định (không gắn timestamp), tái lập được từ cùng đầu vào.

Cách dùng::

    python scripts/evaluate_kappa.py --rater-a a.jsonl --rater-b b.jsonl \
        --output reports/kappa.md --json reports/kappa.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import sys
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
ANNOTATOR_ID_FIELD = "annotator_id"
PASS_ID_FIELD = "pass_id"
IS_DRY_RUN_FIELD = "is_dry_run"

_DASH = "\u2014"  # em dash cho ô rỗng


# ---------------------------------------------------------------------------
# Đọc & lập chỉ mục dữ liệu
# ---------------------------------------------------------------------------
def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Đọc tệp JSONL, bỏ qua dòng trống, kiểm tra mỗi dòng là JSON object."""
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


def is_dry_run_record(record: dict[str, Any]) -> bool:
    """Xác định bản ghi mô phỏng/dry-run cần loại khỏi thống kê nghiên cứu."""
    if record.get(IS_DRY_RUN_FIELD) is True:
        return True
    if str(record.get(IS_DRY_RUN_FIELD, "")).lower() == "true":
        return True
    ann_id = str(record.get(ANNOTATOR_ID_FIELD, "")).strip()
    if ann_id.startswith("simulated_") or ann_id.lower() == "dryrun":
        return True
    return False


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
    """Tổng hợp thống kê ``seconds_spent`` (giây) trên một tập bản ghi thực tế.

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


def compute_timing_breakdown(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Tính toán thời gian tổng quan và phân tách riêng cho Phishing vs Benign phục vụ PLAN-01."""
    overall_stats = seconds_spent_stats(records)
    phish_records = [r for r in records if str(r.get(CLASS_LABEL_FIELD, "")).strip().lower() == "phishing"]
    benign_records = [r for r in records if str(r.get(CLASS_LABEL_FIELD, "")).strip().lower() == "benign"]

    phish_stats = seconds_spent_stats(phish_records)
    benign_stats = seconds_spent_stats(benign_records)

    return {
        "overall": overall_stats,
        "phishing": phish_stats,
        "benign": benign_stats,
        # Giữ tương thích ngược với các trường phẳng
        **overall_stats,
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


def validate_session_records(
    records: Sequence[dict[str, Any]],
    file_path: Path,
    expected_pass: int = 1,
    expected_annotator: str | None = None,
) -> set[str]:
    """Kiểm tra tính hợp lệ của phiên gán nhãn: pass_id và annotator_id."""
    annotators: set[str] = set()

    for idx, rec in enumerate(records):
        raw_pass = rec.get(PASS_ID_FIELD)
        if raw_pass is not None:
            try:
                pass_val = int(raw_pass)
            except (ValueError, TypeError) as err:
                raise ValueError(f"{file_path}: bản ghi #{idx} có pass_id không hợp lệ: {raw_pass}") from err
            if pass_val != expected_pass:
                raise ValueError(
                    f"{file_path}: bản ghi #{idx} có pass_id={pass_val} "
                    f"(kỳ vọng pass_id={expected_pass}). Tệp này không thuộc Pass {expected_pass}!"
                )

        ann = str(rec.get(ANNOTATOR_ID_FIELD, "")).strip()
        if ann:
            annotators.add(ann)

    if expected_annotator and annotators and expected_annotator not in annotators:
        raise ValueError(
            f"{file_path}: annotator_id tìm thấy là {annotators}, "
            f"không khớp với annotator kỳ vọng '{expected_annotator}'."
        )

    return annotators


def evaluate(
    rater_a_path: Path,
    rater_b_path: Path,
    *,
    require_provenance: bool = True,
    expected_pass: int = 1,
    expected_rater_a: str | None = "A",
    expected_rater_b: str | None = "B",
    verify_pilot_32: bool = False,
    pilot_manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Chạy toàn bộ nghiệm thu Pass 1 và trả về payload kết quả."""
    raw_records_a = load_jsonl(rater_a_path)
    raw_records_b = load_jsonl(rater_b_path)

    # 1. Loại bỏ các bản ghi mô phỏng/dry-run khỏi thống kê con người
    records_a = [r for r in raw_records_a if not is_dry_run_record(r)]
    records_b = [r for r in raw_records_b if not is_dry_run_record(r)]

    dry_run_count_a = len(raw_records_a) - len(records_a)
    dry_run_count_b = len(raw_records_b) - len(records_b)

    if not records_a or not records_b:
        raise ValueError("Không còn bản ghi gán nhãn thật nào sau khi loại bỏ dry-run/synthetic.")

    # 2. Xác thực phiên gán nhãn (Pass ID & Annotator ID)
    annotators_a = validate_session_records(records_a, rater_a_path, expected_pass, expected_rater_a)
    annotators_b = validate_session_records(records_b, rater_b_path, expected_pass, expected_rater_b)

    if annotators_a and annotators_b and annotators_a == annotators_b:
        raise ValueError(
            f"Cả hai tệp đều có cùng annotator_id: {annotators_a}. "
            "Nghiệm thu Pass 1 yêu cầu hai người đánh giá độc lập khác nhau (A và B)!"
        )

    # 3. Lập chỉ mục sample_id
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

    # 4. Kiểm tra nghiệm thu REAL-PILOT-32-V1 nếu được yêu cầu
    if verify_pilot_32:
        if len(shared_ids) != 32:
            raise ValueError(
                f"Nghiệm thu REAL-PILOT-32-V1 yêu cầu đủ 32 mẫu, nhưng nhận được {len(shared_ids)} mẫu."
            )
        expected_ids = {f"PILOT-{i:03d}" for i in range(1, 33)}
        missing_ids = expected_ids - ids_a
        if missing_ids:
            raise ValueError(
                f"Nghiệm thu REAL-PILOT-32-V1 thiếu các sample_id: {sorted(missing_ids)[:5]}..."
            )

    if pilot_manifest_path and pilot_manifest_path.is_file():
        with pilot_manifest_path.open("r", encoding="utf-8") as f:
            manifest_data = json.load(f)
            if manifest_data.get("acceptance", {}).get("D") != "approved":
                raise ValueError("Manifest pilot chưa được Lead D phê duyệt (acceptance.D != 'approved').")
            if not manifest_data.get("ready_for_annotation"):
                raise ValueError("Manifest pilot chưa ở trạng thái sẵn sàng (ready_for_annotation != true).")

    # 5. Đo Cohen's Kappa (tự động lọc random_subset bên trong)
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

    # 6. Thu thập bất đồng thuận (đã loại bỏ dry-run)
    disagreements = collect_disagreements(index_a, index_b, shared_ids)

    # 7. Thống kê thời gian (đã loại bỏ dry-run, tách riêng Phishing vs Benign phục vụ PLAN-01)
    timing_a = compute_timing_breakdown(records_a)
    timing_b = compute_timing_breakdown(records_b)

    return {
        "pass": PASS_NAME,
        "rater_a": {
            "file": str(rater_a_path),
            "record_count": len(records_a),
            "dry_run_excluded": dry_run_count_a,
            "annotator_id": sorted(annotators_a),
        },
        "rater_b": {
            "file": str(rater_b_path),
            "record_count": len(records_b),
            "dry_run_excluded": dry_run_count_b,
            "annotator_id": sorted(annotators_b),
        },
        "paired_sample_count": len(shared_ids),
        "kappa": {
            CLASS_LABEL_FIELD: kappa_result_to_dict(kappa_class),
            PRIMARY_ORG_FIELD: kappa_result_to_dict(kappa_org),
        },
        "seconds_spent": {
            "rater_a": timing_a,
            "rater_b": timing_b,
        },
        "disagreement_count": len(disagreements),
        "disagreements": disagreements,
        "pilot_32_verified": verify_pilot_32,
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
    out.append(f"- **Rater A**: `{rater_a['file']}` \u2014 {rater_a['record_count']} bản ghi hợp lệ ({rater_a['dry_run_excluded']} dry-run đã loại)")
    out.append(f"- **Rater B**: `{rater_b['file']}` \u2014 {rater_b['record_count']} bản ghi hợp lệ ({rater_b['dry_run_excluded']} dry-run đã loại)")
    out.append(f"- **Số mẫu ghép cặp**: {payload['paired_sample_count']}")
    out.append(f"- **Số ca bất đồng thuận**: {payload['disagreement_count']}")
    if payload.get("pilot_32_verified"):
        out.append("- **Xác thực REAL-PILOT-32-V1**: \u2705 Đủ 32/32 mẫu chuẩn.")
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

    out.append("## Thời gian gán nhãn (`seconds_spent`, giây) \u2014 Phục vụ PLAN-01")
    out.append("")
    out.append("| Rater | Phân nhóm | N hợp lệ | Thiếu | K.hợp lệ | Mean (s) | Median (s) | Min | Max | Total (s) |")
    out.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")

    for display_name, key in (("A", "rater_a"), ("B", "rater_b")):
        timing_data = payload["seconds_spent"][key]
        groups = [
            ("Toàn bộ", timing_data["overall"]),
            ("Phishing (PLAN-01)", timing_data["phishing"]),
            ("Benign", timing_data["benign"]),
        ]
        for grp_name, stats in groups:
            out.append(
                "| {rater} | {grp} | {count} | {missing} | {invalid} | {mean} | {median} | {min} | {max} | {total} |".format(
                    rater=display_name,
                    grp=grp_name,
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
            "thống kê seconds_spent (tách riêng phishing vs benign) và liệt kê bất đồng thuận giữa A và B."
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
        "--pass-id",
        type=int,
        default=1,
        help="ID lượt gán nhãn kỳ vọng (mặc định: 1 cho Pass 1).",
    )
    parser.add_argument(
        "--expected-rater-a",
        type=str,
        default="A",
        help="Annotator ID kỳ vọng cho tệp rater A (mặc định: 'A').",
    )
    parser.add_argument(
        "--expected-rater-b",
        type=str,
        default="B",
        help="Annotator ID kỳ vọng cho tệp rater B (mặc định: 'B').",
    )
    parser.add_argument(
        "--verify-pilot-32",
        action="store_true",
        help="Bật kiểm tra xác thực chặt chẽ gói REAL-PILOT-32-V1 (đủ 32 ID).",
    )
    parser.add_argument(
        "--pilot-manifest",
        type=Path,
        default=None,
        help="Đường dẫn pilot_manifest.json để xác thực trạng thái approved của Lead D.",
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
            expected_pass=args.pass_id,
            expected_rater_a=args.expected_rater_a,
            expected_rater_b=args.expected_rater_b,
            verify_pilot_32=args.verify_pilot_32,
            pilot_manifest_path=args.pilot_manifest,
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