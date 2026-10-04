"""Script Audit riêng cột date trên toàn bộ tập train PhreshPhish (Task DATA-01).

Nguyên tắc nghiên cứu học thuật (Academic Research Skills - ARS):
1. Chỉ đọc cột 'date' (hoặc metadata tương đương), TUYỆT ĐỐI KHÔNG đọc URL, HTML hay label.
2. Pinned git revision cụ thể để đảm bảo tính tái lập (reproducibility).
3. Thống kê phân bố theo tháng, ngày min, ngày max, số lượng bản ghi bị thiếu/sai định dạng.
4. Đánh giá độ phủ đối với cửa sổ dự kiến (01/10/2024 - 31/12/2025).
"""

import sys
import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("DateAudit")

PINNED_REPO = "phreshphish/phreshphish"
PINNED_REVISION = "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "source_audit" / "phreshphish"
OUTPUT_FILE = OUTPUT_DIR / "date_audit_report.json"

PROPOSED_WINDOW_START = "2024-10-01"
PROPOSED_WINDOW_END = "2025-12-31"


def audit_dates():
    try:
        from huggingface_hub import HfFileSystem
        import pyarrow.parquet as pq
    except ImportError as e:
        logger.error(
            f"Thiếu thư viện: {e}. Vui lòng cài đặt pyarrow và huggingface_hub."
        )
        sys.exit(1)

    logger.info(f"Khởi tạo kết nối HfFileSystem tới repo {PINNED_REPO} (rev: {PINNED_REVISION})...")
    fs = HfFileSystem()

    # Tìm các file train parquet
    pattern = f"datasets/{PINNED_REPO}@{PINNED_REVISION}/data/train-*.parquet"
    train_files = sorted(fs.glob(pattern))

    if not train_files:
        # Fallback thử không có prefix datasets/
        pattern_fallback = f"{PINNED_REPO}@{PINNED_REVISION}/data/train-*.parquet"
        train_files = sorted(fs.glob(pattern_fallback))

    logger.info(f"Tìm thấy {len(train_files)} tệp train parquet cần kiểm kê.")
    if not train_files:
        logger.error(f"Không tìm thấy file parquet nào khớp với pattern: {pattern}")
        sys.exit(1)

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

    logger.info("Bắt đầu quét cột 'date' bằng kỹ thuật Column Projection (chỉ tải byte của cột date)...")

    for idx, fpath in enumerate(train_files, 1):
        try:
            # Chỉ đọc DUY NHẤT cột 'date'
            table = pq.read_table(fpath, columns=["date"], filesystem=fs)
            date_col = table["date"].to_pylist()
            n_file_rows = len(date_col)
            total_rows += n_file_rows

            for d_val in date_col:
                if d_val is None or str(d_val).strip() == "" or str(d_val).lower() == "none":
                    missing_date_count += 1
                    continue

                d_str = str(d_val).strip()
                # Parse date string
                parsed_dt = None
                for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d", "%d-%m-%Y"):
                    try:
                        parsed_dt = datetime.strptime(d_str[:10], fmt).date()
                        break
                    except ValueError:
                        continue

                if not parsed_dt:
                    invalid_date_count += 1
                    continue

                d_iso = parsed_dt.isoformat()
                month_key = d_iso[:7]  # YYYY-MM
                month_counts[month_key] += 1

                if min_date is None or parsed_dt < min_date:
                    min_date = parsed_dt
                if max_date is None or parsed_dt > max_date:
                    max_date = parsed_dt

                # Kiểm tra thuộc cửa sổ dự kiến
                if parsed_dt < win_start_dt:
                    dates_before_window += 1
                elif parsed_dt > win_end_dt:
                    dates_after_window += 1
                else:
                    dates_in_window += 1

            if idx % 5 == 0 or idx == len(train_files):
                logger.info(
                    f"Tiến độ: {idx}/{len(train_files)} files | Đã quét: {total_rows:,} mẫu | "
                    f"Min: {min_date} | Max: {max_date}"
                )

        except Exception as e:
            logger.error(f"Lỗi khi đọc file {fpath}: {e}")
            raise e

    valid_dates_count = total_rows - missing_date_count - invalid_date_count
    coverage_ratio = (dates_in_window / valid_dates_count) if valid_dates_count > 0 else 0.0

    report = {
        "dataset_id": PINNED_REPO,
        "pinned_revision": PINNED_REVISION,
        "split": "train",
        "audited_at_utc": datetime.utcnow().isoformat() + "Z",
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
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info("=" * 60)
    logger.info(f"AUDIT HOÀN TẤT VÀ ĐÃ GHI BÁO CÁO: {OUTPUT_FILE}")
    logger.info(f"Tổng mẫu: {total_rows:,} | Hợp lệ: {valid_dates_count:,} | Thiếu: {missing_date_count}")
    logger.info(f"Dải ngày thực tế: {min_date} --> {max_date}")
    logger.info(f"Số mẫu trong cửa sổ đề xuất ({PROPOSED_WINDOW_START} đến {PROPOSED_WINDOW_END}): {dates_in_window:,} ({coverage_ratio:.2%})")
    logger.info("=" * 60)


if __name__ == "__main__":
    audit_dates()
