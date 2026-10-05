"""Module phân chia tập dữ liệu chống rò rỉ (Anti-Leakage Data Splitting Engine).

Triển khai theo quy chuẩn nghiêm ngặt của NCKH_2:
- EXPERIMENT_PROTOCOL.md: Grouped 5-fold CV lặp 3 seed (17, 42, 2026), inner validation split.
- DATA_PROTOCOL.md: eTLD+1 + shared hosting tenant grouping, bảo toàn component trùng nội dung,
  không rò rỉ group giữa train và test.
- Strict Record Validation: Bắt buộc sample_id duy nhất toàn cục, từ chối ID rỗng/trùng lặp,
  từ chối URL/nhóm hỏng; nghiêm cấm tự sinh row:<idx>.
- Usability & Class Sufficiency: Cân bằng nhãn theo nhóm, kiểm tra outer train/val/test và inner train
  không được rỗng, kiểm tra độ phủ lớp học máy (phishing / benign).
- Temporal Split: 60% Train / 20% Val / 20% Test, kiểm tra tham số nghiêm ngặt, không chia cắt
  cùng một ngày lịch, loại trừ trùng nhóm sớm, gắn trạng thái evaluable / not_evaluable rõ ràng.
"""

from collections import Counter, defaultdict
from datetime import date
import math
import random
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from phishing.data.date_parser import parse_strict_date
from phishing.data.grouping import extract_group_id

# 3 Random seed định trước theo đề cương và giao thức thực nghiệm
DEFAULT_SEEDS: Tuple[int, ...] = (17, 42, 2026)


def assert_no_group_leakage(
    train_groups: Iterable[str],
    test_groups: Iterable[str],
    context: str = "",
) -> None:
    """Kiểm tra và đảm bảo không có bất kỳ group_id nào xuất hiện đồng thời ở cả hai tập.

    Ném ra ValueError nếu phát hiện rò rỉ dữ liệu (Data Leakage).
    """
    train_set = set(train_groups)
    test_set = set(test_groups)
    intersection = train_set.intersection(test_set)

    if intersection:
        sample_leaks = sorted(intersection)[:5]
        msg = (
            f"DATA LEAKAGE DETECTED {context}: {len(intersection)} groups found in both sets! "
            f"Sample leaking groups: {sample_leaks}"
        )
        raise ValueError(msg)


def assert_strict_temporal_order(
    train_dates: Sequence[date],
    val_dates: Sequence[date],
    test_dates: Sequence[date],
) -> None:
    """Kiểm tra và đảm bảo tính tuần tự nghiêm ngặt của thời gian giữa các tập.

    Yêu cầu: max(train) < min(val) và max(val) < min(test).
    Tuyệt đối không để ngày ở tương lai xuất hiện trong quá khứ hoặc cắt ngang cùng một ngày.
    """
    if not train_dates or not val_dates or not test_dates:
        raise ValueError("Train, validation and test date collections must not be empty.")

    max_train = max(train_dates)
    min_val = min(val_dates)
    max_val = max(val_dates)
    min_test = min(test_dates)

    if max_train >= min_val:
        raise ValueError(
            f"Temporal order violated between Train and Val: "
            f"train max date ({max_train}) >= val min date ({min_val}). "
            f"Samples from the same calendar day must not be split across partitions."
        )

    if max_val >= min_test:
        raise ValueError(
            f"Temporal order violated between Val and Test: "
            f"val max date ({max_val}) >= test min date ({min_test}). "
            f"Samples from the same calendar day must not be split across partitions."
        )


