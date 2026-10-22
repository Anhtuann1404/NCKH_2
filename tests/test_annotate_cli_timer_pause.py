"""Kiểm thử đơn vị và tích hợp cho cơ chế PausableTimer và tính năng Pause/Resume của CLI.

Quy chuẩn ARS & Safety:
1. Kiểm thử tất định bằng mock clock độc lập (deterministic mock time_fn).
2. Kiểm tra chứng minh toán học: `seconds_spent = raw_wall_time - total_paused_time`.
3. Kiểm tra tính lũy kế của nhiều lần tạm dừng liên tiếp (multiple pause/resume cycles).
4. Kiểm tra tính ổn định: active elapsed không tăng trong lúc đang pause.
5. Kiểm tra an toàn giao diện CLI: gõ :p / :pause tại prompt_choice, prompt_text_input
   và display_sample_and_allow_reading kích hoạt tạm dừng và phục hồi đúng thời gian.
"""

from __future__ import annotations

import io
from pathlib import Path
import pytest

from phishing.annotation.timer import PausableTimer
from scripts.annotate_cli import (
    CLASS_LABEL_CHOICES,
    display_sample_and_allow_reading,
    prompt_choice,
    prompt_text_input,
)


class MockClock:
    """Đồng hồ giả lập có thể điều khiển thời gian phục vụ kiểm thử tất định."""

    def __init__(self, start_time: float = 1000.0) -> None:
        self.current_time = start_time

    def time(self) -> float:
        return self.current_time

    def advance(self, seconds: float) -> None:
        assert seconds >= 0, "Không được lùi thời gian"
        self.current_time += seconds


class TestPausableTimerUnit:
    """Tập kiểm thử đơn vị cho lớp PausableTimer."""

    def test_timer_continuous_active_without_pause(self):
        """Chứng minh khi không tạm dừng, active_elapsed bằng raw_elapsed."""
        clock = MockClock(100.0)
        timer = PausableTimer(time_fn=clock.time, start_now=True)

        clock.advance(15.75)
        assert timer.raw_elapsed() == 15.75
        assert timer.active_elapsed() == 15.75
        assert timer.total_paused_seconds == 0.0
        assert not timer.is_paused
        assert len(timer.pause_intervals) == 0

    def test_timer_single_pause_and_resume_deduction(self):
        """Chứng minh một lần tạm dừng 20s trong tổng thời gian 50s cho active_elapsed = 30s."""
        clock = MockClock(200.0)
        timer = PausableTimer(time_fn=clock.time, start_now=True)

        # Làm việc 10s
        clock.advance(10.0)
        assert timer.active_elapsed() == 10.0

        # Tạm dừng nghỉ 20s
        pause_ts = timer.pause()
        assert pause_ts == 210.0
        assert timer.is_paused

        # Trong lúc nghỉ, thời gian trôi thêm 20s nhưng active_elapsed vẫn giữ nguyên 10s
        clock.advance(20.0)
        assert timer.is_paused
        assert timer.active_elapsed() == 10.0
        assert timer.total_paused_seconds == 20.0
        assert timer.raw_elapsed() == 30.0

        # Quay lại làm việc
        resumed_duration = timer.resume()
        assert resumed_duration == 20.0
        assert not timer.is_paused
        assert timer.total_paused_seconds == 20.0

        # Làm việc tiếp thêm 20s
        clock.advance(20.0)
        assert timer.raw_elapsed() == 50.0  # 10 + 20 (nghỉ) + 20
        assert timer.active_elapsed() == 30.0  # 10 + 20 (làm việc)
        assert len(timer.pause_intervals) == 1
        assert timer.pause_intervals[0] == (210.0, 230.0, 20.0)

    def test_timer_multiple_pauses_accumulate_correctly(self):
        """Chứng minh nhiều lần tạm dừng liên tiếp được tích lũy chính xác."""
        clock = MockClock(0.0)
        timer = PausableTimer(time_fn=clock.time, start_now=True)

        # Làm việc 5s
        clock.advance(5.0)

        # Nghỉ lần 1: 10s
        timer.pause()
        clock.advance(10.0)
        timer.resume()

        # Làm việc tiếp 15s
        clock.advance(15.0)

        # Nghỉ lần 2: 25s
        timer.pause()
        clock.advance(25.0)
        timer.resume()

        # Làm việc tiếp 10s
        clock.advance(10.0)

        # Tổng: raw = 5 + 10 + 15 + 25 + 10 = 65s
        # Nghỉ = 10 + 25 = 35s
        # Active = 5 + 15 + 10 = 30s
        assert timer.raw_elapsed() == 65.0
        assert timer.total_paused_seconds == 35.0
        assert timer.active_elapsed() == 30.0
        assert len(timer.pause_intervals) == 2
        assert timer.pause_intervals[0][2] == 10.0
        assert timer.pause_intervals[1][2] == 25.0

    def test_timer_idempotent_calls(self):
        """Chứng minh gọi pause 2 lần liên tiếp hoặc resume khi chưa pause không làm sai lệch."""
        clock = MockClock(0.0)
        timer = PausableTimer(time_fn=clock.time, start_now=True)

        # Resume khi chưa pause trả về 0.0
        assert timer.resume() == 0.0
        assert timer.total_paused_seconds == 0.0

        clock.advance(5.0)
        p1 = timer.pause()
        clock.advance(2.0)
        p2 = timer.pause()  # Gọi lại khi đang pause
        assert p1 == p2
        clock.advance(3.0)
        dur = timer.resume()
        assert dur == 5.0
        assert timer.total_paused_seconds == 5.0
        assert timer.active_elapsed() == 5.0

    def test_timer_interactive_pause_custom_io(self):
        """Chứng minh interactive_pause dừng đồng hồ, đợi input và tiếp tục thành công."""
        clock = MockClock(10.0)
        timer = PausableTimer(time_fn=clock.time, start_now=True)

        clock.advance(8.0)  # Active: 8s

        printed = []

        def mock_input(prompt: str) -> str:
            # Giả lập người dùng tạm dừng trong 15s trước khi ấn phím
            clock.advance(15.0)
            return ""

        dur = timer.interactive_pause(input_fn=mock_input, print_fn=lambda msg: printed.append(msg))
        assert dur == 15.0
        assert timer.active_elapsed() == 8.0
        assert timer.total_paused_seconds == 15.0
        assert any("[PAUSE]" in p for p in printed)
        assert any("[RESUME]" in p for p in printed)


