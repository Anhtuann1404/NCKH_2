"""Module annotation: Xuất view gán nhãn mù an toàn, tính chỉ số Cohen's Kappa, và quản lý exclusion registry."""

import json
from typing import List, Dict, Any, Optional


def compute_cohens_kappa(rater1: List[Any], rater2: List[Any]) -> float:
    """Tính chỉ số thỏa thuận liên đánh giá viên Cohen's Kappa giữa A và B trên mẫu ngẫu nhiên.
    
    Quy tắc ARS: Chỉ áp dụng trên 30% mẫu ngẫu nhiên được chọn trước, tuyệt đối không tính trên các ca khó được chuyển riêng.
    """
    if len(rater1) != len(rater2) or len(rater1) == 0:
        raise ValueError("Hai danh sách nhãn phải có cùng độ dài và không được rỗng.")

    n = len(rater1)
    categories = sorted(list(set(rater1) | set(rater2)))
    cat_to_idx = {c: i for i, c in enumerate(categories)}
    k = len(categories)

    if k <= 1:
        return 1.0

    # Ma trận nhầm lẫn
    matrix = [[0] * k for _ in range(k)]
    for r1, r2 in zip(rater1, rater2):
        matrix[cat_to_idx[r1]][cat_to_idx[r2]] += 1

    # Quan sát Po
    po = sum(matrix[i][i] for i in range(k)) / n

    # Kỳ vọng Pe
    row_sums = [sum(matrix[i][j] for j in range(k)) for i in range(k)]
    col_sums = [sum(matrix[i][j] for i in range(k)) for j in range(k)]
    pe = sum((row_sums[i] * col_sums[i]) for i in range(k)) / (n * n)

    if pe == 1.0:
        return 1.0

    return (po - pe) / (1.0 - pe)
