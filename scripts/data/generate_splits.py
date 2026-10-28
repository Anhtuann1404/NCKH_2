#!/usr/bin/env python3
"""CLI công cụ phân chia tập dữ liệu chống rò rỉ (DATA-03 Splits Generator).

Tự động sinh:
1. groups.json: Ánh xạ sample_id -> group_id (eTLD+1 / UGC tenant / Connected duplicate components).
2. grouped_5fold_splits.json: Phân chia 5-fold CV qua 3 seeds (17, 42, 2026) kèm inner validation.
3. temporal_splits.json: Phân chia mốc thời gian 60/20/20 không chia ngày và loại trừ trùng nhóm sớm.
4. manifest.json: Khóa mã băm liên kết đầu vào, groups, splits, phiên bản PSL và quy tắc.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from typing import Any, Dict, List, Optional, Set
import uuid

# Đảm bảo mã hóa UTF-8 an toàn trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Thêm src vào PYTHONPATH nếu chạy trực tiếp
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from phishing.data.exclusion import ExclusionRegistry
from phishing.data.grouping import (
    GROUP_RULES_VERSION,
    PSL_SNAPSHOT_SHA256,
    PSL_VERSION,
    TLDEXTRACT_VERSION,
    extract_group_id,
)
from phishing.data.splits import (
    DEFAULT_SEEDS,
    assert_no_group_leakage,
    assert_strict_temporal_order,
    generate_grouped_kfold,
    generate_temporal_split,
)


def load_records(input_path: Path) -> List[Dict[str, Any]]:
    """Nạp danh sách bản ghi từ tệp JSON hoặc JSONL."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    suffix = input_path.suffix.lower()
    records: List[Dict[str, Any]] = []

    if suffix == ".jsonl":
        with open(input_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    records.append(json.loads(line_str))
                except json.JSONDecodeError as err:
                    raise ValueError(f"Invalid JSON at line {line_no} in {input_path}: {err}") from err
    elif suffix == ".json":
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict) and "samples" in data and isinstance(data["samples"], list):
                records = data["samples"]
            else:
                raise ValueError("JSON input must be a list of records or contain a 'samples' list.")
    else:
        raise ValueError(f"Unsupported input file format: {suffix}. Supported: .json, .jsonl")

    return records


