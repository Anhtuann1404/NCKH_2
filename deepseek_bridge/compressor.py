"""Module nén ngữ cảnh dự án NCKH để cấp cho DeepSeek.
Đảm bảo DeepSeek nhận đúng các ràng buộc cốt lõi mà không bị tràn token.
"""

from pathlib import Path
from typing import List, Optional

PROJECT_INVARIANTS = """
[BỘ NGUYÊN TẮC BẮT BUỘC - DỰ ÁN NCKH PHISHING]:
1. Đề tài: Phát hiện website phishing mạo danh tổ chức bằng học máy kết hợp URL và nội dung trang.
2. Lõi khoa học: Đo giá trị tăng thêm của bộ tín hiệu mạo danh có cấu trúc (Tổ chức - Tên miền - Ý định) khi bổ sung vào mô hình cơ sở URL + DOM + Text trên miền chưa gặp (unseen domains).
3. Chống rò rỉ (Zero Data Leakage):
   - Mọi phép chia tập (CV / train-test) BẮT BUỘC nhóm theo eTLD+1 domain.
   - Không để cùng một domain hoặc template gần trùng xuất hiện ở cả train và test.
4. Ràng buộc nhãn & đặc trưng:
   - TUYỆT ĐỐI KHÔNG dùng nhãn nguồn (target, label, metadata) làm đặc trưng đầu vào mô hình.
   - Mọi đặc trưng phải trích xuất hoàn toàn offline từ URL và file HTML tĩnh đã lưu (KHÔNG thực thi JavaScript, KHÔNG fetch tài nguyên ngoài).
5. Xử lý hạ tầng dùng chung (Shared Hosting / UGC):
   - Các nền tảng Google Sites, SharePoint, Azure Blob, Google Forms... là hạ tầng người dùng xuất bản. KHÔNG coi là domain chính thức của thương hiệu chỉ vì thuộc máy chủ Google/Microsoft. Đánh dấu cờ 'shared_unverified'.
6. 14 mã tổ chức chuẩn:
   - Microsoft, Google, Apple, Amazon, Meta, LinkedIn, Adobe, Booking, PayPal, DHL, Spotify, Alibaba, Mastercard, X/Twitter.
7. Giao thức thực nghiệm:
   - Mô hình: M0 (URL) -> M1 (URL+DOM) -> M2 (M1+Text TF-IDF) -> M3 (M2+Tín hiệu mạo danh) + B-rule.
   - Chọn ngưỡng nội bộ tại mục tiêu FPR 1% và 5%.
   - Grouped 5-fold CV lặp 3 seed (17, 42, 2026), tính khoảng tin cậy Bootstrap 95%.
8. Tiêu chuẩn mã nguồn:
   - Python 3.10+, Type hints đầy đủ, docstrings rõ ràng, kiểm thử đơn vị (pytest).
   - Code tái lập được (reproducible), tham số cấu hình tách biệt.
""".strip()

SYSTEM_PROMPT_DEEPSEEK = f"""
Bạn là Chuyên gia Cấp cao về An toàn Thông tin và Kỹ sư Học máy (Senior ML Security Engineer).
Bạn đang cộng tác cùng Antigravity (Orchestrator) trong dự án NCKH của nhóm bạn Tuấn (Anhtuann1404).

NHIỆM VỤ CỦA BẠN:
- Với chế độ BRAINSTORM (Reasoning): Phân tích logic sâu, thiết kế thuật toán, đề xuất kiến trúc đặc trưng, chứng minh tính chặt chẽ học thuật.
- Với chế độ CODING (Implementation): Sinh code Python chuẩn mực, tối ưu, có type hints, xử lý ngoại lệ, tuân thủ 100% các nguyên tắc bên dưới.

{PROJECT_INVARIANTS}
""".strip()

def compress_task_context(
    task: str,
    file_paths: Optional[List[str]] = None,
    max_lines_per_file: int = 150
) -> str:
    """Nén ngữ cảnh tác vụ và các file liên quan thành một prompt súc tích."""
    context_parts = [
        f"### YÊU CẦU TÁC VỤ:\n{task}\n"
    ]
    
    if file_paths:
        context_parts.append("### NGỮ CẢNH CÁC FILE LIÊN QUAN:")
        for fp in file_paths:
            path = Path(fp)
            if not path.is_file():
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                total_lines = len(lines)
                if total_lines > max_lines_per_file:
                    truncated = lines[:max_lines_per_file]
                    content = "".join(truncated) + f"\n... [Đã nén: hiển thị {max_lines_per_file}/{total_lines} dòng] ...\n"
                else:
                    content = "".join(lines)
                context_parts.append(f"\n--- File: {path.name} ---\n{content}")
            except Exception as e:
                context_parts.append(f"\n--- File: {path.name} (Lỗi đọc: {e}) ---")

    return "\n\n".join(context_parts)
