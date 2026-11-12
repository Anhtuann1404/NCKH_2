"""Module tính toán độ đồng thuận liên đánh giá viên Cohen's Kappa Ma trận 3x3 (Codebook v1.1).

Tuân thủ nghiêm ngặt Kỷ luật ARS & Ponytail Discipline:
1. Thư viện chuẩn Python thuần túy (math, random, dataclasses, typing). Zero external dependency.
2. Đánh giá trên ma trận 3x3 chuẩn theo 3 danh mục của Codebook v1.1:
   ['phishing', 'benign', 'insufficient_evidence'].
3. Tính toán đầy đủ:
   - Po (observed agreement), Pe (expected chance agreement), Unweighted Cohen's Kappa.
   - Sai số chuẩn tiệm cận Fleiss (Fleiss Asymptotic Standard Error).
   - Khoảng tin cậy 95% tiệm cận (Fleiss CI 95%).
   - Khoảng tin cậy 95% phi tham số Bootstrap (1.000 lượt resample có hoàn lại).
   - Phân định 3 vùng quyết định (Pass >= 0.75, Conditional Review 0.60-0.75, Stop < 0.60).
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Any, Literal, Sequence

CODEBOOK_V1_1_LABELS: tuple[str, ...] = ("phishing", "benign", "insufficient_evidence")


@dataclass(frozen=True, slots=True)
class Kappa3x3Result:
    """Kết quả đo đạc độ đồng thuận Cohen's Kappa ma trận 3x3 kèm khoảng tin cậy 95%."""
    sample_count: int
    labels: list[str]
    matrix_3x3: list[list[int]]  # rows: Rater A, columns: Rater B
    observed_agreement: float    # Po
    expected_agreement: float    # Pe
    kappa: float | None
    se_fleiss: float | None
    ci95_fleiss: tuple[float, float] | None
    ci95_bootstrap: tuple[float, float] | None
    status: Literal["valid", "undefined_single_class", "zero_variance"]
    zone: Literal["pass", "conditional_review", "stop", "undefined"]
    marginal_rater_a: dict[str, int]
    marginal_rater_b: dict[str, int]
    per_class_agreement: dict[str, int]


def _validate_label(lbl: Any, idx: int, rater_name: str) -> str:
    if lbl is None:
        raise ValueError(f"Nhãn rỗng/None tại mẫu index {idx} của {rater_name}.")
    s = str(lbl).strip()
    if not s:
        raise ValueError(f"Nhãn trống tại mẫu index {idx} của {rater_name}.")
    if s not in CODEBOOK_V1_1_LABELS:
        raise ValueError(
            f"Nhãn không hợp lệ '{s}' tại mẫu index {idx} của {rater_name}. "
            f"Chỉ chấp nhận 3 danh mục Codebook v1.1: {CODEBOOK_V1_1_LABELS}"
        )
    return s


