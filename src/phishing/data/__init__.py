"""Module data: Quản lý nạp dữ liệu, kiểm tra tính toàn vẹn (SHA-256), chuẩn hóa URL và eTLD+1."""

from typing import Dict, Any

__all__ = ["verify_sha256"]


def verify_sha256(file_path: str, expected_hash: str) -> bool:
    """Xác thực mã băm SHA-256 của một file dữ liệu."""
    import hashlib
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest().lower() == expected_hash.lower()
