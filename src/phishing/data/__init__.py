"""Module data: Quản lý nạp dữ liệu, kiểm tra tính toàn vẹn (SHA-256), chuẩn hóa URL và eTLD+1."""

from typing import Dict, Any

__all__ = ["verify_sha256"]


def verify_sha256(file_path: str, expected_hash: str, *, normalize_newlines: bool = True) -> bool:
    """Xác thực mã băm SHA-256 của một file dữ liệu.

    Với các tệp cấu hình JSON/văn bản, chuẩn hóa ký tự xuống dòng (LF) để đảm bảo
    mã băm bất biến trên đa nền tảng (Windows CRLF vs Linux/macOS LF).
    """
    import hashlib
    with open(file_path, "rb") as f:
        data = f.read()
    if normalize_newlines and file_path.endswith((".json", ".txt", ".md", ".py")):
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest().lower() == expected_hash.lower()
