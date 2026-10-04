"""Module annotation: Xuất view gán nhãn mù an toàn, tính chỉ số Cohen's Kappa, và quản lý exclusion registry."""

from dataclasses import dataclass
from typing import Any, List, Literal, Optional, Sequence

from .blind_view import (
    AnnotationRecord,
    BlindSample,
    assert_neutral_sample_id,
    assert_no_label_leak,
    create_blind_sample,
    export_blind_view,
    extract_safe_view_content,
    validate_annotation_record,
)


@dataclass(frozen=True, slots=True)
class KappaResult:
    """Kết quả đo đạc độ đồng thuận giữa hai người đánh giá độc lập theo Cohen's Kappa."""
    kappa: float | None
    observed_agreement: float  # P_o (tỷ lệ đồng thuận quan sát)
    expected_agreement: float  # P_e (tỷ lệ đồng thuận ngẫu nhiên kỳ vọng)
    status: Literal["valid", "undefined_single_class", "undefined_zero_variance"]
    sample_count: int
    categories: list[str]


def compute_cohens_kappa(
    rater1: Sequence[Any],
    rater2: Sequence[Any],
    *,
    is_difficult: Sequence[bool] | None = None,
    allow_dry_run: bool = False,
) -> KappaResult:
    """Tính chỉ số thỏa thuận liên đánh giá viên Cohen's Kappa giữa A và B trên mẫu ngẫu nhiên.

    Quy tắc ARS bắt buộc:
    1. Chỉ áp dụng trên 30% mẫu ngẫu nhiên được chọn trước, tuyệt đối không tính trên các ca khó
       được chuyển riêng (nếu cung cấp is_difficult, các ca khó sẽ bị loại khỏi mẫu đo).
    2. Loại bỏ triệt để các bản ghi mô phỏng/dry-run (is_dry_run=True) để không làm sai lệch thống kê.
    3. Khi Pe = 1.0 (hoặc toàn bộ dữ liệu chỉ có duy nhất 1 danh mục), hệ số Kappa không xác định (0/0).
       Hàm trả về kappa = None, status = 'undefined_single_class', và ghi nhận P_o riêng biệt.
    4. Kiểm tra tính toàn vẹn dữ liệu: phát hiện thiếu nhãn (None, rỗng, whitespace).
    """
    if len(rater1) != len(rater2) or len(rater1) == 0:
        raise ValueError("Hai danh sách nhãn phải có cùng độ dài và không được rỗng.")

    diff_flags = is_difficult if is_difficult is not None else [False] * len(rater1)
    if is_difficult is not None and len(is_difficult) != len(rater1):
        raise ValueError("Độ dài mảng is_difficult phải khớp với độ dài danh sách nhãn.")

    # Lọc bỏ các ca khó và bản ghi dry-run mô phỏng
    clean_pairs = []
    for r1, r2, diff in zip(rater1, rater2, diff_flags):
        is_dr1 = getattr(r1, "is_dry_run", False) or (isinstance(r1, dict) and r1.get("is_dry_run", False))
        is_dr2 = getattr(r2, "is_dry_run", False) or (isinstance(r2, dict) and r2.get("is_dry_run", False))
        if not allow_dry_run and (is_dr1 or is_dr2):
            continue

        if diff:
            continue

        val1 = getattr(r1, "class_label", None) or (r1.get("class_label") if isinstance(r1, dict) else r1)
        val2 = getattr(r2, "class_label", None) or (r2.get("class_label") if isinstance(r2, dict) else r2)
        clean_pairs.append((val1, val2))

    if not clean_pairs:
        raise ValueError("Không còn mẫu ngẫu nhiên hợp lệ nào sau khi loại bỏ ca khó và bản ghi dry-run.")

    r1_list, r2_list = zip(*clean_pairs)

    # Kiểm tra thiếu dữ liệu
    for idx, (v1, v2) in enumerate(zip(r1_list, r2_list)):
        if v1 is None or v2 is None or str(v1).strip() == "" or str(v2).strip() == "":
            raise ValueError(f"Thiếu dữ liệu nhãn tại vị trí mẫu index {idx}: rater1={v1!r}, rater2={v2!r}")

    n = len(r1_list)
    categories = sorted(list(set(str(x) for x in r1_list) | set(str(x) for x in r2_list)))
    cat_to_idx = {c: i for i, c in enumerate(categories)}
    k = len(categories)

    # Nếu toàn bộ mẫu chỉ có duy nhất 1 category (k <= 1), Pe = 1.0 -> Kappa = 0/0 (không xác định)
    if k <= 1:
        return KappaResult(
            kappa=None,
            observed_agreement=1.0,
            expected_agreement=1.0,
            status="undefined_single_class",
            sample_count=n,
            categories=categories,
        )

    # Ma trận nhầm lẫn (confusion matrix)
    matrix = [[0] * k for _ in range(k)]
    for r1, r2 in zip(r1_list, r2_list):
        matrix[cat_to_idx[str(r1)]][cat_to_idx[str(r2)]] += 1

    # Đồng thuận quan sát Po
    po = sum(matrix[i][i] for i in range(k)) / n

    # Đồng thuận kỳ vọng ngẫu nhiên Pe
    row_sums = [sum(matrix[i][j] for j in range(k)) for i in range(k)]
    col_sums = [sum(matrix[i][j] for i in range(k)) for j in range(k)]
    pe = sum((row_sums[i] * col_sums[i]) for i in range(k)) / (n * n)

    if pe >= 1.0 or abs(1.0 - pe) < 1e-12:
        return KappaResult(
            kappa=None,
            observed_agreement=po,
            expected_agreement=pe,
            status="undefined_single_class",
            sample_count=n,
            categories=categories,
        )

    kappa_val = (po - pe) / (1.0 - pe)
    return KappaResult(
        kappa=round(kappa_val, 4),
        observed_agreement=round(po, 4),
        expected_agreement=round(pe, 4),
        status="valid",
        sample_count=n,
        categories=categories,
    )