def _validate_and_extract_record(
    idx: int,
    rec: Mapping[str, Any],
    id_field: str,
    url_field: str,
    group_field: Optional[str],
    label_field: Optional[str],
    seen_ids: Set[str],
) -> Tuple[str, str, str]:
    """Kiểm định tính toàn vẹn bản ghi trước mọi thao tác phân chia:

    1. ID bắt buộc có mặt, là chuỗi không rỗng, và duy nhất toàn cục.
    2. Nhận group_id/component index đã kiểm chứng nếu có sẵn, không tự chia lẻ theo URL.
    3. Nếu không có group_id, URL phải hợp lệ để trích xuất group_id (từ chối unknown).
    4. Tuyệt đối không tự sinh row:<idx> thành nhóm độc lập.
    """
    raw_sid = rec.get(id_field)
    if raw_sid is None:
        raise ValueError(f"Record #{idx} is missing mandatory ID field '{id_field}'.")

    if not isinstance(raw_sid, str) or isinstance(raw_sid, bool):
        raise TypeError(f"Record #{idx} '{id_field}' must be a non-empty string, got {type(raw_sid).__name__}.")

    sid = raw_sid.strip()
    if not sid:
        raise ValueError(f"Record #{idx} has empty ID field '{id_field}'.")

    if sid in seen_ids:
        raise ValueError(f"Duplicate sample_id detected: '{sid}'. All records must have globally unique IDs.")
    seen_ids.add(sid)

    # Ưu tiên nhận group_id hoặc component index đã kiểm chứng từ đầu vào
    gid = ""
    if group_field and group_field in rec and rec[group_field] is not None:
        raw_gid = rec[group_field]
        if not isinstance(raw_gid, str) or isinstance(raw_gid, bool):
            raise TypeError(f"Record '{sid}' '{group_field}' must be a string, got {type(raw_gid).__name__}.")
        cand_gid = raw_gid.strip()
        if not cand_gid or cand_gid == "unknown" or any(c.isspace() for c in cand_gid):
            raise ValueError(f"Record '{sid}' has invalid '{group_field}': {raw_gid!r}.")
        gid = cand_gid

    if not gid:
        raw_url = rec.get(url_field)
        if raw_url is None:
            raise ValueError(
                f"Record '{sid}' missing valid '{group_field}' and has no '{url_field}'. "
                f"Silent fallback to 'row:<idx>' is strictly forbidden."
            )
        if not isinstance(raw_url, str) or isinstance(raw_url, bool):
            raise TypeError(f"Record '{sid}' '{url_field}' must be a string, got {type(raw_url).__name__}.")
        cand_url = raw_url.strip()
        if not cand_url:
            raise ValueError(
                f"Record '{sid}' missing valid '{group_field}' and has no '{url_field}' (URL is empty). "
                f"Silent fallback to 'row:<idx>' is strictly forbidden."
            )
        gid = extract_group_id(cand_url)
        if gid == "unknown" or any(c.isspace() for c in gid):
            raise ValueError(
                f"Record '{sid}' has invalid URL '{cand_url}' that cannot be mapped to a valid group."
            )

    lbl = "unlabeled"
    if label_field and label_field in rec and rec[label_field] is not None:
        raw_lbl = rec[label_field]
        cand_lbl = str(raw_lbl).strip()
        if cand_lbl:
            lbl = cand_lbl

    return sid, gid, lbl


