"""Kiểm thử hồi quy cho bộ quét bảo vệ Git Isolation Verifier.

Chứng minh:
1. Bộ quét phát hiện chính xác literal vận hành thật nếu xuất hiện ở vị trí test (SEC002 hoặc SEC001).
2. Thông báo vi phạm TUYỆT ĐỐI KHÔNG in lại giá trị bí mật mà che giấu bằng [REDACTED_SECRET].
3. Bộ quét cho phép các fixture test giả lập (synthetic/dummy) hợp lệ chạy qua mà không cảnh báo nhầm (zero false positives).
4. Bộ quét chặn đứng việc gán literal string cho biến salt/secret trong thư mục code (src/, scripts/).
"""

from pathlib import Path
import pytest

from scripts.data.verify_git_isolation import (
    KNOWN_EXPOSED_SALT_LITERAL,
    scan_public_docs_for_leaks,
)


def test_scanner_detects_prohibited_operational_secret_in_test_dir(tmp_path: Path):
    """Chứng minh bộ quét phát hiện literal vận hành thật nếu bị đưa vào file test."""
    test_dir = tmp_path / "tests"
    test_dir.mkdir(parents=True, exist_ok=True)
    leaky_file = test_dir / "test_accidental_leak.py"
    leaky_file.write_text(
        f'def test_dummy():\n    salt = "{KNOWN_EXPOSED_SALT_LITERAL}"\n',
        encoding="utf-8",
    )

    res = scan_public_docs_for_leaks(target_dirs=[test_dir])
    assert res["status"] == "FAIL"
    assert res["leaks_count"] >= 1

    # Kiểm tra bảo vệ thông tin: Thông báo vi phạm không được in chuỗi bí mật thật
    for leak in res["leaks"]:
        assert KNOWN_EXPOSED_SALT_LITERAL not in leak.get("term", "")
        assert "[REDACTED" in leak.get("term", "")


def test_scanner_allows_synthetic_dummy_test_fixtures(tmp_path: Path):
    """Chứng minh bộ quét cho phép các fixture test dùng giá trị giả lập synthetic/dummy."""
    test_dir = tmp_path / "tests"
    test_dir.mkdir(parents=True, exist_ok=True)
    synthetic_file = test_dir / "test_valid_synthetic.py"
    synthetic_file.write_text(
        'def test_synthetic():\n'
        '    SYNTHETIC_DUMMY_SALT = "synthetic_dummy_salt_for_proposal_a_test_only_xyz"\n'
        '    salt = "salt_check"\n'
        '    blind_salt = "seed_test_salt_123"\n',
        encoding="utf-8",
    )

    res = scan_public_docs_for_leaks(target_dirs=[test_dir])
    assert res["status"] == "PASS"
    assert res["leaks_count"] == 0


def test_scanner_blocks_literal_salt_assignment_in_code_dir(tmp_path: Path):
    """Chứng minh bộ quét chặn đứng việc gán literal string cho biến salt trong thư mục code (src/scripts)."""
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    bad_code_file = src_dir / "pipeline_with_hardcoded_salt.py"
    bad_code_file.write_text(
        'def run():\n    blind_salt = "any_unapproved_literal_string"\n',
        encoding="utf-8",
    )

    res = scan_public_docs_for_leaks(target_dirs=[src_dir])
    assert res["status"] == "FAIL"
    assert res["leaks_count"] >= 1
    assert "any_unapproved_literal_string" not in res["leaks"][0]["term"]
    assert "[REDACTED_SECRET]" in res["leaks"][0]["term"]
