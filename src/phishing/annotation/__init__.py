"""Module annotation: Xuất view gán nhãn mù an toàn, tính chỉ số Cohen's Kappa, và quản lý exclusion registry."""

from dataclasses import dataclass
from typing import Any, List, Literal, Optional, Sequence

from .blind_view import (
    AnnotationRecord,
    BlindSample,
    assert_neutral_sample_id,
    assert_no_label_leak,
    compute_sample_content_hash,
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
    allow_synthetic: bool = False,
    require_provenance: bool = True,
) -> KappaResult:
    """Tính chỉ số thỏa thuận liên đánh giá viên Cohen's Kappa giữa A và B trên mẫu ngẫu nhiên.

    Quy tắc ARS bắt buộc:
    1. Trong luồng nghiên cứu (require_provenance=True), bắt buộc từng bản ghi phải có đầy đủ 6 trường
       provenance (dataset_id, dataset_hash, codebook_version, codebook_hash, sampling_plan_version, sample_content_hash)
       và sample_id hợp lệ. Nếu thiếu bất kỳ trường nào, lập tức ném ngoại lệ ValueError.
    2. Nếu cần tính toán thuần túy từ chuỗi nhãn hoặc bộ dữ liệu test đơn giản không có provenance,
       sử dụng compute_cohens_kappa_from_labels hoặc truyền rõ require_provenance=False.
    3. Chọn theo random_subset, giữ cả ca khó vốn nằm trong random. is_difficult
       chỉ là metadata, không quyết định loại mẫu.
    4. Loại bỏ triệt để các bản ghi mô phỏng/dry-run (is_dry_run=True) và dữ liệu mô phỏng (is_synthetic=True)
       khỏi thống kê nghiên cứu (trừ khi được chỉ định rõ qua allow_dry_run/allow_synthetic).
    5. Khi Pe = 1.0 (hoặc toàn bộ dữ liệu chỉ có duy nhất 1 danh mục), hệ số Kappa không xác định (0/0).
       Hàm trả về kappa = None, status = 'undefined_single_class', và ghi nhận P_o riêng biệt.
    6. Kiểm tra tính toàn vẹn dữ liệu: phát hiện thiếu nhãn (None, rỗng, whitespace).
    """
    if len(rater1) != len(rater2) or len(rater1) == 0:
        raise ValueError("Hai danh sách nhãn phải có cùng độ dài và không được rỗng.")

    if is_difficult is not None and len(is_difficult) != len(rater1):
        raise ValueError("Độ dài mảng is_difficult phải khớp với độ dài danh sách nhãn.")
    if random_subset is not None and len(random_subset) != len(rater1):
        raise ValueError("Độ dài random_subset phải khớp danh sách nhãn.")
    if label_field not in {"class_label", "primary_org"}:
        raise ValueError("label_field phải là class_label hoặc primary_org.")

    def _extract_sid(r):
        if isinstance(r, dict):
            return r.get("sample_id")
        return getattr(r, "sample_id", None)

    provenance_check_fields = [
        "dataset_id",
        "dataset_hash",
        "codebook_hash",
        "codebook_version",
        "sampling_plan_version",
        "sample_content_hash",
    ]

    # LUỒNG NGHIÊN CỨU: Bắt buộc đầy đủ 6 trường provenance và sample_id trên từng bản ghi
    if require_provenance:
        for r_name, r_list in [("rater1", rater1), ("rater2", rater2)]:
            for idx, r in enumerate(r_list):
                if not isinstance(r, dict) and not hasattr(r, "sample_id"):
                    raise ValueError(
                        f"THIẾU PROVENANCE: Chuỗi nhãn thô không có thông tin provenance. "
                        f"Luồng nghiên cứu yêu cầu bản ghi có đầy đủ provenance và hash nội dung. "
                        f"Để tính toán từ chuỗi nhãn thô, sử dụng compute_cohens_kappa_from_labels hoặc require_provenance=False."
                    )
                sid = _extract_sid(r)
                if not sid or str(sid).strip() == "":
                    raise ValueError(f"THIẾU PROVENANCE: Bản ghi index {idx} của {r_name} thiếu hoặc rỗng 'sample_id'.")
                for req_f in provenance_check_fields:
                    val = getattr(r, req_f, None) if not isinstance(r, dict) else r.get(req_f)
                    if val is None or str(val).strip() == "":
                        raise ValueError(
                            f"THIẾU PROVENANCE: Bản ghi '{sid}' của {r_name} thiếu hoặc rỗng trường bắt buộc '{req_f}' "
                            f"trong luồng nghiên cứu."
                        )

    has_any_prov = any(
        any(
            (getattr(r, pf, None) if not isinstance(r, dict) else r.get(pf)) is not None
            and str(getattr(r, pf, None) if not isinstance(r, dict) else r.get(pf)).strip() != ""
            for pf in provenance_check_fields
        )
        for r in rater1 + rater2
    )

    has_any_sid1 = any(_extract_sid(r) is not None and str(_extract_sid(r)).strip() != "" for r in rater1)
    has_any_sid2 = any(_extract_sid(r) is not None and str(_extract_sid(r)).strip() != "" for r in rater2)

    if has_any_prov and not (has_any_sid1 and has_any_sid2):
        raise ValueError("Tập dữ liệu có thông tin provenance nhưng thiếu 'sample_id' để đối chiếu từng cặp.")

    if has_any_sid1 or has_any_sid2:
        if not all(_extract_sid(r) is not None and str(_extract_sid(r)).strip() != "" for r in rater1):
            raise ValueError("THIẾU PROVENANCE: Tập nhãn của rater1 có bản ghi thiếu hoặc rỗng 'sample_id'.")
        if not all(_extract_sid(r) is not None and str(_extract_sid(r)).strip() != "" for r in rater2):
            raise ValueError("THIẾU PROVENANCE: Tập nhãn của rater2 có bản ghi thiếu hoặc rỗng 'sample_id'.")

        dict2 = {str(_extract_sid(r)).strip(): r for r in rater2}
        if len(dict2) != len(rater2):
            raise ValueError("Phát hiện sample_id trùng lặp trong danh sách rater2.")
        dict1 = {str(_extract_sid(r)).strip(): r for r in rater1}
        if len(dict1) != len(rater1):
            raise ValueError("Phát hiện sample_id trùng lặp trong danh sách rater1.")
        if set(dict1.keys()) != set(dict2.keys()):
            raise ValueError("Danh sách sample_id giữa hai đánh giá viên không khớp nhau.")

        # Sắp xếp ổn định tất định theo sample_id
        orig_sids = [str(_extract_sid(r)).strip() for r in rater1]
        sorted_sids = sorted(list(dict1.keys()))
        orig_indices = {sid: idx for idx, sid in enumerate(orig_sids)}

        rater1 = [dict1[sid] for sid in sorted_sids]
        rater2 = [dict2[sid] for sid in sorted_sids]

        if random_subset is not None:
            random_subset = [random_subset[orig_indices[sid]] for sid in sorted_sids]
        if is_difficult is not None:
            is_difficult = [is_difficult[orig_indices[sid]] for sid in sorted_sids]

        # Kiểm tra tính đồng nhất về provenance: Cấm đa gói / đa codebook / đa sampling-plan
        provenance_fields = [
            "dataset_id",
            "dataset_hash",
            "codebook_hash",
            "codebook_version",
            "sampling_plan_version",
            "is_synthetic",
        ]
        for field in provenance_fields:
            vals1 = [getattr(r, field, None) if not isinstance(r, dict) else r.get(field) for r in rater1]
            vals2 = [getattr(r, field, None) if not isinstance(r, dict) else r.get(field) for r in rater2]
            clean_v1 = {v for v in vals1 if v is not None and str(v).strip() != ""}
            clean_v2 = {v for v in vals2 if v is not None and str(v).strip() != ""}
            if len(clean_v1) > 1 or len(clean_v2) > 1:
                raise ValueError(
                    f"LỖI ĐA GÓI: Tập dữ liệu tính Kappa chứa bản ghi từ nhiều '{field}' khác nhau "
                    f"(rater1: {clean_v1}, rater2: {clean_v2}). Mỗi lần tính chỉ được chạy trên duy nhất một gói."
                )
            # Yêu cầu provenance đầy đủ và thống nhất trong toàn tập: không cho phép bản ghi bị thiếu khi tập có khai báo
            if clean_v1 or clean_v2:
                if any(v is None or str(v).strip() == "" for v in vals1):
                    raise ValueError(
                        f"THIẾU PROVENANCE: Tập nhãn của rater1 có bản ghi thiếu hoặc rỗng trường '{field}'."
                    )
                if any(v is None or str(v).strip() == "" for v in vals2):
                    raise ValueError(
                        f"THIẾU PROVENANCE: Tập nhãn của rater2 có bản ghi thiếu hoặc rỗng trường '{field}'."
                    )
                if clean_v1 != clean_v2:
                    raise ValueError(
                        f"Không thể tính Kappa: mâu thuẫn provenance '{field}' giữa hai đánh giá viên "
                        f"({clean_v1} vs {clean_v2})."
                    )

        # Kiểm tra tính đầy đủ và thống nhất của sample_content_hash
        sh1 = [getattr(r, "sample_content_hash", None) if not isinstance(r, dict) else r.get("sample_content_hash") for r in rater1]
        sh2 = [getattr(r, "sample_content_hash", None) if not isinstance(r, dict) else r.get("sample_content_hash") for r in rater2]
        has_hash1 = any(h is not None and str(h).strip() != "" for h in sh1)
        has_hash2 = any(h is not None and str(h).strip() != "" for h in sh2)
        if has_hash1 or has_hash2:
            if any(h is None or str(h).strip() == "" for h in sh1):
                raise ValueError(
                    "THIẾU PROVENANCE: Tập nhãn của rater1 có bản ghi thiếu hoặc rỗng trường 'sample_content_hash'."
                )
            if any(h is None or str(h).strip() == "" for h in sh2):
                raise ValueError(
                    "THIẾU PROVENANCE: Tập nhãn của rater2 có bản ghi thiếu hoặc rỗng trường 'sample_content_hash'."
                )

        # Kiểm tra từng cặp nhãn khớp đúng provenance và sample_content_hash theo sample_id
        for sid, r1, r2 in zip(sorted_sids, rater1, rater2):
            h1 = getattr(r1, "sample_content_hash", None) if not isinstance(r1, dict) else r1.get("sample_content_hash")
            h2 = getattr(r2, "sample_content_hash", None) if not isinstance(r2, dict) else r2.get("sample_content_hash")
            h1_str = str(h1).strip() if h1 is not None else ""
            h2_str = str(h2).strip() if h2 is not None else ""
            if (h1_str or h2_str) and h1_str != h2_str:
                raise ValueError(
                    f"MÂU THUẪN NỘI DUNG MẪU: Cặp mẫu '{sid}' có sample_content_hash không khớp giữa hai đánh giá viên "
                    f"('{h1}' vs '{h2}')."
                )
            for pf in provenance_fields:
                v1 = getattr(r1, pf, None) if not isinstance(r1, dict) else r1.get(pf)
                v2 = getattr(r2, pf, None) if not isinstance(r2, dict) else r2.get(pf)
                v1_str = str(v1).strip() if v1 is not None else ""
                v2_str = str(v2).strip() if v2 is not None else ""
                if (v1_str or v2_str) and v1_str != v2_str:
                    raise ValueError(
                        f"MÂU THUẪN PROVENANCE: Cặp mẫu '{sid}' có '{pf}' không khớp giữa A và B "
                        f"('{v1}' vs '{v2}')."
                    )

    # Lọc bỏ các ca khó, bản ghi dry-run và dữ liệu mô phỏng
    clean_pairs = []
    for index, (r1, r2) in enumerate(zip(rater1, rater2)):
        is_dr1 = getattr(r1, "is_dry_run", False) or (isinstance(r1, dict) and r1.get("is_dry_run", False))
        is_dr2 = getattr(r2, "is_dry_run", False) or (isinstance(r2, dict) and r2.get("is_dry_run", False))
        if not allow_dry_run and (is_dr1 or is_dr2):
            continue

        is_syn1 = getattr(r1, "is_synthetic", False) or (isinstance(r1, dict) and r1.get("is_synthetic", False))
        is_syn2 = getattr(r2, "is_synthetic", False) or (isinstance(r2, dict) and r2.get("is_synthetic", False))
        if not allow_synthetic and (is_syn1 or is_syn2):
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
        raise ValueError("Không còn mẫu ngẫu nhiên hợp lệ nào sau khi loại bỏ ca khó, bản ghi dry-run và dữ liệu mô phỏng.")

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


