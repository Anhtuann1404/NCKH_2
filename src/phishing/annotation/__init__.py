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
    random_subset: Sequence[bool] | None = None,
    label_field: Literal["class_label", "primary_org"] = "class_label",
    allow_dry_run: bool = False,
) -> KappaResult:
    """Tính chỉ số thỏa thuận liên đánh giá viên Cohen's Kappa giữa A và B trên mẫu ngẫu nhiên.

    Quy tắc ARS bắt buộc:
    1. Chọn theo random_subset, giữ cả ca khó vốn nằm trong random. is_difficult
       chỉ là metadata, không quyết định loại mẫu. Chuỗi nhãn không metadata được
       xem là đầu vào đã lọc random; khi truyền is_difficult phải truyền membership.
    2. Loại bỏ triệt để các bản ghi mô phỏng/dry-run (is_dry_run=True) để không làm sai lệch thống kê.
    3. Khi Pe = 1.0 (hoặc toàn bộ dữ liệu chỉ có duy nhất 1 danh mục), hệ số Kappa không xác định (0/0).
       Hàm trả về kappa = None, status = 'undefined_single_class', và ghi nhận P_o riêng biệt.
    4. Kiểm tra tính toàn vẹn dữ liệu: phát hiện thiếu nhãn (None, rỗng, whitespace).
    """
    if len(rater1) != len(rater2) or len(rater1) == 0:
        raise ValueError("Hai danh sách nhãn phải có cùng độ dài và không được rỗng.")

    # Ghép cặp nhãn giữa A và B bằng từ điển theo sample_id nếu có để tránh lệch thứ tự dòng
    has_sid1 = len(rater1) > 0 and all(isinstance(r, dict) and "sample_id" in r or hasattr(r, "sample_id") for r in rater1)
    has_sid2 = len(rater2) > 0 and all(isinstance(r, dict) and "sample_id" in r or hasattr(r, "sample_id") for r in rater2)

    if has_sid1 and has_sid2:
        dict2 = {getattr(r, "sample_id", None) or r["sample_id"]: r for r in rater2}
        if len(dict2) != len(rater2):
            raise ValueError("Phát hiện sample_id trùng lặp trong danh sách rater2.")
        dict1_sids = [getattr(r, "sample_id", None) or r["sample_id"] for r in rater1]
        if len(set(dict1_sids)) != len(rater1):
            raise ValueError("Phát hiện sample_id trùng lặp trong danh sách rater1.")
        if set(dict1_sids) != set(dict2.keys()):
            raise ValueError("Danh sách sample_id giữa hai đánh giá viên không khớp nhau.")

        def _get_pkg_hash(item: Any) -> str | None:
            if isinstance(item, dict):
                return item.get("dataset_hash") or item.get("package_hash")
            return getattr(item, "dataset_hash", None) or getattr(item, "package_hash", None)

        hashes1 = {h for r in rater1 if (h := _get_pkg_hash(r))}
        hashes2 = {h for r in rater2 if (h := _get_pkg_hash(r))}
        if hashes1 and hashes2 and hashes1 != hashes2:
            raise ValueError(f"Không thể tính Kappa: hai đánh giá viên gán trên gói dữ liệu khác nhau (hash: {hashes1} vs {hashes2}).")

        rater2 = [dict2[sid] for sid in dict1_sids]

    if is_difficult is not None and len(is_difficult) != len(rater1):
        raise ValueError("Độ dài mảng is_difficult phải khớp với độ dài danh sách nhãn.")
    if random_subset is not None and len(random_subset) != len(rater1):
        raise ValueError("Độ dài random_subset phải khớp danh sách nhãn.")
    if label_field not in {"class_label", "primary_org"}:
        raise ValueError("label_field phải là class_label hoặc primary_org.")

    # Lọc bỏ các ca khó và bản ghi dry-run mô phỏng
    clean_pairs = []
    for index, (r1, r2) in enumerate(zip(rater1, rater2)):
        is_dr1 = getattr(r1, "is_dry_run", False) or (isinstance(r1, dict) and r1.get("is_dry_run", False))
        is_dr2 = getattr(r2, "is_dry_run", False) or (isinstance(r2, dict) and r2.get("is_dry_run", False))
        if not allow_dry_run and (is_dr1 or is_dr2):
            continue

        membership1 = r1.get("random_subset") if isinstance(r1, dict) else getattr(r1, "random_subset", None)
        membership2 = r2.get("random_subset") if isinstance(r2, dict) else getattr(r2, "random_subset", None)
        if random_subset is not None:
            membership = random_subset[index]
            if any(m is not None and m != membership for m in (membership1, membership2)):
                raise ValueError("random_subset không khớp metadata bản ghi.")
        elif membership1 is not None or membership2 is not None:
            if membership1 != membership2:
                raise ValueError("random_subset A/B không khớp.")
            membership = membership1
        elif is_difficult is not None:
            raise ValueError("Cần random_subset để phân biệt ca khó random và ca khó thêm.")
        else:
            membership = True  # Chuỗi nhãn đã được caller lọc theo manifest.
        if not isinstance(membership, bool):
            raise ValueError("random_subset phải là boolean.")
        if not membership:
            continue

        val1 = r1.get(label_field) if isinstance(r1, dict) else getattr(r1, label_field, r1)
        val2 = r2.get(label_field) if isinstance(r2, dict) else getattr(r2, label_field, r2)
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
