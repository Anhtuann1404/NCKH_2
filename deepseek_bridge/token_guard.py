import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple

class TokenLimitExceededError(Exception):
    """Ngoại lệ khi chạm ngưỡng giới hạn token cho phép."""
    pass

class TokenGuard:
    """Bộ kiểm soát hạn mức token (Token Guard) giúp tránh cạn kiệt ngân sách API."""

    def __init__(self, log_dir: Path | None = None):
        if log_dir is None:
            self.log_dir = Path(__file__).resolve().parent.parent / "logs" / "deepseek"
        else:
            self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.tracker_file = self.log_dir / "token_tracker.json"

        # Đọc cấu hình giới hạn từ biến môi trường (hoặc mặc định)
        self.max_tokens_per_call = int(os.environ.get("DEEPSEEK_MAX_TOKENS_PER_CALL", "4096"))
        self.session_token_limit = int(os.environ.get("DEEPSEEK_SESSION_TOKEN_LIMIT", "100000"))

        self._data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        if self.tracker_file.is_file():
            try:
                with open(self.tracker_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "session_start": datetime.now().isoformat(),
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "call_count": 0,
            "history": []
        }

    def _save_data(self):
        try:
            with open(self.tracker_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def check_budget(self, estimated_prompt_tokens: int = 1500) -> Tuple[bool, str]:
        """Kiểm tra xem yêu cầu tiếp theo có vượt quá hạn mức phiên không."""
        current_used = self._data.get("total_tokens", 0)
        projected = current_used + estimated_prompt_tokens
        
        if current_used >= self.session_token_limit:
            msg = (
                f"🚨 CẢNH BÁO HẠN MỨC TOKEN: Bạn đã dùng hết {current_used:,} / {self.session_token_limit:,} tokens "
                f"của phiên hiện tại. Để bảo vệ ngân sách, hệ thống tạm dừng gọi API."
            )
            return False, msg
            
        if projected > self.session_token_limit:
            msg = (
                f"⚠️ Yêu cầu sắp tới (dự kiến ~{projected:,} tokens) có thể vượt quá hạn mức phiên "
                f"({self.session_token_limit:,} tokens). Hiện tại đã dùng {current_used:,} tokens."
            )
            return True, msg

        return True, "OK"

    def record_usage(self, prompt_tokens: int, completion_tokens: int, model: str, task_summary: str = ""):
        """Ghi nhận lượng token thực tế đã tiêu thụ."""
        total = prompt_tokens + completion_tokens
        self._data["total_prompt_tokens"] += prompt_tokens
        self._data["total_completion_tokens"] += completion_tokens
        self._data["total_tokens"] += total
        self._data["call_count"] += 1

        self._data["history"].append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total": total,
            "task_summary": task_summary[:100]
        })

        # Giữ tối đa 50 bản ghi lịch sử gần nhất
        if len(self._data["history"]) > 50:
            self._data["history"] = self._data["history"][-50:]

        self._save_data()

    def get_summary(self) -> Dict[str, Any]:
        """Lấy thông tin tổng hợp lượng token đã sử dụng và còn lại."""
        used = self._data.get("total_tokens", 0)
        remaining = max(0, self.session_token_limit - used)
        pct_used = (used / self.session_token_limit * 100) if self.session_token_limit > 0 else 0
        return {
            "total_tokens_used": used,
            "prompt_tokens_used": self._data.get("total_prompt_tokens", 0),
            "completion_tokens_used": self._data.get("total_completion_tokens", 0),
            "call_count": self._data.get("call_count", 0),
            "session_limit": self.session_token_limit,
            "remaining_budget": remaining,
            "percentage_used": round(pct_used, 1),
            "max_tokens_per_call": self.max_tokens_per_call
        }

    def reset_session(self):
        """Đặt lại hạn mức phiên mới (khi người dùng đồng ý tiếp tục)."""
        self._data["session_start"] = datetime.now().isoformat()
        self._data["total_prompt_tokens"] = 0
        self._data["total_completion_tokens"] = 0
        self._data["total_tokens"] = 0
        self._data["call_count"] = 0
        self._save_data()
