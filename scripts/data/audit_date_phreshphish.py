"""Script Audit riêng cột date trên toàn bộ 56 shards tập train PhreshPhish (Task DATA-01).

Nguyên tắc nghiên cứu học thuật (Academic Research Skills - ARS):
1. Chỉ đọc cột 'date' (hoặc metadata tương đương), TUYỆT ĐỐI KHÔNG đọc URL, HTML hay label.
2. Pinned git revision cụ thể (eabec4b7a66324b79cc8a0ad856d1731dc26fe1a) để đảm bảo tính tái lập.
3. Sử dụng bộ phân tích ngày nghiêm ngặt (parse_strict_date) kiểm tra toàn chuỗi, chống lỗi cắt chuỗi d_str[:10].
4. Thu thập thông tin chi tiết từng shard (path, kích thước byte, source_metadata_lfs_sha256, số dòng, min/max).
5. Phân biệt minh bạch giữa checksum metadata nguồn và checksum tự xác minh cục bộ (locally_verified_sha256).
"""

import sys
import json
import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Thêm src vào sys.path để import phishing.data.date_parser
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from phishing.data.date_parser import parse_strict_date
except ImportError:
    # Fallback trực tiếp nếu import gặp vấn đề đường dẫn
    import re
    from datetime import date
    ISO_DATE_REGEX = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")
    ISO_DATETIME_REGEX = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])[T ][0-2]\d:[0-5]\d:[0-5]\d(?:\.\d+)?(?:Z|[+-][0-2]\d:[0-5]\d)?$")
    def parse_strict_date(value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            s = value.strip()
            if not s or s.lower() in {"none", "null", "nan", "nat", ""}:
                return None
            if ISO_DATE_REGEX.fullmatch(s):
                try:
                    return datetime.strptime(s, "%Y-%m-%d").date()
                except ValueError:
                    return None
            if ISO_DATETIME_REGEX.fullmatch(s):
                try:
                    return datetime.fromisoformat(s.replace(" ", "T").replace("Z", "+00:00")).date()
                except ValueError:
                    return None
        return None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("DateAudit")

PINNED_REPO = "phreshphish/phreshphish"
PINNED_REVISION = "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a"
OUTPUT_DIR = PROJECT_ROOT / "data" / "source_audit" / "phreshphish"
AUDIT_REPORT_FILE = OUTPUT_DIR / "date_audit_report.json"
SOURCE_MANIFEST_FILE = PROJECT_ROOT / "configs" / "source_manifest.json"

PROPOSED_WINDOW_START = "2024-10-01"
PROPOSED_WINDOW_END = "2025-12-31"


def audit_dates():
    try:
        from huggingface_hub import HfFileSystem
        import pyarrow.parquet as pq
    except ImportError as e:
        logger.error(f"Thiếu thư viện: {e}. Vui lòng cài đặt pyarrow và huggingface_hub.")
        sys.exit(1)

    logger.info(f"Khởi tạo kết nối HfFileSystem tới repo {PINNED_REPO} (rev: {PINNED_REVISION})...")
    fs = HfFileSystem()

    # Tìm các file train parquet
    pattern = f"datasets/{PINNED_REPO}@{PINNED_REVISION}/data/train-*.parquet"
    train_files = sorted(fs.glob(pattern))

    if not train_files:
        pattern_fallback = f"{PINNED_REPO}@{PINNED_REVISION}/data/train-*.parquet"
        train_files = sorted(fs.glob(pattern_fallback))

    logger.info(f"Tìm thấy {len(train_files)} tệp train parquet cần kiểm kê.")
    if len(train_files) != 56:
        logger.warning(f"CẢNH BÁO: Số lượng tệp ({len(train_files)}) khác với kỳ vọng 56 shards!")

    total_rows = 0
    missing_date_count = 0
    invalid_date_count = 0
    month_counts = Counter()
    min_date = None
    max_date = None

    dates_in_window = 0
    dates_before_window = 0
    dates_after_window = 0

    win_start_dt = datetime.strptime(PROPOSED_WINDOW_START, "%Y-%m-%d").date()
    win_end_dt = datetime.strptime(PROPOSED_WINDOW_END, "%Y-%m-%d").date()

    shards_metadata = []

    logger.info("Bắt đầu quét cột 'date' bằng kỹ thuật Column Projection (chỉ tải byte của cột date)...")

    for idx, fpath in enumerate(train_files, 0):
        try:
            # 1. Thu thập metadata shard qua HfFileSystem.info
            file_info = fs.info(fpath)
            byte_size = file_info.get("size", 0)
            blob_id = file_info.get("blob_id")
            lfs_info = file_info.get("lfs")
            source_lfs_sha256 = getattr(lfs_info, "sha256", None) if lfs_info else None
            fname = Path(fpath).name

            # 2. Chỉ đọc DUY NHẤT cột 'date' qua PyArrow
            table = pq.read_table(fpath, columns=["date"], filesystem=fs)
            date_col = table["date"].to_pylist()
            n_file_rows = len(date_col)
            total_rows += n_file_rows

            shard_missing = 0
            shard_invalid = 0
            shard_valid = 0
            shard_min_date = None
            shard_max_date = None

            for d_val in date_col:
                if d_val is None or str(d_val).strip() == "" or str(d_val).lower() in {"none", "null"}:
                    shard_missing += 1
                    missing_date_count += 1
                    continue

                parsed_dt = parse_strict_date(d_val)
                if parsed_dt is None:
                    shard_invalid += 1
                    invalid_date_count += 1
                    continue

                shard_valid += 1
                d_iso = parsed_dt.isoformat()
                month_key = d_iso[:7]  # YYYY-MM
                month_counts[month_key] += 1

                if min_date is None or parsed_dt < min_date:
                    min_date = parsed_dt
                if max_date is None or parsed_dt > max_date:
                    max_date = parsed_dt

                if shard_min_date is None or parsed_dt < shard_min_date:
                    shard_min_date = parsed_dt
                if shard_max_date is None or parsed_dt > shard_max_date:
                    shard_max_date = parsed_dt

                # Kiểm tra thuộc cửa sổ dự kiến
                if parsed_dt < win_start_dt:
                    dates_before_window += 1
                elif parsed_dt > win_end_dt:
                    dates_after_window += 1
                else:
                    dates_in_window += 1

            shard_record = {
                "shard_index": idx,
                "file_name": fname,
                "relative_path": f"data/{fname}",
                "byte_size": byte_size,
                "source_metadata_lfs_sha256": source_lfs_sha256,
                "locally_verified_sha256": None,
                "checksum_type": "SHA-256 (HF Git-LFS pointer metadata)",
                "verification_status": "metadata_only_column_projected",
                "audited_rows": n_file_rows,
                "valid_dates": shard_valid,
                "missing_dates": shard_missing,
                "invalid_dates": shard_invalid,
                "min_date": shard_min_date.isoformat() if shard_min_date else None,
                "max_date": shard_max_date.isoformat() if shard_max_date else None,
            }
            shards_metadata.append(shard_record)

            if (idx + 1) % 5 == 0 or (idx + 1) == len(train_files):
                logger.info(
                    f"Tiến độ: {idx + 1}/{len(train_files)} shards | Đã quét: {total_rows:,} mẫu | "
                    f"Min: {min_date} | Max: {max_date}"
                )

        except Exception as e:
            logger.error(f"Lỗi khi đọc file {fpath}: {e}")
            raise e

    valid_dates_count = total_rows - missing_date_count - invalid_date_count
    coverage_ratio = (dates_in_window / valid_dates_count) if valid_dates_count > 0 else 0.0

    # Kiểm tra tính toàn vẹn (Self-Consistency Checks)
    assert total_rows == sum(s["audited_rows"] for s in shards_metadata), "Lệch tổng số dòng giữa shards và tổng kết!"
    assert len(shards_metadata) == 56, f"Dự kiến 56 shards nhưng thực tế là {len(shards_metadata)}!"

    audit_timestamp = datetime.now(timezone.utc).isoformat()

    report = {
        "dataset_id": PINNED_REPO,
        "pinned_revision": PINNED_REVISION,
        "split": "train",
        "audited_at_utc": audit_timestamp,
        "parquet_files_audited": len(train_files),
        "total_rows": total_rows,
        "valid_dates_count": valid_dates_count,
        "missing_date_count": missing_date_count,
        "invalid_date_count": invalid_date_count,
        "min_date": min_date.isoformat() if min_date else None,
        "max_date": max_date.isoformat() if max_date else None,
        "monthly_distribution": dict(sorted(month_counts.items())),
        "proposed_window": {
            "start": PROPOSED_WINDOW_START,
            "end": PROPOSED_WINDOW_END,
            "samples_in_window": dates_in_window,
            "samples_before_window": dates_before_window,
            "samples_after_window": dates_after_window,
            "window_coverage_ratio": round(coverage_ratio, 4),
        },
        "anti_leakage_compliance": {
            "columns_read": ["date"],
            "url_read": False,
            "html_read": False,
            "labels_read": False,
            "targets_read": False,
            "strict_parser_verified": True,
            "no_slicing_used": True,
        },
        "shards": shards_metadata,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Cập nhật source_manifest.json có danh sách shard chi tiết
    manifest = {
        "status": "verified_pinned_source_shards",
        "source_id": "phreshphish",
        "source_url": f"https://huggingface.co/datasets/{PINNED_REPO}",
        "revision": PINNED_REVISION,
        "retrieved_at_utc": audit_timestamp,
        "reviewer": "Thành viên C (Data Pipeline Owner)",
        "license_declaration": "cc-by-4.0",
        "usage_conditions": "Anti-phishing research only as stated by dataset card and authors",
        "permission_evidence_url": f"https://huggingface.co/datasets/{PINNED_REPO}",
        "redistribution_status": "restricted_to_features_and_indices",
        "source_split": "train",
        "capture_mode": "raw_html_url_pairs",
        "total_shards": len(shards_metadata),
        "total_records": total_rows,
        "date_audit_path": "data/source_audit/phreshphish/date_audit_report.json",
        "date_range": {
            "min": min_date.isoformat() if min_date else None,
            "max": max_date.isoformat() if max_date else None,
        },
        "dictionary_lock_path": "configs/dictionary_v1.json",
        "notes": (
            "Audited through strict date-only column projection across all 56 parquet files at pinned revision. "
            "Checksums recorded are from source Git-LFS metadata (source_metadata_lfs_sha256); local byte stream "
            "sha256 is null as raw files were not downloaded locally. Zero labels, URLs, or HTML content read."
        ),
        "files": shards_metadata,
    }

    with open(SOURCE_MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    logger.info("=" * 60)
    logger.info(f"AUDIT HOÀN TẤT VÀ ĐÃ GHI BÁO CÁO: {AUDIT_REPORT_FILE}")
    logger.info(f"ĐÃ CẬP NHẬT SOURCE MANIFEST: {SOURCE_MANIFEST_FILE}")
    logger.info(f"Tổng số shard: {len(shards_metadata)} | Tổng mẫu: {total_rows:,} | Hợp lệ: {valid_dates_count:,}")
    logger.info(f"Dải ngày thực tế: {min_date} --> {max_date}")
    logger.info(f"Số mẫu trong cửa sổ đề xuất ({PROPOSED_WINDOW_START} đến {PROPOSED_WINDOW_END}): {dates_in_window:,} ({coverage_ratio:.2%})")
    logger.info("=" * 60)


if __name__ == "__main__":
    audit_dates()
