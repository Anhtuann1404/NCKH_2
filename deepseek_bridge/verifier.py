import ast
import re
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class VerificationResult:
    passed: bool
    clean_code: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

class CodeVerifier:
    """Bộ kiểm tra mã nguồn (Verifier) đảm bảo code của DeepSeek không có lỗi cú pháp
    và tuân thủ các nguyên tắc bất biến của đề tài NCKH.
    """

    @staticmethod
    def extract_code(raw_text: str) -> str:
        """Trích xuất khối mã nguồn Python từ phản hồi markdown của mô hình."""
        pattern = r"```(?:python)?\s*\n(.*?)\n```"
        matches = re.findall(pattern, raw_text, re.DOTALL)
        if matches:
            # Lấy khối code dài nhất (thường là khối mã nguồn chính)
            return max(matches, key=len).strip()
        return raw_text.strip()

    def verify_code(self, raw_code: str, is_feature_or_model: bool = True) -> VerificationResult:
        """Kiểm tra cú pháp và các quy tắc học thuật bất biến."""
        code = self.extract_code(raw_code)
        errors = []
        warnings = []

        # 1. Kiểm tra lỗi cú pháp (Syntax Validation)
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Lỗi cú pháp Python tại dòng {e.lineno}: {e.msg}\n  -> {e.text}")
            return VerificationResult(passed=False, clean_code=code, errors=errors)

        # 2. Kiểm tra các quy tắc học thuật (Academic Invariant Rules)
        code_lower = code.lower()

        # Quy tắc 1: Không dùng cột 'target' hoặc 'label' làm đặc trưng mô hình
        if is_feature_or_model:
            forbidden_feature_patterns = [
                r"features\s*=\s*\[.*['\"]target['\"].*\]",
                r"features\s*=\s*\[.*['\"]label['\"].*\]",
                r"x\s*=\s*df\[.*['\"]target['\"].*\]",
                r"x\s*=\s*df\[.*['\"]label['\"].*\]",
            ]
            for pat in forbidden_feature_patterns:
                if re.search(pat, code_lower):
                    errors.append(
                        "VI PHẠM QUY TẮC: Cột 'target' hoặc 'label' từ nguồn bị đưa vào làm đặc trưng đầu vào X! "
                        "Theo đề cương, chỉ được trích xuất đặc trưng từ URL và HTML tĩnh."
                    )

        # Quy tắc 2: Cảnh báo chia tập ngẫu nhiên không theo nhóm domain (Leakage risk)
        if "train_test_split" in code and "group" not in code_lower and "stratifiedgroup" not in code_lower:
            warnings.append(
                "CẢNH BÁO RÒ RỈ: Phát hiện sử dụng `train_test_split` ngẫu nhiên thông thường. "
                "Theo giao thức NCKH, bắt buộc phải dùng GroupKFold hoặc GroupShuffleSplit theo domain (eTLD+1)."
            )

        # Quy tắc 3: Cảnh báo gọi mạng sống trong module trích xuất đặc trưng
        if "feature" in code_lower and ("urllib.request.urlopen" in code or "requests.get(" in code):
            warnings.append(
                "CẢNH BÁO: Phát hiện gọi mạng trực tiếp (requests.get / urlopen) trong mã nguồn đặc trưng. "
                "Đề cương quy định trích xuất offline từ HTML đã lưu trữ, không fetch mạng sống."
            )

        passed = len(errors) == 0
        return VerificationResult(
            passed=passed,
            clean_code=code,
            errors=errors,
            warnings=warnings
        )