def generate_grouped_kfold(
    records: Sequence[Mapping[str, Any]],
    n_splits: int = 5,
    seeds: Sequence[int] = DEFAULT_SEEDS,
    id_field: str = "sample_id",
    url_field: str = "url",
    group_field: Optional[str] = "group_id",
    label_field: Optional[str] = "class_label",
) -> Dict[int, List[Dict[str, Any]]]:
    """Tạo phân chia Grouped K-Fold Cross Validation với nhiều random seeds.

    Mỗi URL/mẫu được gán group_id (theo eTLD+1 hoặc tenant dịch vụ dùng chung).
    Toàn bộ các mẫu cùng group_id bắt buộc nằm trọn vẹn trong một fold.
    Đồng thời phân chia inner validation fold bên trong outer train để phục vụ
    tinh chỉnh ngưỡng operating threshold mà không làm lộ outer test.

    Trả về:
        Dict mapping từ seed (17, 42, 2026) -> List gồm n_splits thông số fold.
    """
    if not records:
        raise ValueError("Records sequence cannot be empty.")
    if not seeds:
        raise ValueError("seeds list cannot be empty. At least one seed is required.")
    if len(seeds) != len(set(seeds)):
        raise ValueError(f"Duplicate seeds detected: {seeds}. Seeds must be unique.")
    if n_splits < 3:
        raise ValueError(
            f"n_splits must be at least 3 (got {n_splits}) to support outer test "
            f"and non-empty inner train/validation folds."
        )

    # 1. Thu thập group_id và ánh xạ mẫu có kiểm định toàn vẹn nghiêm ngặt
    seen_ids: Set[str] = set()
    sample_to_group: Dict[str, str] = {}
    sample_to_label: Dict[str, str] = {}
    sample_to_source: Dict[str, str] = {}
    group_to_samples: Dict[str, List[str]] = defaultdict(list)
    group_label_counts: Dict[str, Counter] = defaultdict(Counter)

    for idx, rec in enumerate(records):
        sid, gid, lbl = _validate_and_extract_record(
            idx=idx,
            rec=rec,
            id_field=id_field,
            url_field=url_field,
            group_field=group_field,
            label_field=label_field,
            seen_ids=seen_ids,
        )
        sample_to_group[sid] = gid
        sample_to_label[sid] = lbl
        # Thu thập thông tin nguồn nếu có
        source_val = rec.get("source") or rec.get("source_id") or "default"
        sample_to_source[sid] = str(source_val).strip()
        group_to_samples[gid].append(sid)
        group_label_counts[gid][lbl] += 1

    distinct_groups = sorted(group_to_samples.keys())
    if len(distinct_groups) < n_splits:
        raise ValueError(
            f"Cannot create {n_splits} grouped folds with only {len(distinct_groups)} distinct groups."
        )

    # Đếm tổng nhãn toàn corpus để kiểm tra tính khả dụng của các fold
    all_corpus_labels = sorted({lbl for lbl in sample_to_label.values() if lbl != "unlabeled"})
    has_labels = len(all_corpus_labels) > 0
    all_sources = sorted({s for s in sample_to_source.values()})
    has_multi_source = len(all_sources) > 1

    # Xác định các lớp mục tiêu bắt buộc (phishing vs benign cho bài toán phát hiện lừa đảo)
    target_classes: List[str]
    if any(lbl.lower() in {"phishing", "phish", "benign"} for lbl in all_corpus_labels):
        target_classes = ["phishing", "benign"]
    elif has_labels:
        target_classes = all_corpus_labels
    else:
        target_classes = []

    all_seed_results: Dict[int, List[Dict[str, Any]]] = {}

    for seed in seeds:
        rng = random.Random(seed)

        # Trộn ngẫu nhiên danh sách nhóm trước theo seed
        shuffled_groups = list(distinct_groups)
        shuffled_groups.sort()  # deterministic base sort
        rng.shuffle(shuffled_groups)

        # Sắp xếp nhóm lớn trước (greedy bin-packing) để cân bằng số lượng mẫu giữa các fold
        shuffled_groups.sort(key=lambda g: len(group_to_samples[g]), reverse=True)

        fold_groups: List[List[str]] = [[] for _ in range(n_splits)]
        fold_sample_counts = [0] * n_splits
        # Theo dõi số lượng mẫu nhãn đầu tiên (nếu có) để cân bằng lớp
        primary_label = target_classes[0] if target_classes else (all_corpus_labels[0] if has_labels else None)
        fold_primary_counts = [0] * n_splits

        for gid in shuffled_groups:
            # Gán group vào fold hiện đang có ít mẫu nhất, ưu tiên fold thiếu nhãn chính
            if primary_label and group_label_counts[gid][primary_label] > 0:
                best_fold_idx = min(
                    range(n_splits),
                    key=lambda i: (fold_primary_counts[i], fold_sample_counts[i]),
                )
            else:
                best_fold_idx = min(range(n_splits), key=lambda i: fold_sample_counts[i])

            fold_groups[best_fold_idx].append(gid)
            fold_sample_counts[best_fold_idx] += len(group_to_samples[gid])
            if primary_label:
                fold_primary_counts[best_fold_idx] += group_label_counts[gid][primary_label]

        fold_results: List[Dict[str, Any]] = []

        for k in range(n_splits):
            test_grp_set = set(fold_groups[k])
            train_grp_set: Set[str] = set()
            for other_k in range(n_splits):
                if other_k != k:
                    train_grp_set.update(fold_groups[other_k])

            # Kiểm định chống rò rỉ dữ liệu mức outer
            assert_no_group_leakage(train_grp_set, test_grp_set, f"Seed {seed} Fold {k}")

            train_samples: List[str] = []
            test_samples: List[str] = []

            for gid in sorted(train_grp_set):
                train_samples.extend(group_to_samples[gid])
            for gid in sorted(test_grp_set):
                test_samples.extend(group_to_samples[gid])

            # Tạo inner validation split bên trong outer train:
            # Chọn 1 trong các fold còn lại làm inner validation (ví dụ fold liền kề k+1 mod n_splits)
            inner_val_k = (k + 1) % n_splits
            inner_val_grp_set = set(fold_groups[inner_val_k])
            inner_train_grp_set = train_grp_set - inner_val_grp_set

            # Kiểm định chống rò rỉ dữ liệu mức inner
            assert_no_group_leakage(inner_train_grp_set, inner_val_grp_set, f"Seed {seed} Fold {k} Inner")

            inner_train_samples: List[str] = []
            inner_val_samples: List[str] = []
            for gid in sorted(inner_train_grp_set):
                inner_train_samples.extend(group_to_samples[gid])
            for gid in sorted(inner_val_grp_set):
                inner_val_samples.extend(group_to_samples[gid])

            # Kiểm tra tính khả dụng: Không được để fold nào bị rỗng
            if not test_samples:
                raise ValueError(f"Fold {k} test set is empty.")
            if not train_samples:
                raise ValueError(f"Fold {k} train set is empty.")
            if not inner_train_samples:
                raise ValueError(f"Fold {k} inner train set is empty.")
            if not inner_val_samples:
                raise ValueError(f"Fold {k} inner val set is empty.")

            train_label_dist = Counter(sample_to_label[s] for s in train_samples)
            test_label_dist = Counter(sample_to_label[s] for s in test_samples)
            inner_train_label_dist = Counter(sample_to_label[s] for s in inner_train_samples)
            inner_val_label_dist = Counter(sample_to_label[s] for s in inner_val_samples)

            # Kiểm tra tính đầy đủ của lớp (Class Sufficiency) trên CẢ 4 phân vùng:
            # outer_train, outer_test, inner_train, inner_val
            missing_outer_train = [lbl for lbl in target_classes if train_label_dist.get(lbl, 0) == 0]
            missing_outer_test = [lbl for lbl in target_classes if test_label_dist.get(lbl, 0) == 0]
            missing_inner_train = [lbl for lbl in target_classes if inner_train_label_dist.get(lbl, 0) == 0]
            missing_inner_val = [lbl for lbl in target_classes if inner_val_label_dist.get(lbl, 0) == 0]

            is_usable = True
            unusable_reasons: List[str] = []

            if not has_labels:
                class_status = "unlabeled"
            elif len(all_corpus_labels) < 2:
                class_status = "insufficient_classes"
                is_usable = False
                unusable_reasons.append(
                    f"Corpus lacks binary classes (found only {all_corpus_labels}; both phishing and benign required)"
                )
            elif missing_outer_train or missing_outer_test or missing_inner_train or missing_inner_val:
                class_status = "insufficient_classes"
                is_usable = False
                if missing_outer_train:
                    unusable_reasons.append(f"outer_train missing {missing_outer_train}")
                if missing_outer_test:
                    unusable_reasons.append(f"outer_test missing {missing_outer_test}")
                if missing_inner_train:
                    unusable_reasons.append(f"inner_train missing {missing_inner_train}")
                if missing_inner_val:
                    unusable_reasons.append(f"inner_val missing {missing_inner_val}")
            else:
                class_status = "sufficient"

            # Kiểm tra phân bố lớp theo nguồn (nếu có đa nguồn dữ liệu gộp)
            source_sufficiency: Dict[str, Any] = {}
            if has_multi_source:
                train_sources = Counter(sample_to_source[s] for s in train_samples)
                test_sources = Counter(sample_to_source[s] for s in test_samples)
                missing_sources_test = [s for s in all_sources if test_sources.get(s, 0) == 0]
                source_sufficiency = {
                    "all_sources": all_sources,
                    "train_sources": dict(train_sources),
                    "test_sources": dict(test_sources),
                    "missing_in_test": missing_sources_test,
                }

            fold_results.append({
                "fold": k,
                "seed": seed,
                "is_usable": is_usable,
                "unusable_reason": "; ".join(unusable_reasons) if unusable_reasons else None,
                "train_indices": sorted(train_samples),
                "test_indices": sorted(test_samples),
                "inner_train_indices": sorted(inner_train_samples),
                "inner_val_indices": sorted(inner_val_samples),
                "train_groups": sorted(train_grp_set),
                "test_groups": sorted(test_grp_set),
                "inner_train_groups": sorted(inner_train_grp_set),
                "inner_val_groups": sorted(inner_val_grp_set),
                "class_sufficiency": {
                    "status": class_status,
                    "target_classes": target_classes,
                    "missing_in_outer_train": missing_outer_train,
                    "missing_in_outer_test": missing_outer_test,
                    "missing_in_inner_train": missing_inner_train,
                    "missing_in_inner_val": missing_inner_val,
                },
                "source_sufficiency": source_sufficiency,
                "metrics": {
                    "train_sample_count": len(train_samples),
                    "test_sample_count": len(test_samples),
                    "inner_train_sample_count": len(inner_train_samples),
                    "inner_val_sample_count": len(inner_val_samples),
                    "train_groups_count": len(train_grp_set),
                    "test_groups_count": len(test_grp_set),
                    "train_label_distribution": dict(train_label_dist),
                    "test_label_distribution": dict(test_label_dist),
                    "inner_train_label_distribution": dict(inner_train_label_dist),
                    "inner_val_label_distribution": dict(inner_val_label_dist),
                },
            })

        all_seed_results[seed] = fold_results

    return all_seed_results