def compute_kappa_3x3(
    labels_a: Sequence[str],
    labels_b: Sequence[str],
    *,
    bootstrap_iterations: int = 1000,
    random_seed: int = 42,
) -> Kappa3x3Result:
    """Tính chỉ số Cohen's Kappa ma trận 3x3 cho 2 chuỗi nhãn của Annotator A và B."""
    n = len(labels_a)
    if n == 0 or len(labels_b) != n:
        raise ValueError(f"Hai danh sách nhãn phải có cùng độ dài và không được rỗng (a={len(labels_a)}, b={len(labels_b)}).")

    clean_a = [_validate_label(lbl, i, "Annotator A") for i, lbl in enumerate(labels_a)]
    clean_b = [_validate_label(lbl, i, "Annotator B") for i, lbl in enumerate(labels_b)]

    labels_list = list(CODEBOOK_V1_1_LABELS)
    label_to_idx = {l: i for i, l in enumerate(labels_list)}
    k = len(labels_list)  # 3

    matrix = [[0] * k for _ in range(k)]
    for la, lb in zip(clean_a, clean_b):
        matrix[label_to_idx[la]][label_to_idx[lb]] += 1

    row_sums = [sum(matrix[i][j] for j in range(k)) for i in range(k)]
    col_sums = [sum(matrix[j][i] for j in range(k)) for i in range(k)]

    marginal_a = {labels_list[i]: row_sums[i] for i in range(k)}
    marginal_b = {labels_list[i]: col_sums[i] for i in range(k)}
    per_class_agree = {labels_list[i]: matrix[i][i] for i in range(k)}

    agree_count = sum(matrix[i][i] for i in range(k))
    po = agree_count / n
    pe = sum(row_sums[i] * col_sums[i] for i in range(k)) / (n * n)

    if pe >= 1.0 or abs(1.0 - pe) < 1e-12:
        return Kappa3x3Result(
            sample_count=n,
            labels=labels_list,
            matrix_3x3=matrix,
            observed_agreement=round(po, 4),
            expected_agreement=round(pe, 4),
            kappa=None,
            se_fleiss=None,
            ci95_fleiss=None,
            ci95_bootstrap=None,
            status="undefined_single_class",
            zone="undefined",
            marginal_rater_a=marginal_a,
            marginal_rater_b=marginal_b,
            per_class_agreement=per_class_agree,
        )

    kappa = (po - pe) / (1.0 - pe)

    var_fleiss = (po * (1.0 - po)) / (n * ((1.0 - pe) ** 2))
    se_fleiss = math.sqrt(max(0.0, var_fleiss))
    ci95_f_low = max(-1.0, kappa - 1.96 * se_fleiss)
    ci95_f_high = min(1.0, kappa + 1.96 * se_fleiss)
    ci95_fleiss = (round(ci95_f_low, 4), round(ci95_f_high, 4))

    ci95_bootstrap = None
    if bootstrap_iterations > 0 and n > 1:
        rng = random.Random(random_seed)
        pairs = list(zip(clean_a, clean_b))
        boot_kappas: list[float] = []

        for _ in range(bootstrap_iterations):
            sampled_pairs = [pairs[rng.randint(0, n - 1)] for _ in range(n)]
            b_matrix = [[0] * k for _ in range(k)]
            for sa, sb in sampled_pairs:
                b_matrix[label_to_idx[sa]][label_to_idx[sb]] += 1

            b_po = sum(b_matrix[i][i] for i in range(k)) / n
            b_rows = [sum(b_matrix[i][j] for j in range(k)) for i in range(k)]
            b_cols = [sum(b_matrix[j][i] for j in range(k)) for i in range(k)]
            b_pe = sum(b_rows[i] * b_cols[i] for i in range(k)) / (n * n)

            if b_pe < 1.0 and abs(1.0 - b_pe) >= 1e-12:
                b_k = (b_po - b_pe) / (1.0 - b_pe)
                boot_kappas.append(b_k)

        if len(boot_kappas) >= 50:
            boot_kappas.sort()
            idx_low = int(0.025 * len(boot_kappas))
            idx_high = min(len(boot_kappas) - 1, int(0.975 * len(boot_kappas)))
            b_low = max(-1.0, boot_kappas[idx_low])
            b_high = min(1.0, boot_kappas[idx_high])
            ci95_bootstrap = (round(b_low, 4), round(b_high, 4))
        else:
            ci95_bootstrap = ci95_fleiss

    zone: Literal["pass", "conditional_review", "stop", "undefined"]
    if kappa >= 0.75:
        zone = "pass"
    elif kappa >= 0.60:
        zone = "conditional_review"
    else:
        zone = "stop"

    return Kappa3x3Result(
        sample_count=n,
        labels=labels_list,
        matrix_3x3=matrix,
        observed_agreement=round(po, 4),
        expected_agreement=round(pe, 4),
        kappa=round(kappa, 4),
        se_fleiss=round(se_fleiss, 4),
        ci95_fleiss=ci95_fleiss,
        ci95_bootstrap=ci95_bootstrap,
        status="valid",
        zone=zone,
        marginal_rater_a=marginal_a,
        marginal_rater_b=marginal_b,
        per_class_agreement=per_class_agree,
    )


def compute_kappa_3x3_from_records(
    records_a: Sequence[Any],
    records_b: Sequence[Any],
    *,
    sample_id_field: str = "sample_id",
    label_field: str = "class_label",
    allow_dry_run: bool = False,
    bootstrap_iterations: int = 1000,
    random_seed: int = 42,
) -> Kappa3x3Result:
    """Tính toán Cohen's Kappa 3x3 từ 2 danh sách AnnotationRecord của A và B."""
    def _get(rec: Any, key: str) -> Any:
        if isinstance(rec, dict):
            return rec.get(key)
        return getattr(rec, key, None)

    clean_recs_a = [r for r in records_a if allow_dry_run or not _get(r, "is_dry_run")]
    clean_recs_b = [r for r in records_b if allow_dry_run or not _get(r, "is_dry_run")]

    map_a: dict[str, str] = {}
    for r in clean_recs_a:
        sid = _get(r, sample_id_field)
        if not sid:
            raise ValueError(f"Bản ghi Annotator A thiếu trường {sample_id_field}: {r}")
        sid_str = str(sid)
        if sid_str in map_a:
            raise ValueError(f"Trùng lặp sample_id trong danh sách của Annotator A: {sid_str}")
        lbl = _get(r, label_field)
        map_a[sid_str] = str(lbl) if lbl is not None else ""

    map_b: dict[str, str] = {}
    for r in clean_recs_b:
        sid = _get(r, sample_id_field)
        if not sid:
            raise ValueError(f"Bản ghi Annotator B thiếu trường {sample_id_field}: {r}")
        sid_str = str(sid)
        if sid_str in map_b:
            raise ValueError(f"Trùng lặp sample_id trong danh sách của Annotator B: {sid_str}")
        lbl = _get(r, label_field)
        map_b[sid_str] = str(lbl) if lbl is not None else ""

    keys_a = set(map_a.keys())
    keys_b = set(map_b.keys())
    if keys_a != keys_b:
        diff_ab = keys_a - keys_b
        diff_ba = keys_b - keys_a
        raise ValueError(
            f"Tập hợp sample_id không khớp giữa Annotator A và B. "
            f"Chỉ có ở A ({len(diff_ab)} mẫu): {sorted(list(diff_ab))[:5]}... "
            f"Chỉ có ở B ({len(diff_ba)} mẫu): {sorted(list(diff_ba))[:5]}..."
        )

    sorted_sids = sorted(list(keys_a))
    paired_labels_a = [map_a[sid] for sid in sorted_sids]
    paired_labels_b = [map_b[sid] for sid in sorted_sids]

    return compute_kappa_3x3(
        paired_labels_a,
        paired_labels_b,
        bootstrap_iterations=bootstrap_iterations,
        random_seed=random_seed,
    )


