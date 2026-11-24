"""Kiểm thử hồi quy cho tính năng kiểm tra tính độc lập của bản sao lưu trong execute_block2_migration.py.

Tuân thủ nghiêm ngặt chỉ đạo của Lead D:
1. Sử dụng fixture hoàn toàn giả lập (synthetic test data), tuyệt đối KHÔNG chứa bí mật vận hành thật,
   salt, seed, candidate UID hay locator từ tập dữ liệu hạn chế.
2. Kiểm tra các trường hợp:
   - Backup trùng đường dẫn sổ cái -> Bị chặn (ValueError).
   - Backup có đường dẫn tương đối khác nhau nhưng trỏ về cùng một tệp -> Bị chặn (ValueError).
   - Backup là hardlink của sổ cái -> Bị chặn (ValueError).
   - Backup là symlink của sổ cái -> Bị chặn (ValueError) nếu môi trường hỗ trợ symlink.
   - Backup là bản sao độc lập có cùng nội dung -> PASS.
   - Lỗi truy cập/hệ thống khi kiểm tra độc lập -> Fail-closed (OSError).
3. Kiểm tra tích hợp vào cmd_apply:
   - Khi backup là hardlink/samefile, cmd_apply dừng ngay trước khi ghi, giữ nguyên byte và số block của sổ cái.
"""

import os
from pathlib import Path
import sys
from typing import Generator

import pytest

# Thiết lập đường dẫn import
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

from scripts.data.execute_block2_migration import (
    check_file_independence,
    cmd_apply,
)


@pytest.fixture
def synthetic_ledger(tmp_path: Path) -> Path:
    """Tạo tệp ledger giả lập hoàn toàn (synthetic)."""
    ledger_file = tmp_path / "synthetic_ledger.json"
    ledger_file.write_bytes(b"SYNTHETIC_DUMMY_LEDGER_CONTENT_2BLOCKS")
    return ledger_file


def test_same_path_string_blocked(synthetic_ledger: Path):
    """Trường hợp 1A: Backup trùng đường dẫn sổ cái hoàn toàn -> Bị chặn."""
    with pytest.raises(ValueError, match="trỏ tới cùng một tệp vật lý"):
        check_file_independence(synthetic_ledger, synthetic_ledger, "sổ cái", "bản sao lưu")


def test_relative_canonical_same_file_blocked(synthetic_ledger: Path, tmp_path: Path):
    """Trường hợp 1B: Đường dẫn tương đối khác nhau nhưng trỏ về cùng một tệp -> Bị chặn."""
    cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        p1 = Path("synthetic_ledger.json")
        p2 = Path("./synthetic_ledger.json")
        p3 = Path("../") / tmp_path.name / "synthetic_ledger.json"

        with pytest.raises(ValueError, match="trỏ tới cùng một tệp vật lý"):
            check_file_independence(p1, p2, "sổ cái", "bản sao lưu")

        with pytest.raises(ValueError, match="trỏ tới cùng một tệp vật lý"):
            check_file_independence(p1, p3, "sổ cái", "bản sao lưu")
    finally:
        os.chdir(cwd)


def test_hardlink_backup_blocked(synthetic_ledger: Path, tmp_path: Path):
    """Trường hợp 2: Backup là hardlink của sổ cái -> Bị chặn."""
    hardlink_backup = tmp_path / "backup_hardlink.json"
    try:
        os.link(synthetic_ledger, hardlink_backup)
    except OSError as exc:
        pytest.skip(f"Hệ thống tệp không hỗ trợ tạo hardlink: {exc}")

    with pytest.raises(ValueError, match="hardlink hoặc symlink"):
        check_file_independence(synthetic_ledger, hardlink_backup, "sổ cái", "bản sao lưu")


def test_symlink_backup_blocked(synthetic_ledger: Path, tmp_path: Path):
    """Trường hợp 3: Backup là symlink của sổ cái -> Bị chặn."""
    symlink_backup = tmp_path / "backup_symlink.json"
    try:
        os.symlink(synthetic_ledger, symlink_backup)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Môi trường không hỗ trợ hoặc thiếu quyền tạo symlink trên Windows: {exc}")

    with pytest.raises(ValueError, match="trỏ tới cùng một tệp vật lý"):
        check_file_independence(synthetic_ledger, symlink_backup, "sổ cái", "bản sao lưu")


def test_independent_backup_allowed(synthetic_ledger: Path, tmp_path: Path):
    """Trường hợp 4: Backup là tệp bản sao độc lập có cùng nội dung -> PASS."""
    independent_backup = tmp_path / "backup_independent.json"
    independent_backup.write_bytes(synthetic_ledger.read_bytes())

    # Không được ném ngoại lệ
    check_file_independence(synthetic_ledger, independent_backup, "sổ cái", "bản sao lưu")


def test_fail_closed_on_system_error(synthetic_ledger: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Trường hợp 5: Khi os.path.samefile gặp lỗi hệ điều hành/truy cập -> Dừng an toàn (fail-closed, OSError)."""
    independent_backup = tmp_path / "backup_independent.json"
    independent_backup.write_bytes(synthetic_ledger.read_bytes())

    import scripts.data.execute_block2_migration as mig_mod

    def mock_samefile_error(p1, p2):
        raise OSError("Giả lập lỗi I/O hoặc lỗi truy cập metadata hệ thống")

    monkeypatch.setattr(mig_mod.os.path, "samefile", mock_samefile_error)

    with pytest.raises(OSError, match="Không thể xác minh độc lập tệp"):
        check_file_independence(synthetic_ledger, independent_backup, "sổ cái", "bản sao lưu")


def test_apply_fails_closed_when_backup_is_same_file(
    synthetic_ledger: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Trường hợp 6: cmd_apply chặn ngay lập tức nếu backup trùng tệp sổ cái, bảo toàn sổ cái 100%."""
    import hashlib
    import scripts.data.execute_block2_migration as mig_mod

    raw_content = synthetic_ledger.read_bytes()
    initial_hash = hashlib.sha256(raw_content).hexdigest()
    initial_size = len(raw_content)

    dummy_proposal = tmp_path / "dummy_proposal.json"
    dummy_proposal.write_bytes(b'{"dummy": true}')
    prop_hash = hashlib.sha256(dummy_proposal.read_bytes()).hexdigest()

    # Khớp hash giả lập để kiểm tra đúng guard check_file_independence
    monkeypatch.setattr(mig_mod, "EXPECTED_LEDGER_HASH", initial_hash)
    monkeypatch.setattr(mig_mod, "EXPECTED_LEDGER_SIZE", initial_size)
    monkeypatch.setattr(mig_mod, "EXPECTED_PROPOSAL_HASH", prop_hash)
    monkeypatch.setattr(mig_mod, "EXPECTED_PROPOSAL_SIZE", len(dummy_proposal.read_bytes()))

    # Gọi apply với backup chính là synthetic_ledger
    with pytest.raises(ValueError, match="trỏ tới cùng một tệp vật lý"):
        cmd_apply(synthetic_ledger, dummy_proposal, synthetic_ledger)

    # Đảm bảo sổ cái không bị can thiệp
    post_bytes = synthetic_ledger.read_bytes()
    assert len(post_bytes) == initial_size
    assert hashlib.sha256(post_bytes).hexdigest() == initial_hash
