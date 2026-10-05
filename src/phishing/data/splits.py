"""Module phân chia tập dữ liệu chống rò rỉ (Anti-Leakage Data Splitting Engine).

Triển khai theo quy chuẩn nghiêm ngặt của NCKH_2:
- EXPERIMENT_PROTOCOL.md: Grouped 5-fold CV lặp 3 seed (17, 42, 2026), inner validation split.
- DATA_PROTOCOL.md: eTLD+1 + shared hosting tenant grouping, không rò rỉ group giữa train và test.
- Temporal Split: 60% Train / 20% Val / 20% Test, không chia cắt trong cùng một ngày lịch.
  Loại bỏ các bản ghi muộn trùng group sớm ("Loại bản ghi muộn trùng group sớm").
"""

from collections import Counter, defaultdict
from datetime import date
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


def generate_grouped_kfold(
    records: Sequence[Mapping[str, Any]],
    n_splits: int = 5,
    seeds: Sequence[int] = DEFAULT_SEEDS,
    id_field: str = "sample_id",
    url_field: str = "url",
    group_field: Optional[str] = None,
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
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2.")

    # 1. Thu thập group_id và ánh xạ mẫu
    sample_to_group: Dict[Any, str] = {}
    sample_to_label: Dict[Any, str] = {}
    group_to_samples: Dict[str, List[Any]] = defaultdict(list)
    group_label_counts: Dict[str, Counter] = defaultdict(Counter)

    for idx, rec in enumerate(records):
        sample_id = rec.get(id_field, idx)
        if group_field and group_field in rec and rec[group_field]:
            gid = str(rec[group_field])
        elif url_field in rec and rec[url_field]:
            gid = extract_group_id(str(rec[url_field]))
        else:
            gid = f"row:{idx}"

        lbl = str(rec.get(label_field, "unlabeled")) if label_field else "unlabeled"

        sample_to_group[sample_id] = gid
        sample_to_label[sample_id] = lbl
        group_to_samples[gid].append(sample_id)
        group_label_counts[gid][lbl] += 1

    distinct_groups = sorted(group_to_samples.keys())
    if len(distinct_groups) < n_splits:
        raise ValueError(
            f"Cannot create {n_splits} grouped folds with only {len(distinct_groups)} distinct groups."
        )

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

        for gid in shuffled_groups:
            # Gán group vào fold hiện đang có ít mẫu nhất
            min_fold_idx = min(range(n_splits), key=lambda i: fold_sample_counts[i])
            fold_groups[min_fold_idx].append(gid)
            fold_sample_counts[min_fold_idx] += len(group_to_samples[gid])

        fold_results: List[Dict[str, Any]] = []

        for k in range(n_splits):
            test_grp_set = set(fold_groups[k])
            train_grp_set: Set[str] = set()
            for other_k in range(n_splits):
                if other_k != k:
                    train_grp_set.update(fold_groups[other_k])

            # Kiểm định chống rò rỉ dữ liệu mức outer
            assert_no_group_leakage(train_grp_set, test_grp_set, f"Seed {seed} Fold {k}")

            train_samples: List[Any] = []
            test_samples: List[Any] = []

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

            inner_train_samples: List[Any] = []
            inner_val_samples: List[Any] = []
            for gid in sorted(inner_train_grp_set):
                inner_train_samples.extend(group_to_samples[gid])
            for gid in sorted(inner_val_grp_set):
                inner_val_samples.extend(group_to_samples[gid])

            train_label_dist = Counter(sample_to_label[s] for s in train_samples)
            test_label_dist = Counter(sample_to_label[s] for s in test_samples)

            fold_results.append({
                "fold": k,
                "seed": seed,
                "train_indices": sorted(train_samples, key=lambda s: str(s)),
                "test_indices": sorted(test_samples, key=lambda s: str(s)),
                "inner_train_indices": sorted(inner_train_samples, key=lambda s: str(s)),
                "inner_val_indices": sorted(inner_val_samples, key=lambda s: str(s)),
                "train_groups": sorted(train_grp_set),
                "test_groups": sorted(test_grp_set),
                "inner_train_groups": sorted(inner_train_grp_set),
                "inner_val_groups": sorted(inner_val_grp_set),
                "metrics": {
                    "train_sample_count": len(train_samples),
                    "test_sample_count": len(test_samples),
                    "inner_train_sample_count": len(inner_train_samples),
                    "inner_val_sample_count": len(inner_val_samples),
                    "train_groups_count": len(train_grp_set),
                    "test_groups_count": len(test_grp_set),
                    "train_label_distribution": dict(train_label_dist),
                    "test_label_distribution": dict(test_label_dist),
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
    group_field: Optional[str] = None,
    purge_overlapping_groups: bool = True,
) -> Dict[str, Any]:
    """Tạo phân chia mốc thời gian (Temporal Split) 60/20/20 tuân thủ nguyên tắc ARS:

    1. Sắp xếp thứ tự thời gian theo ngày lịch (calendar date).
    2. Tuyệt đối không chia tách các bản ghi trong cùng một ngày lịch.
    3. Điểm cắt được tính toán để tỷ lệ tích lũy xấp xỉ 60% Train, 20% Val, 20% Test.
    4. Chống rò rỉ miền/nhóm từ quá khứ sang tương lai:
       Nếu purge_overlapping_groups=True, các bản ghi ở tập Val/Test có group_id đã từng
       xuất hiện trong tập sớm hơn sẽ bị loại bỏ khỏi tập đánh giá sạch ("Loại bản ghi muộn trùng group sớm").
    """
    if not records:
        raise ValueError("Records sequence cannot be empty.")

    # 1. Trích xuất và xác thực ngày cho từng bản ghi
    valid_entries: List[Dict[str, Any]] = []
    invalid_date_count = 0

    for idx, rec in enumerate(records):
        sample_id = rec.get(id_field, idx)
        d_val = parse_strict_date(rec.get(date_field))
        if d_val is None:
            invalid_date_count += 1
            continue

        if group_field and group_field in rec and rec[group_field]:
            gid = str(rec[group_field])
        elif url_field in rec and rec[url_field]:
            gid = extract_group_id(str(rec[url_field]))
        else:
            gid = f"row:{idx}"

        valid_entries.append({
            "sample_id": sample_id,
            "date": d_val,
            "group_id": gid,
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

    # Sau khi purge, kiểm định chống rò rỉ tuyệt đối
    if purge_overlapping_groups:
        clean_test_group_set = {e["group_id"] for e in clean_test_entries}
        assert_no_group_leakage(train_group_set, clean_test_group_set, "Temporal Train vs Clean Test")

    all_purged_groups = sorted(
        {e["group_id"] for e in purged_val_entries}.union({e["group_id"] for e in purged_test_entries})
    )

    return {
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
        },
    }
