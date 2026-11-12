"""Module tính toán độ đồng thuận liên đánh giá viên Cohen's Kappa Ma trận 3x3 (Codebook v1.1).

Tuân thủ nghiêm ngặt Kỷ luật ARS & Ponytail Discipline:
1. Thư viện chuẩn Python thuần túy (math, random, dataclasses, typing). Zero external dependency.
2. Đánh giá trên ma trận 3x3 chuẩn theo 3 danh mục của Codebook v1.1:
   ['phishing', 'benign', 'insufficient_evidence'].
3. Tính toán đầy đủ:
   - Po (observed agreement), Pe (expected chance agreement), Unweighted Cohen's Kappa.
   - Ước lượng khoảng tin cậy 95% chuẩn mực bằng Non-parametric Paired Bootstrap
     (lấy mẫu lại có hoàn lại theo cặp nhãn A-B của cùng mẫu).
   - Tham số kiểm toán mặc định: seed = 2026, số lượt resample B = 1.000 lượt.
   - Giám sát chặt chẽ tỷ lệ suy biến B_deg / B (Pe* >= 1.0): nếu > 5% thì KHÔNG công bố CI và đưa ra cảnh báo.
   - LOẠI BỎ HOÀN TOÀN mọi công thức xấp xỉ nhị phân cũ và tuyệt đối không dùng phương pháp xấp xỉ thay thế khi bootstrap không đủ lượt hợp lệ.
   - Phân định 3 vùng quyết định: Pass (>= 0.75), Conditional Review (0.60-0.75), Stop (< 0.60).
"""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any, Literal, Sequence

CODEBOOK_V1_1_LABELS: tuple[str, ...] = ("phishing", "benign", "insufficient_evidence")


