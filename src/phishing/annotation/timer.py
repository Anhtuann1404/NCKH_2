"""PausableTimer: Bộ đếm thời gian gán nhãn hỗ trợ tạm dừng và trừ thời gian nghỉ.

Thiết kế phục vụ kỷ luật Academic Research Skills (ARS) và yêu cầu kỹ thuật tiên quyết
của Lead D:
1. Đo lường chính xác thời gian lao động tập trung thực tế (`seconds_spent`).
2. Khấu trừ tự động toàn bộ thời gian tạm dừng / giải lao (idle / pause time)
   khỏi `seconds_spent`, ngăn chặn số liệu nhàn rỗi làm sai lệch mô hình công số PLAN-01.
3. Hỗ trợ dependency injection `time_fn` phục vụ kiểm thử đơn vị tất định.
"""

from __future__ import annotations

import time
from typing import Callable, List, Optional, Tuple


class PausableTimer:
    """Đồng hồ đếm thời gian cho phép tạm dừng (Pause) và tiếp tục (Resume).

    Attributes:
        time_fn: Hàm cung cấp thời gian đơn điệu (mặc định time.perf_counter).
    """

    def __init__(
        self,
        time_fn: Callable[[], float] = time.perf_counter,
        start_now: bool = True,
    ) -> None:
        self._time_fn = time_fn
        self._start_time: float | None = time_fn() if start_now else None
        self._is_paused: bool = False
        self._pause_start: float | None = None
        self._total_paused: float = 0.0
        self._pause_intervals: List[Tuple[float, float, float]] = []

    def start(self) -> None:
        """Bắt đầu đồng hồ nếu chưa chạy."""
        if self._start_time is None:
            self._start_time = self._time_fn()
            self._is_paused = False
            self._pause_start = None
            self._total_paused = 0.0
            self._pause_intervals.clear()

    def pause(self) -> float:
        """Tạm dừng đồng hồ. Trả về timestamp thời điểm bắt đầu tạm dừng."""
        if self._start_time is None:
            self.start()
        now = self._time_fn()
        if not self._is_paused:
            self._is_paused = True
            self._pause_start = now
        return self._pause_start if self._pause_start is not None else now

    def resume(self) -> float:
        """Tiếp tục đồng hồ sau tạm dừng. Trả về thời gian của đợt nghỉ vừa kết thúc (giây)."""
        if not self._is_paused or self._pause_start is None:
            return 0.0
        now = self._time_fn()
        duration = max(0.0, now - self._pause_start)
        self._total_paused += duration
        self._pause_intervals.append((self._pause_start, now, duration))
        self._is_paused = False
        self._pause_start = None
        return duration

    @property
    def is_paused(self) -> bool:
        """Trạng thái hiện tại có đang tạm dừng hay không."""
        return self._is_paused

    @property
    def total_paused_seconds(self) -> float:
        """Tổng thời gian đã tạm dừng (giây). Nếu đang tạm dừng, tính cả đợt hiện tại."""
        paused = self._total_paused
        if self._is_paused and self._pause_start is not None:
            now = self._time_fn()
            paused += max(0.0, now - self._pause_start)
        return paused

    def raw_elapsed(self) -> float:
        """Tổng thời gian trôi qua từ khi bắt đầu đến hiện tại (gồm cả thời gian nghỉ)."""
        if self._start_time is None:
            return 0.0
        now = self._time_fn()
        return round(max(0.0, now - self._start_time), 2)

    def active_elapsed(self) -> float:
        """Thời gian thao tác thực tế (đã trừ toàn bộ thời gian nghỉ), làm tròn 2 chữ số thập phân."""
        if self._start_time is None:
            return 0.0
        now = self._time_fn()
        total_wall = now - self._start_time
        active = total_wall - self.total_paused_seconds
        return round(max(0.0, active), 2)

    @property
    def pause_intervals(self) -> List[Tuple[float, float, float]]:
        """Danh sách các khoảng tạm dừng đã hoàn tất: (start_ts, end_ts, duration_seconds)."""
        return list(self._pause_intervals)

    def interactive_pause(
        self,
        input_fn: Callable[[str], str] = input,
        print_fn: Callable[..., None] = print,
    ) -> float:
        """Hiển thị thông báo tạm dừng tương tác, đợi người dùng tiếp tục, và tự động trừ thời gian."""
        self.pause()
        print_fn("\n" + "=" * 70)
        print_fn("[PAUSE] ĐỒNG HỒ ĐÃ TẠM DỪNG. Bạn có thể nghỉ ngơi.")
        print_fn("        Thời gian nghỉ sẽ được TỰ ĐỘNG TRỪ khỏi `seconds_spent`.")
        print_fn("        Nhấn [Enter] (hoặc gõ bất kỳ ký tự nào) khi quay lại để tiếp tục...")
        print_fn("=" * 70)
        try:
            input_fn("")
        except (KeyboardInterrupt, EOFError):
            # Nếu người dùng ấn Ctrl+C trong khi tạm dừng, giữ trạng thái và tiếp tục raise
            self.resume()
            raise
        dur = self.resume()
        print_fn(f"[RESUME] Đã tiếp tục làm việc! (Đã khấu trừ {dur:.2f} giây thời gian nghỉ)\n")
        return dur