class TestCLIIntegrationTimerPause:
    """Kiểm thử tích hợp các hàm giao diện nhập liệu của CLI có hỗ trợ tạm dừng."""

    def test_prompt_choice_with_pause_command(self, monkeypatch):
        """Chứng minh gõ :p tại prompt_choice sẽ kích hoạt tạm dừng và hỏi lại."""
        clock = MockClock(100.0)
        timer = PausableTimer(time_fn=clock.time, start_now=True)

        clock.advance(5.0)

        # Giả lập chuỗi nhập: đầu tiên nhập ':p', sau đó khi được hỏi lại thì chọn '1'
        inputs = iter([":p", "", "1"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        # Khi pause chạy, giả lập thời gian trôi thêm 30s
        orig_interactive_pause = timer.interactive_pause

        def simulated_interactive_pause():
            clock.advance(30.0)
            timer._total_paused += 30.0
            timer._pause_intervals.append((105.0, 135.0, 30.0))
            return 30.0

        monkeypatch.setattr(timer, "interactive_pause", simulated_interactive_pause)

        res = prompt_choice("Chọn nhãn", CLASS_LABEL_CHOICES, timer=timer)
        assert res == "phishing"
        assert timer.total_paused_seconds == 30.0
        assert timer.active_elapsed() == 5.0

    def test_prompt_text_input_with_pause_command(self, monkeypatch):
        """Chứng minh gõ :pause tại prompt_text_input kích hoạt tạm dừng."""
        clock = MockClock(50.0)
        timer = PausableTimer(time_fn=clock.time, start_now=True)

        clock.advance(4.0)

        inputs = iter([":pause", "", "Bằng chứng quan sát được"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        def simulated_interactive_pause():
            clock.advance(20.0)
            timer._total_paused += 20.0
            return 20.0

        monkeypatch.setattr(timer, "interactive_pause", simulated_interactive_pause)

        val = prompt_text_input("Ghi chú bằng chứng", required=True, timer=timer)
        assert val == "Bằng chứng quan sát được"
        assert timer.total_paused_seconds == 20.0
        assert timer.active_elapsed() == 4.0

    def test_display_sample_and_allow_reading_pause(self, monkeypatch):
        """Chứng minh gõ 'p' trong màn hình đọc văn bản kích hoạt tạm dừng."""
        sample = {
            "sample_id": "SMP-TEST-001",
            "url": "https://test.local/",
            "page_text": "A" * 1200,  # Dài hơn 600 ký tự để kích hoạt vòng lặp đọc
            "structure_summary": {"forms": 1, "inputs": 2, "password_inputs": 0, "has_login_form": False, "buttons": 1, "external_links": 0},
            "translation_provided": False,
        }

        clock = MockClock(0.0)
        timer = PausableTimer(time_fn=clock.time, start_now=True)

        clock.advance(6.0)

        # Lần 1: nhập 'p' để tạm dừng, Lần 2: Enter để tiếp tục
        inputs = iter(["p", "", ""])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        def simulated_interactive_pause():
            clock.advance(40.0)
            timer._total_paused += 40.0
            return 40.0

        monkeypatch.setattr(timer, "interactive_pause", simulated_interactive_pause)

        display_sample_and_allow_reading(sample, 1, 1, interactive=True, timer=timer)
        assert timer.total_paused_seconds == 40.0
        assert timer.active_elapsed() == 6.0