@dataclass(frozen=True, slots=True)
class Kappa3x3Result:
    """Kết quả đo đạc độ đồng thuận Cohen's Kappa ma trận 3x3 kèm khoảng tin cậy 95% Paired Bootstrap."""
    sample_count: int
    labels: list[str]
    matrix_3x3: list[list[int]]  # rows: Rater A, columns: Rater B
    observed_agreement: float    # Po
    expected_agreement: float    # Pe
    kappa: float | None
    ci95_bootstrap: tuple[float, float] | None
    bootstrap_iterations: int
    bootstrap_seed: int
    bootstrap_degenerate_count: int
    bootstrap_degenerate_ratio: float
    bootstrap_warning: str | None
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
    random_seed: int = 2026,
    max_degenerate_ratio: float = 0.05,
) -> Kappa3x3Result:
    """Tính chỉ số Cohen's Kappa ma trận 3x3 và khoảng tin cậy 95% Paired Bootstrap cho 2 chuỗi nhãn của A và B.

    Tham số:
        labels_a: Chuỗi nhãn của Annotator A.
        labels_b: Chuỗi nhãn của Annotator B (cùng độ dài, đã ghép cặp sample_id).
        bootstrap_iterations: Số lượt lấy mẫu lại Paired Bootstrap (mặc định 1.000).
        random_seed: Hạt giống ngẫu nhiên cố định kiểm toán (mặc định 2026).
        max_degenerate_ratio: Ngưỡng tỷ lệ suy biến tối đa cho phép công bố CI (mặc định 0.05 = 5%).
    """
    n = len(labels_a)
    if n == 0 or len(labels_b) != n:
        raise ValueError(f"Hai danh sách nhãn phải có cùng độ dài và không được rỗng (a={len(labels_a)}, b={len(labels_b)}).")

    clean_a = [_validate_label(lbl, i, "Annotator A") for i, lbl in enumerate(labels_a)]
    clean_b = [_validate_label(lbl, i, "Annotator B") for i, lbl in enumerate(labels_b)]

    labels_list = list(CODEBOOK_V1_1_LABELS)
    label_to_idx = {l: i for i, l in enumerate(labels_list)}
    k = len(labels_list)  # 3

    # Xây dựng ma trận nhầm lẫn 3x3
    matrix = [[0] * k for _ in range(k)]
    for la, lb in zip(clean_a, clean_b):
        matrix[label_to_idx[la]][label_to_idx[lb]] += 1

    row_sums = [sum(matrix[i][j] for j in range(k)) for i in range(k)]
    col_sums = [sum(matrix[j][i] for j in range(k)) for i in range(k)]

    marginal_a = {labels_list[i]: row_sums[i] for i in range(k)}
    marginal_b = {labels_list[i]: col_sums[i] for i in range(k)}
    per_class_agree = {labels_list[i]: matrix[i][i] for i in range(k)}

    # Đồng thuận quan sát Po
    agree_count = sum(matrix[i][i] for i in range(k))
    po = agree_count / n

    # Đồng thuận kỳ vọng ngẫu nhiên Pe
    pe = sum(row_sums[i] * col_sums[i] for i in range(k)) / (n * n)

    # Trường hợp đặc biệt: toàn bộ mẫu thuộc 1 danh mục duy nhất (Pe = 1.0)
    if pe >= 1.0 or abs(1.0 - pe) < 1e-12:
        return Kappa3x3Result(
            sample_count=n,
            labels=labels_list,
            matrix_3x3=matrix,
            observed_agreement=round(po, 4),
            expected_agreement=round(pe, 4),
            kappa=None,
            ci95_bootstrap=None,
            bootstrap_iterations=bootstrap_iterations,
            bootstrap_seed=random_seed,
            bootstrap_degenerate_count=0,
            bootstrap_degenerate_ratio=0.0,
            bootstrap_warning="Dữ liệu đơn lớp duy nhất (Pe = 1.0); hệ số Kappa không xác định.",
            status="undefined_single_class",
            zone="undefined",
            marginal_rater_a=marginal_a,
            marginal_rater_b=marginal_b,
            per_class_agreement=per_class_agree,
        )

    kappa = (po - pe) / (1.0 - pe)

    # Ước lượng khoảng tin cậy 95% bằng Non-parametric Paired Bootstrap
    ci95_bootstrap = None
    bootstrap_warning = None
    b_deg_count = 0

    if bootstrap_iterations > 0 and n > 1:
        rng = random.Random(random_seed)
        pairs = list(zip(clean_a, clean_b))
        boot_kappas: list[float] = []

        for _ in range(bootstrap_iterations):
            # Lấy mẫu lại CẶP (y_A, y_B) có hoàn lại
            sampled_pairs = [pairs[rng.randint(0, n - 1)] for _ in range(n)]
            b_matrix = [[0] * k for _ in range(k)]
            for sa, sb in sampled_pairs:
                b_matrix[label_to_idx[sa]][label_to_idx[sb]] += 1

            b_po = sum(b_matrix[i][i] for i in range(k)) / n
            b_rows = [sum(b_matrix[i][j] for j in range(k)) for i in range(k)]
            b_cols = [sum(b_matrix[j][i] for j in range(k)) for i in range(k)]
            b_pe = sum(b_rows[i] * b_cols[i] for i in range(k)) / (n * n)

            # Kiểm tra suy biến: tất cả các cặp bốc được rơi vào 1 lớp duy nhất
            if b_pe >= 1.0 or abs(1.0 - b_pe) < 1e-12:
                b_deg_count += 1
            else:
                b_k = (b_po - b_pe) / (1.0 - b_pe)
                boot_kappas.append(b_k)

        deg_ratio = b_deg_count / bootstrap_iterations

        if deg_ratio > max_degenerate_ratio:
            ci95_bootstrap = None
            bootstrap_warning = (
                f"Tỷ lệ mẫu suy biến B_deg/B = {deg_ratio:.2%} ({b_deg_count}/{bootstrap_iterations}) "
                f"vượt ngưỡng tối đa cho phép ({max_degenerate_ratio:.2%}). "
                "Dữ liệu thiếu biến thiên đa lớp; KHÔNG công bố khoảng tin cậy Bootstrap."
            )
        elif len(boot_kappas) < 50:
            ci95_bootstrap = None
            bootstrap_warning = "Số lượng mẫu bootstrap hợp lệ quá ít (< 50 lượt); KHÔNG công bố khoảng tin cậy."
        else:
            boot_kappas.sort()
            idx_low = int(0.025 * len(boot_kappas))
            idx_high = min(len(boot_kappas) - 1, int(0.975 * len(boot_kappas)))
            b_low = max(-1.0, boot_kappas[idx_low])
            b_high = min(1.0, boot_kappas[idx_high])
            ci95_bootstrap = (round(b_low, 4), round(b_high, 4))
            bootstrap_warning = None
    else:
        deg_ratio = 0.0
        if bootstrap_iterations <= 0:
            bootstrap_warning = "Không chạy bootstrap (bootstrap_iterations = 0)."
        elif n <= 1:
            bootstrap_warning = "Cỡ mẫu quá nhỏ (N <= 1), không thể thực hiện lấy mẫu lại bootstrap."

    # Phân vùng quyết định theo Tiêu chí Đợt 1
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
        ci95_bootstrap=ci95_bootstrap,
        bootstrap_iterations=bootstrap_iterations,
        bootstrap_seed=random_seed,
        bootstrap_degenerate_count=b_deg_count,
        bootstrap_degenerate_ratio=round(deg_ratio, 4),
        bootstrap_warning=bootstrap_warning,
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
    target_sample_ids: Sequence[str] | None = None,
    sample_id_field: str = "sample_id",
    label_field: str = "class_label",
    allow_dry_run: bool = False,
    bootstrap_iterations: int = 1000,
    random_seed: int = 2026,
    max_degenerate_ratio: float = 0.05,
) -> Kappa3x3Result:
    """Tính toán Cohen's Kappa 3x3 từ 2 danh sách AnnotationRecord của A và B.

    Hỗ trợ ranh giới gán nhãn Đợt 1 (A có 100 mẫu, B có 30 mẫu ngẫu nhiên):
    1. Nếu truyền target_sample_ids (30 ID ngẫu nhiên từ hồ sơ phân tầng hạn chế):
       Tự động lọc cả A và B theo đúng 30 ID này, loại bỏ toàn bộ ca khó bổ sung khỏi mẫu số Kappa.
    2. Nếu không truyền target_sample_ids:
       Yêu cầu tập ID của A và B phải trùng khớp tuyệt đối. Nếu lệch cỡ mẫu (ví dụ 100 vs 30),
       ném lỗi cảnh báo rõ ràng để ngăn ngừa tính sai mẫu số.
    3. Tự động loại bỏ bản ghi dry-run (nếu allow_dry_run=False).
    """
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

    if target_sample_ids is not None:
        # Trường hợp ghép cặp có chọn lọc qua danh sách ID phân tầng (ví dụ 30 ID ngẫu nhiên Đợt 1)
        target_list = [str(sid) for sid in target_sample_ids]
        target_set = set(target_list)
        if len(target_list) != len(target_set):
            seen = set()
            duplicates = []
            for sid in target_list:
                if sid in seen and sid not in duplicates:
                    duplicates.append(sid)
                seen.add(sid)
            raise ValueError(
                f"LỖI DANH SÁCH MỤC TIÊU: 'target_sample_ids' chứa ID trùng lặp ({len(target_list)} phần tử nhưng chỉ có {len(target_set)} ID duy nhất). "
                f"Các ID bị lặp: {duplicates}. Cấm tính lặp mẫu số Cohen's Kappa!"
            )
        missing_in_a = target_set - set(map_a.keys())
        missing_in_b = target_set - set(map_b.keys())
        if missing_in_a or missing_in_b:
            raise ValueError(
                f"LỖI GHÉP CẶP PHÂN TẦNG: Danh sách target_sample_ids không tìm thấy đầy đủ trong bản ghi. "
                f"Thiếu ở A ({len(missing_in_a)} mẫu): {list(missing_in_a)[:5]}; "
                f"Thiếu ở B ({len(missing_in_b)} mẫu): {list(missing_in_b)[:5]}."
            )
        paired_sids = target_list
    else:
        # Trường hợp hai tập bản ghi phải khớp mẫu số 100%
        keys_a = set(map_a.keys())
        keys_b = set(map_b.keys())
        if keys_a != keys_b:
            diff_ab = keys_a - keys_b
            diff_ba = keys_b - keys_a
            raise ValueError(
                f"Tập hợp sample_id không khớp giữa Annotator A và B (A={len(keys_a)}, B={len(keys_b)}). "
                f"Chỉ có ở A ({len(diff_ab)} mẫu): {sorted(list(diff_ab))[:5]}... "
                f"Chỉ có ở B ({len(diff_ba)} mẫu): {sorted(list(diff_ba))[:5]}... "
                "Lưu ý: Nếu Đợt 1 có quy mô khác nhau (A=100, B=30), hãy truyền 'target_sample_ids' để lọc đúng 30 mẫu ngẫu nhiên."
            )
        paired_sids = sorted(list(keys_a))

    paired_labels_a = [map_a[sid] for sid in paired_sids]
    paired_labels_b = [map_b[sid] for sid in paired_sids]

    return compute_kappa_3x3(
        paired_labels_a,
        paired_labels_b,
        bootstrap_iterations=bootstrap_iterations,
        random_seed=random_seed,
        max_degenerate_ratio=max_degenerate_ratio,
    )


