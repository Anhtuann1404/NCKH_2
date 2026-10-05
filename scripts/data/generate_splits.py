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

    # 8. MỌI TÍNH TOÁN ĐÃ HOÀN TẤT VÀ XÁC THỰC THÀNH CÔNG -> Ghi vào STAGING DIR trước khi công bố
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

        # 9. Đánh giá tính vững chắc tổng thể (verified_robust)
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

        verified_robust = bool(all_folds_sufficient and all_folds_usable and temporal_evaluable)

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
            "anti_leakage_status": "verified_robust" if verified_robust else "provisional_insufficient_classes",
            "verified_robust": verified_robust,
            "verification_summary": {
                "all_folds_sufficient": all_folds_sufficient,
                "all_folds_usable": all_folds_usable,
                "temporal_evaluable": temporal_evaluable,
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
                for bkp_item in backup_dir.iterdir():
                    if bkp_item.is_file():
                        shutil.copy2(bkp_item, output_dir / bkp_item.name)
                    elif bkp_item.is_dir():
                        shutil.copytree(bkp_item, output_dir / bkp_item.name)
                print(f"[!] Đã khôi phục hoàn toàn trạng thái artifacts trước đó từ backup.", file=sys.stderr)
            raise
        finally:
            if backup_dir and backup_dir.exists():
                shutil.rmtree(backup_dir, ignore_errors=True)

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