def format_kappa_3x3_report(
    result: Kappa3x3Result,
    *,
    title: str = "BÁO CÁO ĐỒNG THUẬN COHEN'S KAPPA MA TRẬN 3x3 (ĐỢT 1)",
) -> str:
    """Xuất báo cáo định dạng Markdown chuẩn ARS cho ma trận 3x3 và các chỉ số tin cậy."""
    labels = result.labels
    m = result.matrix_3x3

    zone_desc = {
        "pass": "✅ **VÙNG ĐẠT CHUẨN (Pass: kappa >= 0.75)** — Đủ điều kiện kỹ thuật để Lead D xem xét mở rộng Đợt 2.",
        "conditional_review": "⚠️ **VÙNG RÀ SOÁT CÓ ĐIỀU KIỆN (0.60 <= kappa < 0.75)** — Không tự động mở Đợt 2; Lead D, B và C họp rà soát snapshot.",
        "stop": "❌ **VÙNG DỪNG KHẨN CẤP (Stop: kappa < 0.60)** — Dừng toàn diện tiêu chọn; Lead D chủ trì họp rà soát Codebook.",
        "undefined": "❓ **KHÔNG XÁC ĐỊNH** — Dữ liệu đơn lớp hoặc Pe >= 1.0.",
    }

    report_lines = [
        f"### {title}",
        "",
        f"- **Quy mô mẫu đối soát ($N$):** {result.sample_count} mẫu",
        f"- **Trạng thái đánh giá:** `{result.status}`",
        f"- **Kết luận phân vùng nghiệm thu:** {zone_desc.get(result.zone, result.zone)}",
        "",
        "#### 1. Ma trận nhầm lẫn $3 \\times 3$ (Confusion Matrix)",
        "",
        "| Rater A (Hàng) \\ Rater B (Cột) | Phishing | Benign | Insufficient Evidence | Tổng A |",
        "|:---|:---:|:---:|:---:|:---:|",
        f"| **Phishing** | {m[0][0]} | {m[0][1]} | {m[0][2]} | **{sum(m[0])}** |",
        f"| **Benign** | {m[1][0]} | {m[1][1]} | {m[1][2]} | **{sum(m[1])}** |",
        f"| **Insufficient Evidence** | {m[2][0]} | {m[2][1]} | {m[2][2]} | **{sum(m[2])}** |",
        f"| **Tổng B** | **{result.marginal_rater_b['phishing']}** | **{result.marginal_rater_b['benign']}** | **{result.marginal_rater_b['insufficient_evidence']}** | **{result.sample_count}** |",
        "",
        "#### 2. Các chỉ số thống kê đồng thuận",
        "",
        f"- **Tỷ lệ đồng thuận quan sát ($P_o$):** `{result.observed_agreement:.4f}` ({result.observed_agreement * 100:.2f}%)",
        f"- **Tỷ lệ đồng thuận kỳ vọng ngẫu nhiên ($P_e$):** `{result.expected_agreement:.4f}` ({result.expected_agreement * 100:.2f}%)",
    ]

    if result.kappa is not None:
        report_lines.extend([
            f"- **Hệ số Cohen's Kappa ($3 \\times 3$):** **`{result.kappa:.4f}`**",
            f"- **Sai số chuẩn tiệm cận Fleiss ($SE$):** `{result.se_fleiss:.4f}`" if result.se_fleiss is not None else "- **Sai số Fleiss:** `N/A`",
            f"- **Khoảng tin cậy 95% tiệm cận Fleiss (Fleiss CI 95%):** `[{result.ci95_fleiss[0]:.4f}, {result.ci95_fleiss[1]:.4f}]`" if result.ci95_fleiss else "- **Fleiss CI 95%:** `N/A`",
            f"- **Khoảng tin cậy 95% Bootstrap (Bootstrap CI 95%):** `[{result.ci95_bootstrap[0]:.4f}, {result.ci95_bootstrap[1]:.4f}]`" if result.ci95_bootstrap else "- **Bootstrap CI 95%:** `N/A`",
        ])
    else:
        report_lines.append("- **Hệ số Cohen's Kappa:** `None` (Dữ liệu đơn lớp hoặc biến thiên bằng 0)")

    return "\n".join(report_lines)
