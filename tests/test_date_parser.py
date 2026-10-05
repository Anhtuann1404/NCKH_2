"""Bộ kiểm thử đơn vị cho parse_strict_date (Task DATA-01).

Kiểm tra:
1. Ngày hợp lệ dạng ISO (YYYY-MM-DD).
2. Chuỗi ngày giờ hợp lệ (YYYY-MM-DDTHH:MM:SS, kèm Z, kèm timezone, hoặc có dấu cách).
3. Ngày lịch sai (ví dụ 2024-02-30, 2025-04-31, 2023-02-29 không nhuận, tháng 13).
4. Hậu tố rác (ví dụ 2024-05-01garbage, 2024-07-02 extra) - chống lỗi d_str[:10].
5. Timestamp Unix hợp lệ và timestamp sai/âm/vượt ngưỡng.
6. Giá trị null, rỗng, whitespace, các chuỗi 'none', 'null'.
7. Các đối tượng datetime.date và datetime.datetime đã có sẵn.
8. Hai ranh giới của cửa sổ dữ liệu thực nghiệm (2024-07-02 và 2025-09-08).
"""

from datetime import date, datetime, timezone
import pytest

from phishing.data.date_parser import parse_strict_date


class TestStrictDateParser:
    """Kiểm thử tính chính xác và an toàn của bộ phân tích ngày."""

    def test_valid_iso_date_strings(self):
        assert parse_strict_date("2024-07-02") == date(2024, 7, 2)
        assert parse_strict_date("2025-09-08") == date(2025, 9, 8)
        assert parse_strict_date("2024-02-29") == date(2024, 2, 29)  # Năm nhuận hợp lệ
        assert parse_strict_date("2025-12-31") == date(2025, 12, 31)

    def test_valid_datetime_strings(self):
        # Dạng T
        assert parse_strict_date("2024-07-02T10:30:00") == date(2024, 7, 2)
        assert parse_strict_date("2024-07-02T10:30:00Z") == date(2024, 7, 2)
        assert parse_strict_date("2024-07-02T10:30:00.123456Z") == date(2024, 7, 2)
        assert parse_strict_date("2024-07-02T10:30:00+07:00") == date(2024, 7, 2)
        # Dạng khoảng trắng
        assert parse_strict_date("2025-09-08 14:15:00") == date(2025, 9, 8)
        assert parse_strict_date("2025-01-01 00:00:00.000") == date(2025, 1, 1)

    def test_invalid_calendar_dates(self):
        """Các ngày không tồn tại trên lịch phải bị từ chối dù có tiền tố đúng dạng."""
        assert parse_strict_date("2024-02-30") is None  # Tháng 2 không bao giờ có ngày 30
        assert parse_strict_date("2023-02-29") is None  # 2023 không phải năm nhuận
        assert parse_strict_date("2025-04-31") is None  # Tháng 4 chỉ có 30 ngày
        assert parse_strict_date("2024-06-31") is None  # Tháng 6 chỉ có 30 ngày
        assert parse_strict_date("2024-13-01") is None  # Không có tháng 13
        assert parse_strict_date("2024-00-10") is None  # Không có tháng 0
        assert parse_strict_date("2024-05-00") is None  # Không có ngày 0

    def test_garbage_suffixes_rejected(self):
        """Chống lỗi slicing d_str[:10]: các chuỗi có hậu tố rác phải bị từ chối 100%."""
        assert parse_strict_date("2024-05-01garbage") is None
        assert parse_strict_date("2024-07-02 extra text") is None
        assert parse_strict_date("2024-07-02T10:30:00garbage") is None
        assert parse_strict_date("2024-07-02-suffix") is None
        assert parse_strict_date("2024-07-02/additional/path") is None

    def test_malformed_formats_rejected(self):
        """Các định dạng không chuẩn mực không được chấp nhận ngầm định."""
        assert parse_strict_date("02-07-2024") is None  # DD-MM-YYYY
        assert parse_strict_date("2024/07/02") is None  # Slash format
        assert parse_strict_date("July 2, 2024") is None
        assert parse_strict_date("random_string") is None

    def test_null_and_empty_values(self):
        assert parse_strict_date(None) is None
        assert parse_strict_date("") is None
        assert parse_strict_date("   ") is None
        assert parse_strict_date("None") is None
        assert parse_strict_date("none") is None
        assert parse_strict_date("null") is None
        assert parse_strict_date("NaN") is None

    def test_existing_date_and_datetime_objects(self):
        d = date(2024, 7, 2)
        dt = datetime(2024, 7, 2, 15, 30, tzinfo=timezone.utc)
        assert parse_strict_date(d) == d
        assert parse_strict_date(dt) == d

    def test_timestamps(self):
        # 1720000000 -> 2024-07-03 UTC
        assert parse_strict_date(1720000000) == date(2024, 7, 3)
        # Timestamp âm hoặc quá xa
        assert parse_strict_date(-1000) is None
        assert parse_strict_date(5000000000) is None

    def test_corpus_window_boundaries(self):
        """Kiểm tra chính xác hai mốc ranh giới của corpus PhreshPhish đã kiểm kê."""
        min_boundary = parse_strict_date("2024-07-02")
        max_boundary = parse_strict_date("2025-09-08")
        assert min_boundary == date(2024, 7, 2)
        assert max_boundary == date(2025, 9, 8)
        assert min_boundary < max_boundary
