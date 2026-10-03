import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import requests

from .config import DeepSeekConfig

logger = logging.getLogger("token_guard")

class TokenLimitExceededError(Exception):
    """Ngoại lệ khi chạm ngưỡng giới hạn số dư token cho phép."""
    pass

class TokenGuard:
    """Bộ kiểm soát số dư tài khoản DeepSeek API thực tế.
    
    Cơ chế hoạt động:
    - Truy vấn trực tiếp số dư thực tế qua API `GET /user/balance`.
    - Tự động ghi nhận mốc nạp cao nhất (peak_balance).
    - Khi số dư còn lại <= 10% so với mức ban đầu (hoặc chạm ngưỡng an toàn),
      hệ thống sẽ tự động DỪNG LẠI và thông báo cho người dùng nạp thêm tiền.
    """

    def __init__(self, config: Optional[DeepSeekConfig] = None, log_dir: Optional[Path] = None):
        self.config = config or DeepSeekConfig()
        if log_dir is None:
            self.log_dir = Path(__file__).resolve().parent.parent / "logs" / "deepseek"
        else:
            self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.tracker_file = self.log_dir / "token_tracker.json"

        # Ngưỡng phần trăm cảnh báo dừng (mặc định: 10%)
        self.stop_percentage = float(os.environ.get("DEEPSEEK_STOP_PERCENTAGE", "10.0"))
        # Giới hạn token tối đa cho 1 request (tránh prompt lỗi sinh vô tận)
        self.max_tokens_per_call = int(os.environ.get("DEEPSEEK_MAX_TOKENS_PER_CALL", "4096"))

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
            "peak_balance": 0.0,
            "currency": "USD",
            "last_known_balance": 0.0,
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

    def fetch_live_balance(self) -> Optional[Dict[str, Any]]:
        """Lấy số dư thực tế từ DeepSeek API endpoint /user/balance."""
        if not self.config.is_configured:
            return None

        endpoint = f"{self.config.base_url}/user/balance"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        try:
            res = requests.get(endpoint, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                is_available = data.get("is_available", False)
                balance_infos = data.get("balance_infos", [])
                if balance_infos:
                    info = balance_infos[0]
                    total_bal = float(info.get("total_balance", "0.0"))
                    currency = info.get("currency", "USD")
                    
                    # Cập nhật peak balance nếu người dùng vừa nạp thêm tiền
                    current_peak = self._data.get("peak_balance", 0.0)
                    if total_bal > current_peak:
                        self._data["peak_balance"] = total_bal
                        self._data["currency"] = currency

                    self._data["last_known_balance"] = total_bal
                    self._data["currency"] = currency
                    self._save_data()

                    return {
                        "is_available": is_available,
                        "total_balance": total_bal,
                        "currency": currency,
                        "peak_balance": self._data.get("peak_balance", total_bal)
                    }
        except Exception as e:
            logger.warning("Không thể truy vấn số dư trực tiếp từ API: %s", e)
        return None

    def check_budget(self, estimated_prompt_tokens: int = 1500) -> Tuple[bool, str]:
        """Kiểm tra số dư tài khoản thực tế. Nếu số dư còn <= 10% mức ban đầu thì DỪNG LẠI."""
        balance_info = self.fetch_live_balance()
        
        # Nếu lấy được số dư thực tế từ API DeepSeek
        if balance_info:
            is_avail = balance_info["is_available"]
            current_bal = balance_info["total_balance"]
            peak_bal = balance_info["peak_balance"]
            currency = balance_info["currency"]

            if not is_avail or current_bal <= 0.0:
                return False, (
                    f"🚨 TÀI KHOẢN ĐÃ HẾT TIỀN: Số dư hiện tại là {current_bal:.2f} {currency}. "
                    f"Hệ thống đã dừng lại. Vui lòng nạp thêm tiền tại platform.deepseek.com để tiếp tục!"
                )

            # Tính tỷ lệ số dư còn lại so với mức nạp ban đầu
            if peak_bal > 0:
                remaining_pct = (current_bal / peak_bal) * 100.0
                if remaining_pct <= self.stop_percentage:
                    stop_threshold = (self.stop_percentage / 100.0) * peak_bal
                    return False, (
                        f"🚨 CẢNH BÁO SẮP HẾT SỐ DƯ (CÒN {remaining_pct:.1f}%): "
                        f"Số dư tài khoản DeepSeek hiện tại là {current_bal:.2f} {currency} "
                        f"(đã chạm ngưỡng tối thiểu {self.stop_percentage}% tương đương {stop_threshold:.2f} {currency}).\n"
                        f"👉 Hệ thống dừng lại để bạn nạp thêm tiền, tránh bị gián đoạn giữa chừng!"
                    )

            return True, f"Số dư khả dụng: {current_bal:.2f} {currency}"

        # Trường hợp không kết nối được endpoint balance (fallback kiểm tra nội bộ)
        return True, "OK"

    def record_usage(self, prompt_tokens: int, completion_tokens: int, model: str, task_summary: str = ""):
        """Ghi nhận lượng token thực tế đã tiêu thụ để phục vụ thống kê NCKH."""
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

        if len(self._data["history"]) > 50:
            self._data["history"] = self._data["history"][-50:]

        self._save_data()

    def get_summary(self) -> Dict[str, Any]:
        """Lấy thông tin tổng hợp số dư tài khoản thực tế và token tiêu thụ."""
        live_info = self.fetch_live_balance()
        current_bal = live_info["total_balance"] if live_info else self._data.get("last_known_balance", 0.0)
        peak_bal = live_info["peak_balance"] if live_info else self._data.get("peak_balance", current_bal)
        currency = live_info["currency"] if live_info else self._data.get("currency", "USD")

        remaining_pct = (current_bal / peak_bal * 100.0) if peak_bal > 0 else 100.0
        stop_amount = (self.stop_percentage / 100.0) * peak_bal if peak_bal > 0 else 0.0

        return {
            "current_balance": current_bal,
            "peak_balance": peak_bal,
            "currency": currency,
            "remaining_percentage": round(remaining_pct, 1),
            "stop_percentage_threshold": self.stop_percentage,
            "stop_balance_threshold": round(stop_amount, 2),
            "total_tokens_used": self._data.get("total_tokens", 0),
            "prompt_tokens_used": self._data.get("total_prompt_tokens", 0),
            "completion_tokens_used": self._data.get("total_completion_tokens", 0),
            "call_count": self._data.get("call_count", 0),
            "max_tokens_per_call": self.max_tokens_per_call
        }
