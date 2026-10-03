import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

from .config import DeepSeekConfig
from .client import DeepSeekClient, DeepSeekResponse
from .compressor import compress_task_context, SYSTEM_PROMPT_DEEPSEEK
from .token_guard import TokenGuard, TokenLimitExceededError
from .verifier import CodeVerifier, VerificationResult

logger = logging.getLogger("deepseek_orchestrator")

@dataclass
class OrchestrationResult:
    status: str  # "SUCCESS" | "NEEDS_USER_DECISION" | "TOKEN_LIMIT_EXCEEDED" | "ERROR"
    code: str = ""
    reasoning: Optional[str] = None
    attempts: int = 0
    max_retries: int = 3
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    token_usage: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""

class Orchestrator:
    """Bộ điều phối (Orchestrator) kết hợp:
    1. Nén ngữ cảnh (Context Compression)
    2. Sinh mã và suy luận qua DeepSeek V4
    3. Kiểm định mã nguồn (Code Verification: cú pháp & quy tắc NCKH)
    4. Giới hạn vòng lặp tự sửa lỗi (Max 3-4 lần)
    5. Kiểm soát ngân sách token (Token Guard)
    """

    def __init__(self, config: Optional[DeepSeekConfig] = None):
        self.config = config or DeepSeekConfig()
        self.client = DeepSeekClient(self.config)
        self.token_guard = TokenGuard()
        self.verifier = CodeVerifier()

    def run_task(
        self,
        task: str,
        relevant_files: Optional[List[str]] = None,
        max_retries: int = 3,
        model: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> OrchestrationResult:
        """Thực thi tác vụ lập trình với vòng lặp phản hồi có kiểm soát ngân sách token."""
        
        # 1. Kiểm tra ngân sách token trước khi bắt đầu
        can_proceed, budget_msg = self.token_guard.check_budget(estimated_prompt_tokens=2000)
        if not can_proceed:
            return OrchestrationResult(
                status="TOKEN_LIMIT_EXCEEDED",
                max_retries=max_retries,
                token_usage=self.token_guard.get_summary(),
                message=budget_msg
            )

        target_model = model or self.config.model_coding
        compressed_context = compress_task_context(task, relevant_files)
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_DEEPSEEK},
            {"role": "user", "content": f"[YÊU CẦU LẬP TRÌNH CHO ĐỀ TÀI NCKH]\n\n{compressed_context}"}
        ]

        attempt_history = []
        last_code = ""
        last_errors = []
        last_warnings = []
        last_reasoning = None

        print(f"\n🔄 [Vòng điều phối] Bắt đầu tác vụ: '{task[:60]}...' (Max retries: {max_retries})")

        for attempt in range(1, max_retries + 1):
            print(f"👉 Lần thử {attempt}/{max_retries} — Đang gửi yêu cầu sang DeepSeek ({target_model})...")
            
            try:
                # Gọi API DeepSeek
                response: DeepSeekResponse = self.client.call_api(
                    messages=messages,
                    model=target_model,
                    temperature=0.2
                )
            except Exception as e:
                return OrchestrationResult(
                    status="ERROR",
                    attempts=attempt,
                    max_retries=max_retries,
                    errors=[str(e)],
                    message=f"Lỗi kết nối API DeepSeek: {e}"
                )

            # Cập nhật Token Guard
            self.token_guard.record_usage(
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                model=target_model,
                task_summary=task
            )

            raw_code = response.content
            last_reasoning = response.reasoning_content

            # Kiểm định code bởi Antigravity Verifier
            verification: VerificationResult = self.verifier.verify_code(raw_code)
            last_code = verification.clean_code
            last_errors = verification.errors
            last_warnings = verification.warnings

            attempt_history.append({
                "attempt": attempt,
                "passed": verification.passed,
                "errors": verification.errors,
                "warnings": verification.warnings,
                "tokens": {
                    "prompt": response.prompt_tokens,
                    "completion": response.completion_tokens
                }
            })

            # Nếu kiểm định thành công -> Hoàn tất!
            if verification.passed:
                print(f"✅ Lần thử {attempt}/{max_retries}: Mã nguồn đạt chuẩn cú pháp và các quy tắc NCKH!")
                
                if output_path:
                    out_file = Path(output_path)
                    out_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(out_file, "w", encoding="utf-8") as f:
                        f.write(verification.clean_code)
                    print(f"💾 Đã lưu code vào: {out_file}")

                return OrchestrationResult(
                    status="SUCCESS",
                    code=verification.clean_code,
                    reasoning=last_reasoning,
                    attempts=attempt,
                    max_retries=max_retries,
                    warnings=verification.warnings,
                    token_usage=self.token_guard.get_summary(),
                    history=attempt_history,
                    message="Mã nguồn hợp lệ và đã vượt qua toàn bộ các bước kiểm tra của Antigravity."
                )

            # Nếu phát hiện lỗi và vẫn còn lượt thử -> Gửi feedback yêu cầu DeepSeek sửa
            print(f"⚠️ Lần thử {attempt}/{max_retries} phát hiện {len(verification.errors)} lỗi:")
            for err in verification.errors:
                print(f"   ❌ {err}")

            if attempt < max_retries:
                # Kiểm tra lại ngân sách trước khi retry
                can_retry, retry_msg = self.token_guard.check_budget(estimated_prompt_tokens=1500)
                if not can_retry:
                    return OrchestrationResult(
                        status="TOKEN_LIMIT_EXCEEDED",
                        code=last_code,
                        attempts=attempt,
                        max_retries=max_retries,
                        errors=last_errors,
                        token_usage=self.token_guard.get_summary(),
                        message=retry_msg
                    )

                print(f"🔁 Đang đóng gói lỗi và gửi yêu cầu sửa code lần {attempt + 1}...")
                feedback = (
                    f"[PHẢN HỒI KIỂM ĐỊNH LẦN {attempt} - PHÁT HIỆN LỖI]:\n"
                    f"Mã nguồn bạn vừa sinh gặp các vấn đề sau:\n"
                    + "\n".join(f"- {err}" for err in verification.errors)
                    + "\n\nYêu cầu: Hãy phân tích nguyên nhân lỗi, sửa lại và trả về toàn bộ khối mã nguồn hoàn chỉnh đã khắc phục."
                )
                messages.append({"role": "assistant", "content": raw_code})
                messages.append({"role": "user", "content": feedback})

        # Nếu đã chạm ngưỡng max_retries mà vẫn còn lỗi -> DỪNG LẠI và xin quyết định từ người dùng
        print(f"\n🛑 ĐÃ ĐẠT GIỚI HẠN {max_retries} LẦN SỬA LỖI TỰ ĐỘNG.")
        return OrchestrationResult(
            status="NEEDS_USER_DECISION",
            code=last_code,
            reasoning=last_reasoning,
            attempts=max_retries,
            max_retries=max_retries,
            errors=last_errors,
            warnings=last_warnings,
            token_usage=self.token_guard.get_summary(),
            history=attempt_history,
            message=(
                f"Đã thực hiện {max_retries} lần yêu cầu DeepSeek tự sửa nhưng vẫn còn lỗi tồn đọng. "
                f"Hệ thống tạm dừng vòng lặp để xin ý kiến của bạn."
            )
        )