def format_kappa_3x3_report(
    result: Kappa3x3Result,
    *,
    title: str = "BÁO CÁO ĐỒNG THUẬN COHEN'S KAPPA MA TRẬN 3x3 (ĐỢT 1)",
) -> str:
    """Xuất báo cáo định dạng Markdown chuẩn ARS cho ma trận 3x3 và Paired Bootstrap CI 95%."""
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
        "#### 2. Các chỉ số thống kê đồng thuận & Khoảng tin cậy Paired Bootstrap",
        "",
        f"- **Tỷ lệ đồng thuận quan sát ($P_o$):** `{result.observed_agreement:.4f}` ({result.observed_agreement * 100:.2f}%)",
        f"- **Tỷ lệ đồng thuận kỳ vọng ngẫu nhiên ($P_e$):** `{result.expected_agreement:.4f}` ({result.expected_agreement * 100:.2f}%)",
    ]

    if result.kappa is not None:
        report_lines.append(f"- **Hệ số Cohen's Kappa ($3 \\times 3$):** **`{result.kappa:.4f}`**")
        report_lines.append(
            f"- **Tỷ lệ suy biến Bootstrap ($B_{{\\text{{deg}}}}/B$):** `{result.bootstrap_degenerate_count}/{result.bootstrap_iterations}` "
            f"({result.bootstrap_degenerate_ratio * 100:.2f}%)"
        )
        if result.ci95_bootstrap is not None:
            report_lines.append(
                f"- **Khoảng tin cậy 95% Paired Bootstrap ({result.bootstrap_iterations} lượt, seed {result.bootstrap_seed}):** "
                f"`[{result.ci95_bootstrap[0]:.4f}, {result.ci95_bootstrap[1]:.4f}]`"
            )
        else:
            if result.bootstrap_iterations <= 0:
                reason = "Không chạy bootstrap (bootstrap_iterations = 0)"
            elif result.bootstrap_degenerate_ratio > 0.05:
                reason = f"Do tỷ lệ mẫu suy biến B_deg/B = {result.bootstrap_degenerate_ratio:.2%} vượt ngưỡng an toàn 5%"
            elif result.bootstrap_warning and ("< 50" in result.bootstrap_warning or "quá ít" in result.bootstrap_warning):
                reason = "Do số lượt bootstrap hợp lệ dưới 50 lượt"
            elif result.bootstrap_warning:
                reason = result.bootstrap_warning
            else:
                reason = "Không đủ điều kiện tính bootstrap"

            report_lines.append(f"- **Khoảng tin cậy 95% Paired Bootstrap:** `KHÔNG CÔNG BỐ` ({reason})")

        if result.bootstrap_warning:
            report_lines.append(f"- **Cảnh báo bất định Bootstrap:** ⚠️ *{result.bootstrap_warning}*")
    else:
        report_lines.append("- **Hệ số Cohen's Kappa:** `None` (Dữ liệu đơn lớp hoặc biến thiên bằng 0)")

    return "\n".join(report_lines)