def filter_research_annotations(
    records: Sequence[Any],
    *,
    allow_synthetic: bool = False,
    allow_dry_run: bool = False,
) -> List[Any]:
    """Lọc các bản ghi dùng cho thống kê nghiên cứu khoa học, loại bỏ dữ liệu mô phỏng và dry-run."""
    filtered = []
    for r in records:
        is_dry = getattr(r, "is_dry_run", False) or (isinstance(r, dict) and r.get("is_dry_run", False))
        is_synth = getattr(r, "is_synthetic", False) or (isinstance(r, dict) and r.get("is_synthetic", False))
        if not allow_dry_run and is_dry:
            continue
        if not allow_synthetic and is_synth:
            continue
        filtered.append(r)
    return filtered


def compute_cohens_kappa_from_labels(
    labels1: Sequence[str],
    labels2: Sequence[str],
    *,
    is_difficult: Sequence[bool] | None = None,
    random_subset: Sequence[bool] | None = None,
    allow_dry_run: bool = True,
    allow_synthetic: bool = True,
) -> KappaResult:
    """Tính chỉ số thỏa thuận Cohen's Kappa từ danh sách chuỗi nhãn thô (dùng riêng cho unit test/toán học).

    TÁCH BIỆT RẠCH RÒI KHỎI LUỒNG NGHIÊN CỨU:
    Luồng nghiên cứu chính thức BẮT BUỘC dùng compute_cohens_kappa với require_provenance=True.
    """
    return compute_cohens_kappa(
        labels1,
        labels2,
        is_difficult=is_difficult,
        random_subset=random_subset,
        allow_dry_run=allow_dry_run,
        allow_synthetic=allow_synthetic,
        require_provenance=False,
    )


__all__ = [
    "compute_cohens_kappa",
    "compute_cohens_kappa_from_labels",
    "KappaResult",
    "filter_research_annotations",
    "AnnotationRecord",
    "BlindSample",
    "assert_neutral_sample_id",
    "assert_no_label_leak",
    "compute_sample_content_hash",
    "create_blind_sample",
    "export_blind_view",
    "extract_safe_view_content",
    "validate_annotation_record",
]