def calculate_sha256(file_path: Path) -> str:
    """Tính mã băm SHA-256 chuẩn hóa cho tệp."""
    with open(file_path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest()


def calculate_code_hashes() -> Dict[str, str]:
    """Tính mã băm chi tiết cho từng file mã nguồn ảnh hưởng trực tiếp đến kết quả splits."""
    code_files = [
        SRC_DIR / "phishing" / "data" / "splits.py",
        SRC_DIR / "phishing" / "data" / "grouping.py",
        SRC_DIR / "phishing" / "data" / "date_parser.py",
        REPO_ROOT / "scripts" / "data" / "generate_splits.py",
    ]
    hashes: Dict[str, str] = {}
    for py_file in code_files:
        if py_file.exists():
            with open(py_file, "rb") as f:
                hashes[py_file.name] = hashlib.sha256(f.read()).hexdigest()
    return hashes


def calculate_composite_code_sha256(code_hashes: Dict[str, str]) -> str:
    """Tính mã băm tổng hợp của toàn bộ mã nguồn ảnh hưởng."""
    hasher = hashlib.sha256()
    for fname in sorted(code_hashes.keys()):
        hasher.update(code_hashes[fname].encode("utf-8"))
    return hasher.hexdigest()


def detect_real_data_record(record: Dict[str, Any], id_field: str = "sample_id") -> Optional[str]:
    """Kiểm tra một bản ghi có mang dấu vết/metadata nguồn dữ liệu thật hay không.

    Duyệt toàn bộ metadata nguồn gồm sample_id, source_id, locator, source_revision,
    dataset, định danh shard parquet.
    Trả về lý do phát hiện (chuỗi) nếu có dấu vết dữ liệu thật, hoặc None nếu là dữ liệu mô phỏng.
    """
    sid = str(record.get(id_field, "")).strip()

    # 1. Kiểm tra tiền tố và mẫu ID nguồn dữ liệu thật
    if sid.startswith(("PP-", "PV-", "SMP-", "RSV-", "train-", "test-", "val-")):
        return f"sample_id '{sid}' mang tiền tố dữ liệu thật (PP-/PV-/SMP-/RSV-/train-/test-/val-)"
    if re.match(r"^(PP|PV|SMP|RSV|PHISH|BENIGN)[-_]", sid, re.IGNORECASE):
        return f"sample_id '{sid}' khớp định dạng mẫu dữ liệu thật"

    # 2. Kiểm tra source_id
    src = str(record.get("source_id", "")).strip().lower()
    if src in {"phreshphish", "phishvn"} or "phreshphish" in src or "phishvn" in src:
        return f"source_id '{src}' chỉ định nguồn dữ liệu nghiên cứu thật"

    # 3. Kiểm tra locator
    loc = record.get("locator")
    if isinstance(loc, dict):
        loc_src = str(loc.get("source_id", "")).strip().lower()
        if loc_src in {"phreshphish", "phishvn"} or "phreshphish" in loc_src or "phishvn" in loc_src:
            return f"locator.source_id '{loc_src}' chỉ định nguồn dữ liệu thật"
        for k, v in loc.items():
            v_str = str(v).lower()
            if any(term in v_str for term in ["shard", "parquet", "train-00", "train-055", "row_offset"]):
                return f"locator.{k}='{v}' chứa định danh shard/offset parquet thực tế"
    elif isinstance(loc, str) and loc.strip():
        loc_lower = loc.lower()
        if any(term in loc_lower for term in ["phreshphish", "phishvn", ".parquet", "train-00", "train-055", "shard", "row_offset"]):
            return f"locator chuỗi '{loc}' chứa định danh shard/offset parquet thực tế"

    # 4. Kiểm tra source_revision
    src_rev = record.get("source_revision")
    if src_rev and str(src_rev).strip():
        return f"source_revision '{src_rev}' chỉ định nguồn dữ liệu thật"

    # 5. Kiểm tra trường dataset
    dataset = str(record.get("dataset", "")).strip().lower()
    if dataset in {"phreshphish", "phishvn"} or "phreshphish" in dataset or "phishvn" in dataset:
        return f"dataset '{dataset}' chỉ định nguồn dữ liệu thật"

    return None


def validate_fixture_provenance(record: Dict[str, Any], id_field: str = "sample_id") -> Optional[str]:
    """Kiểm tra một bản ghi có bằng chứng fixture/synthetic tường minh và hợp lệ hay không.

    HỢP ĐỒNG FIXTURE BẮT BUỘC (Strict Provenance Contract):
    1. Tuyệt đối không mang bất kỳ dấu vết dữ liệu thật nào (detect_real_data_record trả về None).
    2. Bắt buộc phải có bằng chứng mô phỏng tường minh:
       'is_synthetic' is True HOẶC 'is_fixture' is True HOẶC 'provenance' in {"synthetic", "fixture"}.

    Trả về None nếu hợp lệ, hoặc chuỗi mô tả lý do từ chối.
    """
    # 1. Kiểm tra dấu vết dữ liệu thật trước tiên
    real_reason = detect_real_data_record(record, id_field=id_field)
    if real_reason is not None:
        return f"phát hiện dấu vết dữ liệu thật ({real_reason})"

    # 2. Kiểm tra bằng chứng fixture tường minh
    is_synth = record.get("is_synthetic")
    is_fix = record.get("is_fixture")
    prov = str(record.get("provenance", "")).strip().lower()

    if is_synth is True or is_fix is True or prov in {"synthetic", "fixture"}:
        return None

    return (
        "thiếu bằng chứng mô phỏng tường minh "
        "(yêu cầu metadata 'is_synthetic': true, 'is_fixture': true hoặc 'provenance': 'synthetic')"
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="NCKH_2 Anti-Leakage Data Splitting Tool (Grouped 5-Fold & Temporal 60/20/20)."
    )
    parser.add_argument("--input", "-i", type=str, required=True, help="Path to input JSON or JSONL file.")
    parser.add_argument("--output-dir", "-o", type=str, default="data/splits", help="Directory to save split manifests.")
    parser.add_argument("--n-splits", "-k", type=int, default=5, help="Number of folds (default: 5, minimum: 3).")
    parser.add_argument("--seeds", type=str, default="17,42,2026", help="Comma-separated random seeds (default: 17,42,2026).")
    parser.add_argument("--id-field", type=str, default="sample_id", help="Field name for unique ID.")
    parser.add_argument("--url-field", type=str, default="url", help="Field name for URL.")
    parser.add_argument("--group-field", type=str, default="group_id", help="Field name for pre-identified group/component.")
    parser.add_argument("--date-field", type=str, default="collected_at", help="Field name for collection date.")
    parser.add_argument("--label-field", type=str, default="class_label", help="Field name for label.")
    parser.add_argument("--skip-temporal", action="store_true", help="Deliberately skip temporal split if dates not available.")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting existing artifacts in output-dir.")
    parser.add_argument(
        "--exclusion-registry",
        type=str,
        default=None,
        help="Đường dẫn exclusion_registry.json để kiểm tra chốt chặn cam kết hạn chế và rò rỉ dữ liệu.",
    )
    parser.add_argument(
        "--fixture-mode",
        action="store_true",
        help=(
            "Khai báo tường minh chế độ dữ liệu mô phỏng (fixture/synthetic). "
            "HỢP ĐỒNG FIXTURE BẮT BUỘC: 100% bản ghi phải có bằng chứng mô phỏng tường minh "
            "(metadata 'is_synthetic': true, 'is_fixture': true hoặc 'provenance': 'synthetic') "
            "và tuyệt đối không chứa bất kỳ dấu vết dữ liệu thật nào. "
            "Mặc định khi không có cờ này, mọi đầu vào đều được coi là dữ liệu thật và bắt buộc phải có "
            "ExclusionRegistry cùng cam kết hạn chế hợp lệ."
        ),
    )
    parser.add_argument(
        "--synthetic-fixture",
        action="store_true",
        dest="fixture_mode",
        help="Bí danh tương đương với --fixture-mode.",
    )
    parser.add_argument(
        "--is-real-data",
        action="store_true",
        help="Chỉ định rõ chế độ dữ liệu thật: bắt buộc phải có ExclusionRegistry và toàn bộ cam kết hạn chế phải được xác minh.",
    )
    parser.add_argument(
        "--allow-unverified-commitments",
        action="store_true",
        help="Chỉ dùng cho testing/audit: cho phép chạy khi chưa xác minh cam kết hạn chế nhưng KHÔNG xuất verified_robust.",
    )

    args = parser.parse_args(argv)

    # 1. Kiểm tra cấu hình và tham số dòng lệnh trước tiên
    if args.n_splits < 3:
        print(f"[!] Error: --n-splits must be at least 3, got {args.n_splits}.", file=sys.stderr)
        return 1

    raw_seeds = (args.seeds or "").strip()
    if not raw_seeds:
        print("[!] Error: --seeds cannot be empty. Specify e.g. --seeds 17,42,2026.", file=sys.stderr)
        return 1

    seed_list: List[int] = []
    for s in raw_seeds.split(","):
        s_clean = s.strip()
        if not s_clean:
            continue
        try:
            seed_list.append(int(s_clean))
        except ValueError:
            print(f"[!] Error: Invalid seed value '{s_clean}'. Seeds must be integers.", file=sys.stderr)
            return 1

    if not seed_list:
        print("[!] Error: --seeds list is empty.", file=sys.stderr)
        return 1

    if len(seed_list) != len(set(seed_list)):
        print(f"[!] Error: Duplicate seeds detected: {seed_list}. Seeds must be unique.", file=sys.stderr)
        return 1

    seeds = tuple(seed_list)

    # 2. Kiểm tra input tệp nguồn trước khi làm bất kỳ thao tác nào
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[!] Error: Input file does not exist: {input_path}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir)

    # 3. Kiểm tra bảo toàn bằng chứng: Không tự ý xóa hoặc ghi đè thư mục run cũ nếu chưa có --overwrite
    target_artifacts = ["groups.json", "grouped_5fold_splits.json", "manifest.json"]
    if not args.skip_temporal:
        target_artifacts.append("temporal_splits.json")

    existing_artifacts = [name for name in target_artifacts if (output_dir / name).exists()]
    if existing_artifacts and not args.overwrite:
        print(
            f"[!] Error: Output directory '{output_dir}' already contains previous run artifacts: {existing_artifacts}.\n"
            f"    To preserve provenance and audit trail, please specify a new run directory (e.g. -o data/splits/run_02)\n"
            f"    or use --overwrite to explicitly replace existing artifacts.",
            file=sys.stderr,
        )
        return 1

    # 4. Nạp dữ liệu vào bộ nhớ
    print(f"[*] Loading records from: {input_path}")
    try:
        records = load_records(input_path)
    except Exception as err:
        print(f"[!] Error loading input records: {err}", file=sys.stderr)
        return 1

    print(f"[*] Successfully loaded {len(records)} records.")
    input_sha256 = calculate_sha256(input_path)

    # 4b. Kiểm tra chốt chặn cam kết hạn chế và phòng chống rò rỉ dữ liệu (Anti-Leakage Protocol)
    # NGUYÊN TẮC BẢO VỆ DỮ LIỆU: MẶC ĐỊNH MỌI ĐẦU VÀO ĐỀU LÀ DỮ LIỆU THẬT.
    # Chỉ được phép kích hoạt nhánh fixture khi hội tụ đủ 2 điều kiện:
    # 1. Có cờ tường minh --fixture-mode (hoặc --synthetic-fixture).
    # 2. 100% bản ghi có bằng chứng mô phỏng tường minh ('is_synthetic': true, 'is_fixture': true hoặc 'provenance': 'synthetic')
    #    và tuyệt đối không mang bất kỳ dấu vết dữ liệu thật nào.
    if args.fixture_mode:
        for idx, r in enumerate(records):
            violation = validate_fixture_provenance(r, id_field=args.id_field)
            if violation is not None:
                sid = r.get(args.id_field, f"row_{idx}")
                print(
                    f"[!] LỖI HỢP ĐỒNG FIXTURE (Anti-Leakage Protocol):\n"
                    f"    Bản ghi tại dòng {idx + 1} (ID: '{sid}') không đáp ứng quy chuẩn fixture: {violation}.\n"
                    f"    Quy tắc: Cờ --fixture-mode yêu cầu 100% bản ghi phải có bằng chứng synthetic tường minh ('is_synthetic': true) "
                    f"    và tuyệt đối cấm tệp trộn thật-fixture hoặc dữ liệu thật. Từ chối fail-closed.",
                    file=sys.stderr,
                )
                return 1
        is_real_data = False
        is_fixture_mode = True
    else:
        # MẶC ĐỊNH XỬ LÝ LÀ DỮ LIỆU THẬT (kể cả ID trung tính, không có metadata nguồn)
        # Bắt buộc phải có ExclusionRegistry và hồ sơ cam kết hạn chế ngoài Git hợp lệ
        is_real_data = True
        is_fixture_mode = False

    reg_path = args.exclusion_registry
    if reg_path is None and is_real_data:
        default_reg = REPO_ROOT / "data" / "exclusion_registry.json"
        if default_reg.exists():
            reg_path = str(default_reg)

    commitments_verified = False
    if is_real_data:
        if reg_path is None or not Path(reg_path).exists():
            print(
                "[!] LỆNH CHẶN FAIL-CLOSED: Chế độ dữ liệu thật bắt buộc phải có exclusion registry hợp lệ!",
                file=sys.stderr,
            )
            return 1

        try:
            registry = ExclusionRegistry(reg_path)
        except Exception as reg_err:
            print(f"[!] LỖI TOÀN VẸN HỒ SƠ HẠN CHẾ: {reg_err}", file=sys.stderr)
            return 1

        try:
            registry.assert_restricted_commitments_verified()
            commitments_verified = True
        except RuntimeError as err:
            commitments_verified = False
            if not args.allow_unverified_commitments:
                print(
                    f"[!] LỆNH CHẶN FAIL-CLOSED: Không thể phân chia tập dữ liệu thật khi hồ sơ cam kết hạn chế ngoài Git chưa được xác minh toàn vẹn!\n"
                    f"    Chi tiết: {err}",
                    file=sys.stderr,
                )
                return 1

        # Kiểm tra rò rỉ mẫu loại trừ trong tập dữ liệu đầu vào của splits
        try:
            registry.assert_no_leakage(
                "splits_input",
                records,
                allow_unverified_commitments=args.allow_unverified_commitments,
            )
        except ValueError as leak_err:
            print(f"[!] LỖI RÒ RỈ DỮ LIỆU ĐẦU VÀO SPLITS: {leak_err}", file=sys.stderr)
            return 1
        except RuntimeError as fail_closed_err:
            if not args.allow_unverified_commitments:
                print(f"[!] LỆNH CHẶN FAIL-CLOSED: {fail_closed_err}", file=sys.stderr)
                return 1
    elif args.exclusion_registry is not None:
        try:
            registry = ExclusionRegistry(args.exclusion_registry)
            try:
                registry.assert_restricted_commitments_verified()
                commitments_verified = True
            except RuntimeError:
                commitments_verified = False
            registry.assert_no_leakage(
                "splits_input",
                records,
                allow_unverified_commitments=args.allow_unverified_commitments,
            )
        except ValueError as leak_err:
            print(f"[!] LỖI RÒ RỈ DỮ LIỆU ĐẦU VÀO SPLITS: {leak_err}", file=sys.stderr)
            return 1
        except Exception as err:
            print(f"[!] LỖI EXCLUSION REGISTRY: {err}", file=sys.stderr)
            return 1
    else:
        # Chế độ fixture/synthetic: không yêu cầu cam kết hạn chế thực tế
        commitments_verified = False

    # 5. Trích xuất groups có bảo toàn component trùng nội dung và kiểm tra tính hợp lệ
    print("[*] Extracting group_id (eTLD+1, UGC tenant & pre-identified components)...")
    groups_manifest: Dict[str, Any] = {
        "metadata": {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_file": str(input_path),
            "input_sha256": input_sha256,
            "total_records": len(records),
            "group_rules_version": GROUP_RULES_VERSION,
            "tldextract_version": TLDEXTRACT_VERSION,
            "psl_snapshot_sha256": PSL_SNAPSHOT_SHA256,
        },
        "sample_groups": {},
        "group_summary": {},
    }

    seen_ids: Set[str] = set()
    group_counts: Dict[str, int] = {}

    for idx, rec in enumerate(records):
        raw_sid = rec.get(args.id_field)
        if raw_sid is None or not isinstance(raw_sid, str) or not raw_sid.strip():
            print(f"[!] Error: Record #{idx} has missing/invalid ID field '{args.id_field}'.", file=sys.stderr)
            return 1
        sid = raw_sid.strip()
        if sid in seen_ids:
            print(f"[!] Error: Duplicate sample_id detected: '{sid}'. All IDs must be globally unique.", file=sys.stderr)
            return 1
        seen_ids.add(sid)

        # Ưu tiên nhận group_id hoặc component index đã kiểm chứng từ đầu vào
        gid = ""
        if args.group_field and args.group_field in rec and rec[args.group_field] is not None:
            raw_gid = rec[args.group_field]
            if isinstance(raw_gid, str):
                cand_gid = raw_gid.strip()
                if cand_gid and cand_gid != "unknown" and not any(c.isspace() for c in cand_gid):
                    gid = cand_gid

        if not gid:
            raw_url = rec.get(args.url_field)
            if raw_url is None or not isinstance(raw_url, str) or not raw_url.strip():
                print(
                    f"[!] Error: Record '{sid}' has neither valid '{args.group_field}' nor '{args.url_field}'. "
                    f"Silent fallback to 'row:<idx>' is strictly forbidden.",
                    file=sys.stderr,
                )
                return 1
            cand_url = raw_url.strip()
            gid = extract_group_id(cand_url)
            if gid == "unknown" or any(c.isspace() for c in gid):
                print(
                    f"[!] Error: Record '{sid}' has invalid URL '{cand_url}' that cannot be mapped to a valid group.",
                    file=sys.stderr,
                )
                return 1

        groups_manifest["sample_groups"][sid] = gid
        group_counts[gid] = group_counts.get(gid, 0) + 1

    groups_manifest["group_summary"] = {
        "distinct_groups_count": len(group_counts),
        "largest_group": max(group_counts.items(), key=lambda x: x[1]) if group_counts else None,
        "smallest_group": min(group_counts.items(), key=lambda x: x[1]) if group_counts else None,
    }

    # 6. Tính toán Grouped K-Fold hoàn chỉnh trong bộ nhớ
    print(f"[*] Generating Grouped {args.n_splits}-Fold splits for seeds: {seeds}...")
    try:
        grouped_splits = generate_grouped_kfold(
            records=records,
            n_splits=args.n_splits,
            seeds=seeds,
            id_field=args.id_field,
            url_field=args.url_field,
            group_field=args.group_field,
            label_field=args.label_field,
        )
    except Exception as err:
        print(f"[!] Error: Grouped K-Fold generation failed: {err}", file=sys.stderr)
        return 1

    grouped_manifest: Dict[str, Any] = {
        "metadata": {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "n_splits": args.n_splits,
            "seeds": list(seeds),
            "input_sha256": input_sha256,
            "group_rules_version": GROUP_RULES_VERSION,
            "tldextract_version": TLDEXTRACT_VERSION,
            "psl_snapshot_sha256": PSL_SNAPSHOT_SHA256,
            "anti_leakage_verified": True,
        },
        "splits_by_seed": grouped_splits,
    }

    # 7. Tính toán Temporal Split hoàn chỉnh trong bộ nhớ
    temporal_result = None
    temporal_manifest = None
    if args.skip_temporal:
        print("[*] Deliberately skipping Temporal split (--skip-temporal flag passed).")
    else:
        print("[*] Generating Temporal 60/20/20 split with past group purging...")
        try:
            temporal_result = generate_temporal_split(
                records=records,
                train_ratio=0.6,
                val_ratio=0.2,
                test_ratio=0.2,
                id_field=args.id_field,
                date_field=args.date_field,
                url_field=args.url_field,
                group_field=args.group_field,
                label_field=args.label_field,
                purge_overlapping_groups=True,
            )
        except Exception as err:
            print(f"[!] Error: Temporal split failed: {err}", file=sys.stderr)
            return 1

        temporal_manifest = {
            "metadata": {
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "train_ratio": 0.6,
                "val_ratio": 0.2,
                "test_ratio": 0.2,
                "purge_overlapping_groups": True,
                "input_sha256": input_sha256,
                "group_rules_version": GROUP_RULES_VERSION,
                "tldextract_version": TLDEXTRACT_VERSION,
                "psl_snapshot_sha256": PSL_SNAPSHOT_SHA256,
                "verification_checks_passed": temporal_result.get("verification_checks_passed", []),
                "anti_leakage_verified": temporal_result.get("status") == "evaluable",
            },
            "split": temporal_result,
        }

    # 8. Đánh giá tính vững chắc tổng thể (verified_robust) và điều kiện sử dụng để huấn luyện
    all_folds_sufficient = all(
        f["class_sufficiency"]["status"] == "sufficient"
        for fold_list in grouped_splits.values()
        for f in fold_list
    )
    all_folds_usable = all(
        f.get("is_usable", True)
        for fold_list in grouped_splits.values()
        for f in fold_list
    )
    temporal_evaluable = (temporal_result.get("status") == "evaluable") if temporal_result is not None else True

    # TIÊU CHÍ VERIFIED_ROBUST: Bắt buộc là dữ liệu thật ĐÃ ĐƯỢC XÁC MINH TOÀN VẸN cam kết hạn chế
    if is_fixture_mode:
        verified_robust = False
        anti_leakage_status = "synthetic_fixture_test_mode"
        usable_for_training = False
    elif not commitments_verified:
        verified_robust = False
        anti_leakage_status = "audit_only_unverified_commitments"
        usable_for_training = False
    elif all_folds_sufficient and all_folds_usable and temporal_evaluable:
        verified_robust = True
        anti_leakage_status = "verified_robust"
        usable_for_training = True
    else:
        verified_robust = False
        anti_leakage_status = "provisional_insufficient_classes"
        usable_for_training = False

    # Nếu không đủ điều kiện huấn luyện (audit-only hoặc fixture), khóa is_usable trên mọi fold
    if not usable_for_training:
        for seed_val, fold_list in grouped_splits.items():
            for fold in fold_list:
                fold["is_usable"] = False
                fold["unusable_reason"] = (
                    "Chế độ dữ liệu mô phỏng (fixture): không được phép dùng để huấn luyện mô hình thực tế."
                    if is_fixture_mode
                    else "Hồ sơ cam kết hạn chế chưa được xác minh toàn vẹn: chỉ dùng cho kiểm toán (audit-only), không được phép dùng để huấn luyện."
                )

    grouped_manifest["metadata"]["usable_for_training"] = usable_for_training
    grouped_manifest["metadata"]["verified_robust"] = verified_robust
    grouped_manifest["metadata"]["anti_leakage_status"] = anti_leakage_status

    if temporal_manifest is not None:
        temporal_manifest["metadata"]["usable_for_training"] = usable_for_training
        temporal_manifest["metadata"]["verified_robust"] = verified_robust
        temporal_manifest["metadata"]["anti_leakage_status"] = anti_leakage_status

    # 9. MỌI TÍNH TOÁN ĐÃ HOÀN TẤT VÀ XÁC THỰC THÀNH CÔNG -> Ghi vào STAGING DIR trước khi công bố
    staging_dir = output_dir.parent / f".staging_{output_dir.name}_{uuid.uuid4().hex[:8]}"
    staging_dir.mkdir(parents=True, exist_ok=True)

    try:
        stg_groups_file = staging_dir / "groups.json"
        with open(stg_groups_file, "w", encoding="utf-8") as f:
            json.dump(groups_manifest, f, indent=2, ensure_ascii=False)
        groups_sha256 = calculate_sha256(stg_groups_file)

        grouped_manifest["metadata"]["groups_sha256"] = groups_sha256
        stg_grouped_file = staging_dir / "grouped_5fold_splits.json"
        with open(stg_grouped_file, "w", encoding="utf-8") as f:
            json.dump(grouped_manifest, f, indent=2, ensure_ascii=False)
        grouped_sha256 = calculate_sha256(stg_grouped_file)

        temporal_sha256 = None
        if temporal_manifest is not None and temporal_result is not None:
            temporal_manifest["metadata"]["groups_sha256"] = groups_sha256
            stg_temporal_file = staging_dir / "temporal_splits.json"
            with open(stg_temporal_file, "w", encoding="utf-8") as f:
                json.dump(temporal_manifest, f, indent=2, ensure_ascii=False)
            temporal_sha256 = calculate_sha256(stg_temporal_file)

        code_hashes = calculate_code_hashes()
        composite_code_sha256 = calculate_composite_code_sha256(code_hashes)

        # 10. Ghi Manifest liên kết đầy đủ mã băm xuất xứ (Provenance Manifest)
        manifest: Dict[str, Any] = {
            "manifest_type": "DATA-03_SPLIT_MANIFEST",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "input_file": str(input_path),
            "input_sha256": input_sha256,
            "code_sha256": composite_code_sha256,
            "code_hashes": code_hashes,
            "run_parameters": {
                "n_splits": args.n_splits,
                "seeds": list(seeds),
                "id_field": args.id_field,
                "url_field": args.url_field,
                "group_field": args.group_field,
                "date_field": args.date_field,
                "label_field": args.label_field,
                "skip_temporal": args.skip_temporal,
                "is_real_data": is_real_data,
                "fixture_mode": is_fixture_mode,
                "commitments_verified": commitments_verified,
            },
            "grouping_metadata": {
                "group_rules_version": GROUP_RULES_VERSION,
                "tldextract_version": TLDEXTRACT_VERSION,
                "psl_snapshot_sha256": PSL_SNAPSHOT_SHA256,
                "psl_source": "tldextract bundled snapshot",
            },
            "artifacts": {
                "groups_json": {"path": "groups.json", "sha256": groups_sha256},
                "grouped_5fold_splits_json": {"path": "grouped_5fold_splits.json", "sha256": grouped_sha256},
                "temporal_splits_json": (
                    {"path": "temporal_splits.json", "sha256": temporal_sha256} if temporal_sha256 else None
                ),
            },
            "anti_leakage_status": anti_leakage_status,
            "verified_robust": verified_robust,
            "usable_for_training": usable_for_training,
            "verification_summary": {
                "all_folds_sufficient": all_folds_sufficient,
                "all_folds_usable": all_folds_usable,
                "temporal_evaluable": temporal_evaluable,
                "commitments_verified": commitments_verified,
                "usable_for_training": usable_for_training,
            },
        }

        stg_manifest_file = staging_dir / "manifest.json"
        with open(stg_manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        # 11. CÔNG BỐ ATOMIC CÓ BACKUP & ROLLBACK (Khắc phục Điểm 1 của Lead D):
        # Nếu output_dir đã có tệp từ run trước, sao lưu toàn bộ vào backup_dir trước khi xuất bản.
        # Nếu xảy ra bất kỳ lỗi nào trong quá trình xóa/chuyển tệp, khôi phục nguyên vẹn 100% run cũ.
        output_dir.mkdir(parents=True, exist_ok=True)
        backup_dir = None
        existing_items = list(output_dir.iterdir())
        if existing_items:
            backup_dir = output_dir.parent / f".backup_{output_dir.name}_{uuid.uuid4().hex[:8]}"
            shutil.copytree(output_dir, backup_dir)

        publish_success = False
        rollback_completed = False
        try:
            # Xử lý rõ ràng artifact temporal của run trước khi overwrite hoặc skip (Khắc phục Probe 3)
            old_temporal = output_dir / "temporal_splits.json"
            if (args.skip_temporal or temporal_sha256 is None) and old_temporal.exists():
                old_temporal.unlink()

            # Sao chép/di chuyển từng tệp từ staging sang output_dir
            for stg_item in list(staging_dir.iterdir()):
                target_item = output_dir / stg_item.name
                if target_item.exists():
                    target_item.unlink()
                shutil.move(str(stg_item), str(target_item))
            publish_success = True
        except Exception as exc:
            print(f"[!] Lỗi khi công bố artifacts sang {output_dir}: {exc}. Đang tiến hành rollback...", file=sys.stderr)
            # Xóa các tệp dở dang trong output_dir
            for item in list(output_dir.iterdir()):
                if item.is_file() or item.is_symlink():
                    item.unlink(missing_ok=True)
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)

            if backup_dir and backup_dir.exists():
                try:
                    for bkp_item in backup_dir.iterdir():
                        if bkp_item.is_file():
                            shutil.copy2(bkp_item, output_dir / bkp_item.name)
                        elif bkp_item.is_dir():
                            shutil.copytree(bkp_item, output_dir / bkp_item.name)
                    rollback_completed = True
                    print(f"[!] Đã khôi phục hoàn toàn trạng thái artifacts trước đó từ backup.", file=sys.stderr)
                except Exception as rb_exc:
                    rollback_completed = False
                    print(
                        f"[CRITICAL] Khôi phục từ backup thất bại: {rb_exc}. "
                        f"BẢO LƯU THƯ MỤC BACKUP ĐẦY ĐỦ TẠI: {backup_dir} ĐỂ PHỤC HỒI THỦ CÔNG.",
                        file=sys.stderr,
                    )
                    raise RuntimeError(
                        f"Công bố artifacts thất bại ({exc}) và quá trình rollback cũng gặp lỗi ({rb_exc}). "
                        f"Thư mục backup nguyên vẹn được bảo lưu tại: {backup_dir}"
                    ) from exc
            else:
                rollback_completed = True
            raise
        finally:
            if backup_dir and backup_dir.exists():
                if publish_success or rollback_completed:
                    shutil.rmtree(backup_dir, ignore_errors=True)
                else:
                    print(
                        f"[!] BẢO LƯU BACKUP AN TOÀN: Không xóa thư mục sao lưu tại {backup_dir} "
                        f"để phục hồi thủ công do rollback không hoàn tất.",
                        file=sys.stderr,
                    )

        print(f"[+] Saved Group index: {output_dir / 'groups.json'} ({len(group_counts)} groups)")
        print(f"[+] Saved Grouped {args.n_splits}-Fold splits: {output_dir / 'grouped_5fold_splits.json'}")
        if temporal_sha256 is not None:
            print(f"[+] Saved Temporal splits: {output_dir / 'temporal_splits.json'} (Status: {temporal_result.get('status')})")
        print(f"[+] Saved Run Manifest: {output_dir / 'manifest.json'} (Status: {manifest['anti_leakage_status']})")

    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)

    print("\n[V] DATA-03 splitting generation completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