def generate_temporal_split(
    records: Sequence[Mapping[str, Any]],
    train_ratio: float = 0.6,
    val_ratio: float = 0.2,
    test_ratio: float = 0.2,
    id_field: str = "sample_id",
    date_field: str = "collected_at",
    url_field: str = "url",
    group_field: Optional[str] = "group_id",
    label_field: Optional[str] = "class_label",
    purge_overlapping_groups: bool = True,
) -> Dict[str, Any]:
    """Tạo phân chia mốc thời gian (Temporal Split) 60/20/20 tuân thủ nguyên tắc ARS:

    1. Sắp xếp thứ tự thời gian theo ngày lịch (calendar date).
    2. Tuyệt đối không chia tách các bản ghi trong cùng một ngày lịch.
    3. Điểm cắt được tính toán để tỷ lệ tích lũy xấp xỉ 60% Train, 20% Val, 20% Test.
    4. Chống rò rỉ miền/nhóm từ quá khứ sang tương lai:
       Nếu purge_overlapping_groups=True, các bản ghi ở tập Val/Test có group_id đã từng
       xuất hiện trong tập sớm hơn sẽ bị loại bỏ khỏi tập đánh giá sạch ("Loại bản ghi muộn trùng group sớm").
    5. Kiểm định chặt chẽ tỷ lệ đầu vào (dương, hữu hạn, tổng bằng 1.0).
    6. Đánh giá tính khả dụng (evaluability): Nếu sau khi purge mà tập Val hoặc Test bị rỗng
       hoặc thiếu lớp học máy, chuyển trạng thái sang "not_evaluable" kèm lý do chi tiết.
    """
    if not records:
        raise ValueError("Records sequence cannot be empty.")

    # 1. Kiểm định các tham số tỷ lệ nghiêm ngặt
    for r_val, r_name in [(train_ratio, "train_ratio"), (val_ratio, "val_ratio"), (test_ratio, "test_ratio")]:
        if not isinstance(r_val, (int, float)) or not math.isfinite(r_val) or r_val <= 0 or r_val >= 1:
            raise ValueError(f"{r_name} must be a finite positive number between 0 and 1, got {r_val}")

    if abs((train_ratio + val_ratio + test_ratio) - 1.0) > 1e-5:
        raise ValueError(
            f"train_ratio ({train_ratio}), val_ratio ({val_ratio}), and test_ratio ({test_ratio}) "
            f"must sum to 1.0 (got {train_ratio + val_ratio + test_ratio:.6f})."
        )

    # 2. Trích xuất và xác thực bản ghi cùng trường ngày
    seen_ids: Set[str] = set()
    valid_entries: List[Dict[str, Any]] = []
    invalid_date_count = 0

    for idx, rec in enumerate(records):
        sid, gid, lbl = _validate_and_extract_record(
            idx=idx,
            rec=rec,
            id_field=id_field,
            url_field=url_field,
            group_field=group_field,
            label_field=label_field,
            seen_ids=seen_ids,
        )
        d_val = parse_strict_date(rec.get(date_field))
        if d_val is None:
            invalid_date_count += 1
            continue

        valid_entries.append({
            "sample_id": sid,
            "date": d_val,
            "group_id": gid,
            "label": lbl,
            "raw_record": rec,
        })

    if not valid_entries:
        raise ValueError(
            f"No valid dates found in records using field '{date_field}'. "
            f"Encountered {invalid_date_count} invalid/missing dates."
        )

    # Nhóm theo ngày lịch
    date_to_entries: Dict[date, List[Dict[str, Any]]] = defaultdict(list)
    for entry in valid_entries:
        date_to_entries[entry["date"]].append(entry)

    sorted_dates = sorted(date_to_entries.keys())
    if len(sorted_dates) < 3:
        raise ValueError(
            f"Need at least 3 distinct calendar dates to perform temporal split (60/20/20), "
            f"got {len(sorted_dates)} distinct dates."
        )

    total_valid = len(valid_entries)
    target_train_count = max(1, round(train_ratio * total_valid))
    target_val_cum_count = max(target_train_count + 1, round((train_ratio + val_ratio) * total_valid))

    # Tìm điểm cắt ngày T1 (Train) và T2 (Val)
    cum_count = 0
    train_dates: List[date] = []
    val_dates: List[date] = []
    test_dates: List[date] = []

    train_cutoff_idx = 0
    val_cutoff_idx = 1

    # Phân bổ ngày vào 3 phần
    for i, d in enumerate(sorted_dates):
        count_d = len(date_to_entries[d])
        # Đảm bảo ít nhất 1 ngày cho val và ít nhất 1 ngày cho test
        remaining_dates = len(sorted_dates) - 1 - i
        if (cum_count + count_d <= target_train_count or len(train_dates) == 0) and remaining_dates >= 2:
            train_dates.append(d)
            train_cutoff_idx = i
        elif (cum_count + count_d <= target_val_cum_count or len(val_dates) == 0) and remaining_dates >= 1:
            val_dates.append(d)
            val_cutoff_idx = i
        else:
            test_dates.append(d)
        cum_count += count_d

    # Nếu vì lý do làm tròn mà test_dates bị rỗng, tái cân bằng ngày cuối
    if not test_dates and len(val_dates) > 1:
        test_dates.append(val_dates.pop())

    # Kiểm tra trật tự thời gian nghiêm ngặt
    assert_strict_temporal_order(train_dates, val_dates, test_dates)

    # Gom các bản ghi thô theo phân vùng
    raw_train_entries: List[Dict[str, Any]] = []
    for d in train_dates:
        raw_train_entries.extend(date_to_entries[d])

    raw_val_entries: List[Dict[str, Any]] = []
    for d in val_dates:
        raw_val_entries.extend(date_to_entries[d])

    raw_test_entries: List[Dict[str, Any]] = []
    for d in test_dates:
        raw_test_entries.extend(date_to_entries[d])

    # 3. Chống rò rỉ nhóm từ sớm sang muộn (Purge overlapping groups)
    train_group_set = {e["group_id"] for e in raw_train_entries}

    clean_val_entries: List[Dict[str, Any]] = []
    purged_val_entries: List[Dict[str, Any]] = []

    for e in raw_val_entries:
        if purge_overlapping_groups and e["group_id"] in train_group_set:
            purged_val_entries.append(e)
        else:
            clean_val_entries.append(e)

    # Tập nhóm đã quan sát ở quá khứ (Train + Val hợp lệ)
    clean_val_group_set = {e["group_id"] for e in clean_val_entries}
    past_group_set = train_group_set.union(clean_val_group_set)

    clean_test_entries: List[Dict[str, Any]] = []
    purged_test_entries: List[Dict[str, Any]] = []

    for e in raw_test_entries:
        if purge_overlapping_groups and e["group_id"] in past_group_set:
            purged_test_entries.append(e)
        else:
            clean_test_entries.append(e)

    # Sau khi purge, kiểm định chống rò rỉ tuyệt đối nếu test không rỗng
    verification_checks: List[str] = [
        "assert_strict_temporal_order",
        "assert_unique_sample_ids",
    ]
    if purge_overlapping_groups and clean_test_entries:
        clean_test_group_set = {e["group_id"] for e in clean_test_entries}
        assert_no_group_leakage(train_group_set, clean_test_group_set, "Temporal Train vs Clean Test")
        verification_checks.append("assert_no_group_leakage(train vs clean_test)")

    all_purged_groups = sorted(
        {e["group_id"] for e in purged_val_entries}.union({e["group_id"] for e in purged_test_entries})
    )

    # 4. Đánh giá tính khả dụng (Evaluability Status)
    all_labels = sorted({e["label"] for e in valid_entries if e["label"] != "unlabeled"})
    has_labels = len(all_labels) > 0
    target_classes: List[str]
    if any(lbl.lower() in {"phishing", "phish", "benign"} for lbl in all_labels):
        target_classes = ["phishing", "benign"]
    elif has_labels:
        target_classes = all_labels
    else:
        target_classes = []

    train_labels = Counter(e["label"] for e in raw_train_entries)
    val_labels_raw = Counter(e["label"] for e in raw_val_entries)
    val_labels_clean = Counter(e["label"] for e in clean_val_entries)
    test_labels_raw = Counter(e["label"] for e in raw_test_entries)
    test_labels_clean = Counter(e["label"] for e in clean_test_entries)

    train_eval_status = "evaluable"
    train_eval_reason = None
    if len(raw_train_entries) == 0:
        train_eval_status = "not_evaluable"
        train_eval_reason = "Train set is empty"
    elif has_labels:
        if len(all_labels) < 2:
            train_eval_status = "not_evaluable"
            train_eval_reason = f"Corpus lacks binary classes (found only {all_labels}; both phishing and benign required)"
        elif any(train_labels.get(lbl, 0) == 0 for lbl in target_classes):
            train_eval_status = "not_evaluable"
            missing = [lbl for lbl in target_classes if train_labels.get(lbl, 0) == 0]
            train_eval_reason = f"Insufficient classes in train set (missing: {missing})"

    val_eval_status = "evaluable"
    val_eval_reason = None
    if len(clean_val_entries) == 0:
        val_eval_status = "not_evaluable"
        val_eval_reason = "All validation samples purged due to group overlap with train"
    elif has_labels:
        if len(all_labels) < 2:
            val_eval_status = "not_evaluable"
            val_eval_reason = f"Corpus lacks binary classes (found only {all_labels}; both phishing and benign required)"
        elif any(val_labels_clean.get(lbl, 0) == 0 for lbl in target_classes):
            val_eval_status = "not_evaluable"
            missing = [lbl for lbl in target_classes if val_labels_clean.get(lbl, 0) == 0]
            val_eval_reason = f"Insufficient classes in clean validation set (missing: {missing})"

    test_eval_status = "evaluable"
    test_eval_reason = None
    if len(clean_test_entries) == 0:
        test_eval_status = "not_evaluable"
        test_eval_reason = "All test samples purged due to group overlap with past (train/val)"
    elif has_labels:
        if len(all_labels) < 2:
            test_eval_status = "not_evaluable"
            test_eval_reason = f"Corpus lacks binary classes (found only {all_labels}; both phishing and benign required)"
        elif any(test_labels_clean.get(lbl, 0) == 0 for lbl in target_classes):
            test_eval_status = "not_evaluable"
            missing = [lbl for lbl in target_classes if test_labels_clean.get(lbl, 0) == 0]
            test_eval_reason = f"Insufficient classes in clean test set (missing: {missing})"

    overall_status = (
        "evaluable"
        if (train_eval_status == "evaluable" and val_eval_status == "evaluable" and test_eval_status == "evaluable")
        else "not_evaluable"
    )

    return {
        "status": overall_status,
        "evaluability": {
            "train": {"status": train_eval_status, "reason": train_eval_reason},
            "validation": {"status": val_eval_status, "reason": val_eval_reason},
            "test": {"status": test_eval_status, "reason": test_eval_reason},
        },
        "train_indices": [e["sample_id"] for e in raw_train_entries],
        "val_indices": [e["sample_id"] for e in clean_val_entries],
        "test_indices": [e["sample_id"] for e in clean_test_entries],
        "purged_val_indices": [e["sample_id"] for e in purged_val_entries],
        "purged_test_indices": [e["sample_id"] for e in purged_test_entries],
        "train_date_range": [train_dates[0].isoformat(), train_dates[-1].isoformat()],
        "val_date_range": [val_dates[0].isoformat(), val_dates[-1].isoformat()],
        "test_date_range": [test_dates[0].isoformat(), test_dates[-1].isoformat()],
        "cutoffs": {
            "train_cutoff_date": train_dates[-1].isoformat(),
            "val_cutoff_date": val_dates[-1].isoformat(),
        },
        "verification_checks_passed": verification_checks,
        "metrics": {
            "total_valid_records": total_valid,
            "invalid_date_count": invalid_date_count,
            "train_sample_count": len(raw_train_entries),
            "val_raw_sample_count": len(raw_val_entries),
            "val_clean_sample_count": len(clean_val_entries),
            "val_purged_sample_count": len(purged_val_entries),
            "test_raw_sample_count": len(raw_test_entries),
            "test_clean_sample_count": len(clean_test_entries),
            "test_purged_sample_count": len(purged_test_entries),
            "purged_groups_count": len(all_purged_groups),
            "train_groups_count": len(train_group_set),
            "val_clean_groups_count": len(clean_val_group_set),
            "test_clean_groups_count": len({e["group_id"] for e in clean_test_entries}),
            "labels": {
                "train": dict(Counter(e["label"] for e in raw_train_entries)),
                "val_raw": dict(val_labels_raw),
                "val_clean": dict(val_labels_clean),
                "test_raw": dict(test_labels_raw),
                "test_clean": dict(test_labels_clean),
            },
        },
    }
