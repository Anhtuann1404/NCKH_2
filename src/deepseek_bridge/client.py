import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests

from .config import DeepSeekConfig
from .compressor import SYSTEM_PROMPT_DEEPSEEK, compress_task_context

logger = logging.getLogger("deepseek_bridge")

@dataclass
class DeepSeekResponse:
    content: str
    reasoning_content: Optional[str] = None
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    raw_response: Optional[Dict[str, Any]] = None

class DeepSeekClient:
    def __init__(self, config: Optional[DeepSeekConfig] = None):
        self.config = config or DeepSeekConfig()
        self.log_dir = Path(__file__).resolve().parent.parent.parent / "logs" / "deepseek"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_api_key(self):
        if not self.config.is_configured:
            raise ValueError(
                "DEEPSEEK_API_KEY chưa được cấu hình!\n"
                "Vui lòng tạo file .env tại thư mục gốc và thêm:\n"
                "DEEPSEEK_API_KEY=sk-...\n"
                "(Xem file .env.example để biết thêm chi tiết)"
            )

    def call_api(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> DeepSeekResponse:
        self._ensure_api_key()
        
        endpoint = f"{self.config.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        # deepseek-reasoner không hỗ trợ temperature tùy biến, mặc định API kiểm soát
        if model != "deepseek-reasoner" and temperature is not None:
            payload["temperature"] = temperature
        if max_tokens:
            payload["max_tokens"] = max_tokens

        response = requests.post(endpoint, headers=headers, json=payload, timeout=120)
        
        if response.status_code != 200:
            raise RuntimeError(
                f"Lỗi khi gọi DeepSeek API (HTTP {response.status_code}): {response.text}"
            )
            
        data = response.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        content = message.get("content", "")
        reasoning_content = message.get("reasoning_content")
        
        usage = data.get("usage", {})
        
        res = DeepSeekResponse(
            content=content,
            reasoning_content=reasoning_content,
            model=data.get("model", model),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            raw_response=data
        )
        
        self._save_log(model, messages, res)
        return res

    def _save_log(self, model: str, messages: List[Dict[str, str]], res: DeepSeekResponse):
        """Lưu lại nhật ký gọi DeepSeek phục vụ đối chiếu và kiểm chứng học thuật."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"session_{timestamp}_{model.replace('/', '_')}.json"
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "messages": messages,
            "response": {
                "content": res.content,
                "reasoning_content": res.reasoning_content,
                "usage": {
                    "prompt_tokens": res.prompt_tokens,
                    "completion_tokens": res.completion_tokens,
                    "total_tokens": res.total_tokens
                }
            }
        }
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

    def brainstorm(
        self,
        task: str,
        relevant_files: Optional[List[str]] = None,
        additional_instructions: str = ""
    ) -> DeepSeekResponse:
        """Sử dụng mô hình suy luận sâu (DeepSeek-R1) để brainstorm giải thuật hoặc kiến trúc."""
        compressed_task = compress_task_context(task, relevant_files)
        user_content = f"{compressed_task}\n\n{additional_instructions}".strip()
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_DEEPSEEK},
            {"role": "user", "content": f"[CHẾ ĐỘ BRAINSTORM - SUY LUẬN SÂU]\n\n{user_content}"}
        ]
        return self.call_api(messages, model=self.config.model_reasoning)

    def generate_code(
        self,
        task: str,
        relevant_files: Optional[List[str]] = None,
        additional_instructions: str = ""
    ) -> DeepSeekResponse:
        """Sử dụng DeepSeek để sinh mã nguồn chuẩn mực (deepseek-chat hoặc reasoner tùy cấu hình)."""
        compressed_task = compress_task_context(task, relevant_files)
        user_content = f"{compressed_task}\n\n{additional_instructions}".strip()
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_DEEPSEEK},
            {"role": "user", "content": f"[CHẾ ĐỘ SINH CODE - IMPLEMENTATION]\n\n{user_content}"}
        ]
        return self.call_api(messages, model=self.config.model_coding, temperature=0.2)
