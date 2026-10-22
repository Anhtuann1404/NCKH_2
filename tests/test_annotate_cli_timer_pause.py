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
import json
from pathlib import Path
import pytest

from phishing.annotation.blind_view import AnnotationRecord, validate_annotation_record
from phishing.annotation.timer import PausableTimer
from scripts.annotate_cli import (
    CLASS_LABEL_CHOICES,
    annotate_interactive_session,
    display_sample_and_allow_reading,
    load_already_annotated_sample_ids,
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

    def test_timer_abort_during_pause_cancels_and_does_not_accumulate(self):
        """Chứng minh (Điều kiện 5a): Thoát giữa lúc pause (KeyboardInterrupt) không cộng dồn thời gian nghỉ."""
        clock = MockClock(100.0)
        timer = PausableTimer(time_fn=clock.time, start_now=True)

        clock.advance(10.0)  # Active: 10s

        # Lần 1: Nghỉ 5s hoàn tất
        timer.pause()
        clock.advance(5.0)
        timer.resume()
        assert timer.pause_count == 1
        assert timer.total_paused_seconds == 5.0
        assert timer.active_elapsed() == 10.0

        # Lần 2: Bắt đầu pause bằng interactive_pause nhưng bị Ctrl+C / KeyboardInterrupt giữa chừng
        def mock_input_abort(prompt: str) -> str:
            clock.advance(12.0)
            raise KeyboardInterrupt

        with pytest.raises(KeyboardInterrupt):
            timer.interactive_pause(input_fn=mock_input_abort, print_fn=lambda _: None)

        # Trạng thái sau khi abort: cancel_pause đã được gọi
        assert not timer.is_paused
        # Số lần pause vẫn là 1 (không tăng lên 2)
        assert timer.pause_count == 1
        # Tổng thời gian pause vẫn là 5.0 (không bị cộng thêm 12s dở dang)
        assert timer.total_paused_seconds == 5.0
        # Khoảng thời gian dở dang không được lưu vào pause_intervals
        assert len(timer.pause_intervals) == 1
        assert timer.pause_intervals[0][2] == 5.0

    def test_timer_seconds_spent_non_negative_under_clock_skew(self):
        """Chứng minh (Điều kiện 6a): seconds_spent luôn >= 0.0 ngay cả khi đồng hồ lệch/lùi."""
        time_vals = [100.0, 95.0, 90.0]  # Giả lập clock lùi thời gian
        def skewed_time() -> float:
            return time_vals.pop(0) if time_vals else 90.0

        timer = PausableTimer(time_fn=skewed_time, start_now=True)
        assert timer.raw_elapsed() >= 0.0
        assert timer.active_elapsed() >= 0.0


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

    def test_record_validation_and_audit_trail_preserves_pause_metrics(self):
        """Chứng minh (Điều kiện 6b & 7): Schema bảo toàn pause_count, paused_seconds và cấm giá trị âm."""
        sample_dict = {
            "annotator_id": "A",
            "sample_id": "TEST-SMP-001",
            "pass_id": 1,
            "class_label": "benign",
            "primary_org_status": "no_clear_target",
            "catalog_status": "unresolved",
            "observed_service": "None",
            "org_targets": [],
            "org_evidence": [],
            "primary_org": "no_clear_target",
            "identity_role": "unclear",
            "domain_role": "unverified",
            "evidence_note": "Trang tin tức cá nhân bình thường",
            "seconds_spent": 42.5,
            "pause_count": 2,
            "paused_seconds": 15.0,
            "random_subset": False,
            "difficult_case": False,
            "codebook_version": "1.1.0",
            "is_dry_run": False,
            "is_synthetic": False,
            "dataset_id": "test_ds",
            "dataset_hash": "a" * 64,
            "codebook_hash": "b" * 64,
            "sampling_plan_version": "v1.1.0",
            "sample_content_hash": "c" * 64,
            "timestamp_utc": "2026-10-23T00:00:00Z",
            "primary_phishing_type": None,
            "hard_benign_type": None,
            "confidence": "high",
        }

        # 1. Bảo toàn chính xác các trường kiểm toán cho PLAN-01
        record = validate_annotation_record(sample_dict, catalog_org_ids=set())
        assert record.pause_count == 2
        assert record.paused_seconds == 15.0
        assert record.seconds_spent == 42.5

        data_dict = record.to_dict()
        assert data_dict["pause_count"] == 2
        assert data_dict["paused_seconds"] == 15.0
        assert isinstance(data_dict["pause_count"], int)
        assert isinstance(data_dict["paused_seconds"], float)

        # 2. Chặn giá trị âm fail-closed (Điều kiện 6b)
        bad_spent = dict(sample_dict, seconds_spent=-5.0)
        with pytest.raises(ValueError, match="seconds_spent=-5.0 không được âm"):
            validate_annotation_record(bad_spent, catalog_org_ids=set())

        bad_pause_count = dict(sample_dict, pause_count=-1)
        with pytest.raises(ValueError, match="pause_count=-1 không được âm"):
            validate_annotation_record(bad_pause_count, catalog_org_ids=set())

        bad_paused_sec = dict(sample_dict, paused_seconds=-0.5)
        with pytest.raises(ValueError, match="paused_seconds=-0.5 không được âm"):
            validate_annotation_record(bad_paused_sec, catalog_org_ids=set())

    def test_session_abort_during_prompt_does_not_duplicate_or_corrupt_records(self, tmp_path, monkeypatch):
        """Chứng minh (Điều kiện 5b): Thoát giữa chừng không ghi trùng và không lưu bản ghi dở dang."""
        input_file = tmp_path / "blind_input.json"
        output_file = tmp_path / "annotated.jsonl"
        manifest_file = tmp_path / "manifest.json"

        # Chuẩn bị 2 mẫu dữ liệu mô phỏng
        input_data = {
            "dataset_id": "SYNTHETIC-TEST",
            "dataset_type": "synthetic_test",
            "is_synthetic": True,
            "sampling_plan_version": "TEST-PLAN",
            "codebook_version": "1.0.0",
            "random_subset_default": False,
            "samples": [
                {
                    "sample_id": "SMP-001",
                    "url": "https://example.com/login",
                    "page_text": "Sample 1 page text",
                    "structure_summary": {"forms": 1},
                },
                {
                    "sample_id": "SMP-002",
                    "url": "https://test.com/home",
                    "page_text": "Sample 2 page text",
                    "structure_summary": {"forms": 0},
                },
            ],
        }
        input_file.write_text(json.dumps(input_data, ensure_ascii=False), encoding="utf-8")

        # Mock các hàm tương tác:
        # Ở mẫu SMP-001: hoàn thành bình thường (cần 5 lần prompt_choice trong Codebook 1.0.0)
        # Ở mẫu SMP-002: tại câu hỏi đầu tiên (lần gọi thứ 6) bị ngắt (KeyboardInterrupt)
        call_count = {"prompt_choice": 0}

        def mock_display(sample, idx, total, interactive=True, timer=None):
            pass

        def mock_prompt_choice(prompt, choices, timer=None):
            call_count["prompt_choice"] += 1
            if call_count["prompt_choice"] > 5:  # Bắt đầu mẫu SMP-002
                raise KeyboardInterrupt
            return list(choices.values())[0]

        def mock_prompt_text(prompt, default_val="", required=False, timer=None):
            return default_val or "ghi chú test"

        monkeypatch.setattr("scripts.annotate_cli.display_sample_and_allow_reading", mock_display)
        monkeypatch.setattr("scripts.annotate_cli.prompt_choice", mock_prompt_choice)
        monkeypatch.setattr("scripts.annotate_cli.prompt_text_input", mock_prompt_text)

        # Đợt 1: Chạy và bị Ctrl+C ở mẫu SMP-002
        annotate_interactive_session(
            annotator_id="A",
            input_path=input_file,
            output_path=output_file,
        )

        # Kiểm tra đợt 1: Chỉ có 1 bản ghi của SMP-001, tuyệt đối không có SMP-002 dở dang
        lines_1 = [json.loads(line) for line in output_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(lines_1) == 1
        assert lines_1[0]["sample_id"] == "SMP-001"

        # Đợt 2: Người gán chạy lại lệnh sau khi nghỉ
        call_count["prompt_choice"] = 0
        def mock_prompt_choice_resume(prompt, choices, timer=None):
            return list(choices.values())[0]
        monkeypatch.setattr("scripts.annotate_cli.prompt_choice", mock_prompt_choice_resume)

        annotate_interactive_session(
            annotator_id="A",
            input_path=input_file,
            output_path=output_file,
        )

        # Kiểm tra đợt 2: SMP-001 được bỏ qua (không ghi trùng), SMP-002 được hoàn thành
        lines_2 = [json.loads(line) for line in output_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(lines_2) == 2
        assert [r["sample_id"] for r in lines_2] == ["SMP-001", "SMP-002"]
