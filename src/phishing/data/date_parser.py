"""Module phân tích ngày nghiêm ngặt (Strict Date Parser) cho tập dữ liệu phishing.

Nguyên tắc ARS (Academic Research Skills):
1. Không dùng chuỗi con (slicing) d_str[:10] để tránh chấp nhận các chuỗi có hậu tố rác.
2. Kiểm tra toàn chuỗi (fullmatch) và kiểm tra tính hợp lệ lịch (calendar validity).
3. Hỗ trợ các định dạng ngày/thời gian tiêu chuẩn (ISO 8601, YYYY-MM-DD, timestamp).
4. Từ chối ngày lịch sai (ví dụ: 2024-02-30), hậu tố rác, chuỗi rỗng/null và giá trị bất thường.
"""

from datetime import date, datetime, timezone
import re
from typing import Any

# Regex kiểm tra toàn chuỗi
ISO_DATE_REGEX = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")
ISO_DATETIME_REGEX = re.compile(
    r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])"
    r"[T ]"
    r"[0-2]\d:[0-5]\d:[0-5]\d"
    r"(?:\.\d+)?"
    r"(?:Z|[+-][0-2]\d:[0-5]\d)?$"
)

# Giới hạn timestamp hợp lý (từ 1970-01-01 đến 2100-01-01 UTC)
MIN_TIMESTAMP_SEC = 0.0
MAX_TIMESTAMP_SEC = 4102444800.0


def parse_strict_date(value: Any) -> date | None:
    """Phân tích một giá trị thành datetime.date một cách nghiêm ngặt.

    Trả về:
        datetime.date nếu giá trị hợp lệ.
        None nếu giá trị là null, rỗng, sai định dạng, sai ngày lịch hoặc có hậu tố rác.
    """
    if value is None:
        return None

    # Nếu đã là đối tượng date hoặc datetime (ví dụ từ PyArrow Parquet)
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    # Xử lý số nguyên/số thực (Unix timestamp)
    if isinstance(value, (int, float)):
        # Tránh NaN hoặc Inf
        if not (-1e12 < value < 1e12):
            return None
        ts = float(value)
        # Hỗ trợ timestamp milliseconds nếu giá trị > 1e11 (sau năm 5138 theo giây)
        if ts > 1e11:
            ts = ts / 1000.0
        if MIN_TIMESTAMP_SEC <= ts <= MAX_TIMESTAMP_SEC:
            try:
                return datetime.fromtimestamp(ts, tz=timezone.utc).date()
            except (ValueError, OverflowError, OSError):
                return None
        return None

    # Nếu là chuỗi ký tự
    if isinstance(value, str):
        s = value.strip()
        if not s or s.lower() in {"none", "null", "nan", "nat", ""}:
            return None

        # 1. Định dạng chỉ có ngày: YYYY-MM-DD
        if ISO_DATE_REGEX.fullmatch(s):
            try:
                return datetime.strptime(s, "%Y-%m-%d").date()
            except ValueError:
                # Bắt lỗi ngày lịch sai (như 2024-02-30) mà regex vẫn qua
                return None

        # 2. Định dạng ngày giờ: YYYY-MM-DD[T ]HH:MM:SS...
        if ISO_DATETIME_REGEX.fullmatch(s):
            try:
                # Thay dấu cách bằng T để datetime.fromisoformat xử lý đồng nhất
                iso_str = s.replace(" ", "T")
                # Chuẩn hóa Z thành +00:00
                if iso_str.endswith("Z"):
                    iso_str = iso_str[:-1] + "+00:00"
                return datetime.fromisoformat(iso_str).date()
            except ValueError:
                return None

        # Tất cả các định dạng khác hoặc có hậu tố rác đều bị từ chối
        return None

    return None
