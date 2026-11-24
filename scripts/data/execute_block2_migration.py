"""Công cụ thực thi và kiểm định di trú Block 2 vào Sổ cái Quản lý Lô (Block 2 Migration Executor).

Tuân thủ nghiêm ngặt chỉ đạo của Lead D:
1. Thực thi theo các lệnh con (subcommands): precheck, apply, verify, invariance-check.
2. Tự kiểm tra toàn diện đầu vào ngay trong bước ghi (apply) trước khi gọi append_event.
3. Hậu kiểm (verify) bắt buộc có bản sao lưu hợp lệ (8.253 bytes, hash 11acdaf1...); fail-closed nếu thiếu backup.
4. Đối chiếu toàn diện 100% hai sự kiện lịch sử (Block 0 & Block 1) so với bản sao lưu.
5. Sử dụng biến trung gian khi tạo thông báo lỗi, tránh lỗi cú pháp escape nháy trong chuỗi.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Thiết lập đường dẫn import
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

from phishing.data.lot_ledger import LotManagementLedger

# Hằng số mật mã và thông số đã khóa
EXPECTED_LEDGER_HASH = "11acdaf1806a80181006a5817520f21b2660c1a13ac983651e4d7129390a15c5"
EXPECTED_LEDGER_SIZE = 8253
EXPECTED_PROPOSAL_HASH = "643373177cbb8caac892abd7318358f631f4adf57f0f13595c8d7a171597881a"
EXPECTED_PROPOSAL_SIZE = 8847
EXPECTED_BLOCK1_HASH = "675440ba606a56a117494ac979f842d0881104639b7fa8dee771aa85680dd6ba"
EXPECTED_COHORT_SEED_COMMITMENT = "a16ce46f0a55db8ca8c6622b8d6dddcae134e1ca0ccef0104345f5369f8d0fc1"
EXPECTED_SEED_COMMITMENT = "4a5338c74bba9ae857fb9fa16a55cc54cae3c21cf779eb55f87996e6a5b7c4b6"
EXPECTED_EVENT_TYPE = "MIGRATE_MAIN_BATCH1_SUPERSEDE_SALT_AND_LINEAGE_ENRICHMENT"
EXPECTED_ACTOR = "Member C (Nguyễn Thắng)"
EXPECTED_LOT_ID = "main_lot_batch_001"
EXPECTED_STATUS = "RESERVED"


def compute_sha256(data: bytes) -> str:
    """Tính mã băm SHA-256 từ mảng bytes."""
    return hashlib.sha256(data).hexdigest()


def check_file_integrity(path: Path, expected_size: int, expected_hash: str, label: str) -> bytes:
    """Kiểm tra sự tồn tại, dung lượng và mã băm của tệp."""
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy tệp {label} tại: {path}")
    raw = path.read_bytes()
    actual_size = len(raw)
    if actual_size != expected_size:
        raise ValueError(
            f"Dung lượng tệp {label} không đúng! Kỳ vọng: {expected_size} bytes, thực tế: {actual_size} bytes"
        )
    actual_hash = compute_sha256(raw)
    if actual_hash != expected_hash:
        raise ValueError(
            f"SHA-256 tệp {label} không khớp! Kỳ vọng: {expected_hash}, thực tế: {actual_hash}"
        )
    return raw


def validate_proposal_payload(proposal_data: Dict[str, Any]) -> None:
    """Kiểm tra tính hợp lệ của cấu trúc proposal snapshot."""
    actual_lot = proposal_data.get("lot_id")
    if actual_lot != EXPECTED_LOT_ID:
        raise ValueError(f"Proposal không đúng lot_id! Kỳ vọng: {EXPECTED_LOT_ID}, thực tế: {actual_lot}")

    actual_type = proposal_data.get("event_type")
    if actual_type != EXPECTED_EVENT_TYPE:
        raise ValueError(f"Proposal không đúng event_type! Kỳ vọng: {EXPECTED_EVENT_TYPE}, thực tế: {actual_type}")

    actual_actor = proposal_data.get("actor")
    if actual_actor != EXPECTED_ACTOR:
        raise ValueError(f"Proposal không đúng actor! Kỳ vọng: {EXPECTED_ACTOR}, thực tế: {actual_actor}")

    actual_status = proposal_data.get("status")
    if actual_status != EXPECTED_STATUS:
        raise ValueError(f"Proposal không đúng status! Kỳ vọng: {EXPECTED_STATUS}, thực tế: {actual_status}")

    details = proposal_data.get("details")
    if not isinstance(details, dict):
        raise ValueError("Proposal thiếu trường details hợp lệ!")

    allocated = details.get("allocated_candidate_ids", [])
    if len(allocated) != 100:
        raise ValueError(f"Proposal details allocated_candidate_ids không đủ 100 mẫu (thực tế: {len(allocated)})")

    b_subset = details.get("b_subset_candidate_ids", [])
    if len(b_subset) != 30:
        raise ValueError(f"Proposal details b_subset_candidate_ids không đủ 30 mẫu (thực tế: {len(b_subset)})")

    b_indices = details.get("b_indices_in_lot100", [])
    if len(b_indices) != 30:
        raise ValueError(f"Proposal details b_indices_in_lot100 không đủ 30 chỉ số (thực tế: {len(b_indices)})")


def cmd_precheck(ledger_path: Path, proposal_path: Path) -> None:
    """Thực thi tiền kiểm độc lập (Pre-check)."""
    print("=" * 70)
    print("=== [TIỀN KIỂM] KIỂM TRA ĐIỀU KIỆN TIÊN QUYẾT DI TRÚ BLOCK 2 ===")
    print("=" * 70)
    print(f"Sổ cái kiểm tra:  {ledger_path}")
    print(f"Proposal kiểm tra: {proposal_path}")

    # 1. Kiểm tra toàn vẹn sổ cái 2 block
    raw_ledger = check_file_integrity(ledger_path, EXPECTED_LEDGER_SIZE, EXPECTED_LEDGER_HASH, "sổ cái 2 block")
    ledger = LotManagementLedger(ledger_path)
    if len(ledger.events) != 2:
        raise ValueError(f"Sổ cái phải có đúng 2 sự kiện lịch sử! Thực tế có: {len(ledger.events)}")

    b0, b1 = ledger.events[0], ledger.events[1]
    if b0.seq != 0 or b0.event_type != "LEDGER_INITIALIZED" or b0.event_id != "GENESIS":
        raise ValueError(f"Block 0 sai cấu trúc: seq={b0.seq}, type={b0.event_type}, id={b0.event_id}")
    if b1.seq != 1 or b1.event_type != "REGISTER_MAIN_BATCH1_SAMPLES":
        raise ValueError(f"Block 1 sai cấu trúc: seq={b1.seq}, type={b1.event_type}")
    if b1.event_hash != EXPECTED_BLOCK1_HASH:
        raise ValueError(f"Block 1 event_hash sai lệch: {b1.event_hash} != {EXPECTED_BLOCK1_HASH}")

    # 2. Kiểm tra toàn vẹn proposal snapshot
    raw_prop = check_file_integrity(proposal_path, EXPECTED_PROPOSAL_SIZE, EXPECTED_PROPOSAL_HASH, "proposal snapshot")
    proposal_data = json.loads(raw_prop.decode("utf-8"))
    validate_proposal_payload(proposal_data)

    print("✅ [PRECHECK PASS] Tiền kiểm thành công 100%: Sổ cái 2 block và Proposal hoàn toàn hợp lệ.")


def cmd_apply(ledger_path: Path, proposal_path: Path, backup_path: Path) -> None:
    """Thực thi nối Block 2 (Apply) có tự kiểm tra lại toàn bộ đầu vào."""
    print("=" * 70)
    print("=== [THỰC THI] TỰ KIỂM ĐẦU VÀO & NỐI BLOCK 2 VÀO SỔ CÁI ===")
    print("=" * 70)
    print(f"Sổ cái đích:     {ledger_path}")
    print(f"Proposal nguồn:   {proposal_path}")
    print(f"Bản sao lưu:      {backup_path}")

    # YÊU CẦU 3 CỦA LEAD D: Tự kiểm lại đầu vào ngay trong bước ghi
    # 1. Kiểm tra đường dẫn rõ ràng và tệp tồn tại
    if not ledger_path.exists():
        raise FileNotFoundError(f"LỖI TIỀN KIỂM TRƯỚC GHI: Không tìm thấy sổ cái tại: {ledger_path}")
    if not backup_path.exists():
        raise FileNotFoundError(f"LỖI TIỀN KIỂM TRƯỚC GHI: Không tìm thấy bản sao lưu tại: {backup_path}")
    if not proposal_path.exists():
        raise FileNotFoundError(f"LỖI TIỀN KIỂM TRƯỚC GHI: Không tìm thấy proposal tại: {proposal_path}")

    # 2. Kiểm tra sổ cái và backup CÙNG khớp dung lượng và hash 2 block đã khóa
    raw_ledger = check_file_integrity(ledger_path, EXPECTED_LEDGER_SIZE, EXPECTED_LEDGER_HASH, "sổ cái trước ghi")
    raw_backup = check_file_integrity(backup_path, EXPECTED_LEDGER_SIZE, EXPECTED_LEDGER_HASH, "bản sao lưu")

    # 3. Kiểm tra proposal khớp kích thước và hash
    raw_prop = check_file_integrity(proposal_path, EXPECTED_PROPOSAL_SIZE, EXPECTED_PROPOSAL_HASH, "proposal snapshot")
    proposal_data = json.loads(raw_prop.decode("utf-8"))
    validate_proposal_payload(proposal_data)

    # 4. Kiểm tra sổ cái có đúng 2 sự kiện lịch sử hợp lệ
    ledger = LotManagementLedger(ledger_path)
    if len(ledger.events) != 2:
        raise ValueError(f"LỖI TIỀN KIỂM TRƯỚC GHI: Sổ cái có số sự kiện != 2 ({len(ledger.events)})")
    b0, b1 = ledger.events[0], ledger.events[1]
    if b0.seq != 0 or b0.event_type != "LEDGER_INITIALIZED" or b0.event_id != "GENESIS":
        raise ValueError("LỖI TIỀN KIỂM TRƯỚC GHI: Block 0 không hợp lệ")
    if b1.seq != 1 or b1.event_type != "REGISTER_MAIN_BATCH1_SAMPLES" or b1.event_hash != EXPECTED_BLOCK1_HASH:
        raise ValueError("LỖI TIỀN KIỂM TRƯỚC GHI: Block 1 không hợp lệ")

    print("✅ Đã vượt qua toàn bộ các kiểm tra đầu vào trước ghi. Tiến hành nối Block 2...")

    # 5. Thực hiện ghi Block 2 (Append-Only)
    ev2 = ledger.append_event(
        event_type=proposal_data["event_type"],
        actor=proposal_data["actor"],
        lot_id=proposal_data["lot_id"],
        status=proposal_data["status"],
        details=proposal_data["details"],
    )

    new_bytes = ledger_path.read_bytes()
    new_hash = compute_sha256(new_bytes)

    print("✅ [APPLY PASS] Đã nối Block 2 thành công:")
    print(f"   Seq:        {ev2.seq}")
    print(f"   Event ID:   {ev2.event_id}")
    print(f"   Event Type: {ev2.event_type}")
    print(f"   Prev Hash:  {ev2.prev_hash}")
    print(f"   Event Hash: {ev2.event_hash}")
    print(f"   Timestamp:  {ev2.timestamp}")
    print(f"   Sổ cái mới trên đĩa: {len(new_bytes)} bytes | SHA-256: {new_hash}")


def cmd_verify(ledger_path: Path, proposal_path: Path, backup_path: Optional[Path]) -> None:
    """Thực thi hậu kiểm toàn diện (Post-verification) - Bắt buộc có backup hợp lệ."""
    print("=" * 70)
    print("=== [HẬU KIỂM] KIỂM TRA TOÀN DIỆN SỔ CÁI 3 BLOCK VÀ ĐỐI SOÁT SAO LƯU ===")
    print("=" * 70)
    print(f"Sổ cái kiểm tra:  {ledger_path}")
    print(f"Proposal đối soát: {proposal_path}")
    print(f"Bản sao lưu:      {backup_path}")

    # YÊU CẦU 2 CỦA LEAD D: Bắt buộc có bản sao lưu hợp lệ, fail-closed nếu thiếu
    if backup_path is None or str(backup_path).strip() == "":
        raise ValueError("LỖI HẬU KIỂM NGHIÊM TRỌNG: Thiếu đường dẫn BACKUP_PATH! Bắt buộc phải có backup để đối chiếu.")
    if not backup_path.exists():
        raise FileNotFoundError(f"LỖI HẬU KIỂM NGHIÊM TRỌNG: Tệp sao lưu không tồn tại tại: {backup_path}")

    raw_backup = check_file_integrity(backup_path, EXPECTED_LEDGER_SIZE, EXPECTED_LEDGER_HASH, "bản sao lưu đối soát")
    backup_ledger = LotManagementLedger(backup_path)
    if len(backup_ledger.events) != 2:
        raise ValueError(
            f"LỖI HẬU KIỂM NGHIÊM TRỌNG: Bản sao lưu không tải được thành sổ cái 2 sự kiện hợp lệ (thực tế: {len(backup_ledger.events)})"
        )

    # 1. Tải lại độc lập sổ cái từ đĩa và xác thực sequence / cryptographic hash chain
    if not ledger_path.exists():
        raise FileNotFoundError(f"Không tìm thấy sổ cái tại: {ledger_path}")
    ledger = LotManagementLedger(ledger_path)
    if len(ledger.events) != 3:
        raise ValueError(f"Số lượng block không đúng! Kỳ vọng: 3, thực tế: {len(ledger.events)}")

    b0, b1, b2 = ledger.events[0], ledger.events[1], ledger.events[2]

    # 2. Đối chiếu toàn vẹn 2 sự kiện lịch sử so với bản sao lưu
    bk0, bk1 = backup_ledger.events[0], backup_ledger.events[1]
    fields_to_compare = [
        "seq", "event_id", "timestamp", "event_type", "actor",
        "lot_id", "status", "details", "prev_hash", "event_hash"
    ]
    for f in fields_to_compare:
        v0, v_bk0 = getattr(b0, f), getattr(bk0, f)
        if v0 != v_bk0:
            raise ValueError(f"Block 0 bị sai khác trường '{f}' so với bản sao lưu! ({v0} != {v_bk0})")
        v1, v_bk1 = getattr(b1, f), getattr(bk1, f)
        if v1 != v_bk1:
            raise ValueError(f"Block 1 bị sai khác trường '{f}' so với bản sao lưu! ({v1} != {v_bk1})")

    print("✅ Hai sự kiện lịch sử (Block 0 & Block 1) được bảo toàn nguyên vẹn 100% so với bản sao lưu.")

    # 3. Kiểm tra chi tiết Block 0 & Block 1
    if b0.seq != 0 or b0.event_type != "LEDGER_INITIALIZED" or b0.event_id != "GENESIS":
        raise ValueError("Sai lệch cấu trúc Block 0")
    if b1.seq != 1 or b1.event_type != "REGISTER_MAIN_BATCH1_SAMPLES":
        raise ValueError("Sai lệch cấu trúc Block 1")
    if b1.event_hash != EXPECTED_BLOCK1_HASH:
        raise ValueError(f"Mã băm Block 1 bị sai lệch: {b1.event_hash} != {EXPECTED_BLOCK1_HASH}")

    # 4. Kiểm tra chi tiết Block 2
    raw_prop = check_file_integrity(proposal_path, EXPECTED_PROPOSAL_SIZE, EXPECTED_PROPOSAL_HASH, "proposal snapshot")
    proposal_data = json.loads(raw_prop.decode("utf-8"))
    validate_proposal_payload(proposal_data)

    if b2.seq != 2:
        raise ValueError(f"Block 2 seq sai: {b2.seq}")
    if b2.prev_hash != b1.event_hash:
        raise ValueError(f"Block 2 prev_hash không trỏ tới Block 1: {b2.prev_hash} != {b1.event_hash}")
    if b2.event_type != EXPECTED_EVENT_TYPE:
        raise ValueError(f"Block 2 event_type sai: {b2.event_type} != {EXPECTED_EVENT_TYPE}")
    if b2.actor != EXPECTED_ACTOR:
        raise ValueError(f"Block 2 actor sai: {b2.actor} != {EXPECTED_ACTOR}")
    if b2.lot_id != EXPECTED_LOT_ID:
        raise ValueError(f"Block 2 lot_id sai: {b2.lot_id} != {EXPECTED_LOT_ID}")
    if b2.status != EXPECTED_STATUS:
        raise ValueError(f"Block 2 status sai: {b2.status} != {EXPECTED_STATUS}")
    if b2.details != proposal_data["details"]:
        raise ValueError("Block 2 details không khớp 100% với proposal snapshot!")

    # 5. Kiểm tra Active Lot Details
    active = ledger.get_active_lot_details(EXPECTED_LOT_ID)
    if active is None:
        raise ValueError(f"Không lấy được active state cho {EXPECTED_LOT_ID}!")

    prop_details = proposal_data["details"]
    if active.get("allocated_candidate_ids") != prop_details.get("allocated_candidate_ids"):
        raise ValueError("Danh sách/thứ tự 100 candidate IDs trong active state không khớp proposal!")
    if active.get("b_subset_candidate_ids") != prop_details.get("b_subset_candidate_ids"):
        raise ValueError("Danh sách/thứ tự 30 B subset IDs trong active state không khớp proposal!")
    if active.get("b_indices_in_lot100") != prop_details.get("b_indices_in_lot100"):
        raise ValueError("Danh sách/thứ tự 30 chỉ số B trong active state không khớp proposal!")

    # YÊU CẦU 1 CỦA LEAD D: Sử dụng biến trung gian khi kiểm tra và in thông báo lỗi
    actual_cohort_commit = active.get("cohort_seed_commitment")
    actual_seed_commit = active.get("seed_commitment")

    if actual_cohort_commit != EXPECTED_COHORT_SEED_COMMITMENT:
        raise ValueError(
            f"cohort_seed_commitment sai lệch! Kỳ vọng: {EXPECTED_COHORT_SEED_COMMITMENT}, thực tế: {actual_cohort_commit}"
        )
    if actual_seed_commit != EXPECTED_SEED_COMMITMENT:
        raise ValueError(
            f"seed_commitment sai lệch! Kỳ vọng: {EXPECTED_SEED_COMMITMENT}, thực tế: {actual_seed_commit}"
        )
    if actual_cohort_commit == actual_seed_commit:
        raise ValueError("cohort_seed_commitment không được phép trùng seed_commitment!")

    new_bytes = ledger_path.read_bytes()
    new_sha = compute_sha256(new_bytes)

    print("✅ [VERIFY PASS] Hậu kiểm thành công 100%: Sổ cái 3 block hoàn toàn hợp lệ.")
    print(f"   Dung lượng sổ cái 3 block: {len(new_bytes)} bytes | SHA-256: {new_sha}")
    print(f"   Block 2 event_id:   {b2.event_id}")
    print(f"   Block 2 timestamp:  {b2.timestamp}")
    print(f"   Block 2 event_hash: {b2.event_hash}")


def cmd_invariance_check(ledger_path: Path) -> None:
    """Kiểm tra tính bất biến khi đọc (Read-Only Invariance Check)."""
    print("=" * 70)
    print("=== [KIỂM TRA BẤT BIẾN] KIỂM TRA THAO TÁC ĐỌC KHÔNG THAY ĐỔI SỔ CÁI ===")
    print("=" * 70)
    print(f"Sổ cái kiểm tra: {ledger_path}")

    if not ledger_path.exists():
        raise FileNotFoundError(f"Không tìm thấy sổ cái tại: {ledger_path}")

    raw_before = ledger_path.read_bytes()
    h_before = compute_sha256(raw_before)

    ledger = LotManagementLedger(ledger_path)
    active = ledger.get_active_lot_details(EXPECTED_LOT_ID)
    if active is None:
        raise ValueError(f"Không lấy được active state cho {EXPECTED_LOT_ID}")

    ledger_reloaded = LotManagementLedger(ledger_path)
    raw_after = ledger_path.read_bytes()
    h_after = compute_sha256(raw_after)

    if len(ledger_reloaded.events) != 3:
        raise ValueError(f"Số block bị biến động khi đọc! Thực tế: {len(ledger_reloaded.events)}")
    if h_before != h_after or len(raw_before) != len(raw_after):
        raise ValueError("Tệp sổ cái bị thay đổi nội dung khi thực hiện thao tác đọc!")

    print("✅ [INVARIANCE PASS] Xác nhận tính bất biến khi đọc: 0 block phát sinh, 0 byte thay đổi.")
    print(f"   SHA-256 sổ cái trước và sau khi đọc: {h_after}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Công cụ thực thi và kiểm định di trú Block 2 vào Sổ cái Quản lý Lô."
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Subcommand: precheck
    p_pre = subparsers.add_parser("precheck", help="Kiểm tra điều kiện tiên quyết trước khi sao lưu")
    p_pre.add_argument(
        "--ledger-path",
        type=Path,
        default=Path(os.environ.get("LEDGER_PATH", "data/restricted/main_annotation_lot_management_ledger.json")),
        help="Đường dẫn tệp sổ cái (mặc định lấy từ LEDGER_PATH hoặc data/restricted/...)",
    )
    p_pre.add_argument(
        "--proposal-path",
        type=Path,
        default=Path(os.environ.get("PROPOSAL_PATH", "data/restricted/main_batch1_staging_v4_2/proposal_block2_active_state_snapshot.json")),
        help="Đường dẫn proposal snapshot",
    )

    # Subcommand: apply
    p_apply = subparsers.add_parser("apply", help="Tự kiểm đầu vào và thực thi nối Block 2")
    p_apply.add_argument(
        "--ledger-path",
        type=Path,
        default=Path(os.environ.get("LEDGER_PATH", "data/restricted/main_annotation_lot_management_ledger.json")),
        help="Đường dẫn tệp sổ cái đích",
    )
    p_apply.add_argument(
        "--proposal-path",
        type=Path,
        default=Path(os.environ.get("PROPOSAL_PATH", "data/restricted/main_batch1_staging_v4_2/proposal_block2_active_state_snapshot.json")),
        help="Đường dẫn proposal snapshot",
    )
    p_apply.add_argument(
        "--backup-path",
        type=Path,
        default=Path(os.environ.get("BACKUP_PATH", "")),
        help="Đường dẫn bản sao lưu bắt buộc phải có",
    )

    # Subcommand: verify
    p_verify = subparsers.add_parser("verify", help="Hậu kiểm toàn diện 3 block và đối soát bản sao lưu")
    p_verify.add_argument(
        "--ledger-path",
        type=Path,
        default=Path(os.environ.get("LEDGER_PATH", "data/restricted/main_annotation_lot_management_ledger.json")),
        help="Đường dẫn tệp sổ cái cần kiểm",
    )
    p_verify.add_argument(
        "--proposal-path",
        type=Path,
        default=Path(os.environ.get("PROPOSAL_PATH", "data/restricted/main_batch1_staging_v4_2/proposal_block2_active_state_snapshot.json")),
        help="Đường dẫn proposal snapshot",
    )
    p_verify.add_argument(
        "--backup-path",
        type=Path,
        default=Path(os.environ.get("BACKUP_PATH", "")),
        help="Đường dẫn bản sao lưu bắt buộc phải có",
    )

    # Subcommand: invariance-check
    p_inv = subparsers.add_parser("invariance-check", help="Kiểm tra tính bất biến khi đọc")
    p_inv.add_argument(
        "--ledger-path",
        type=Path,
        default=Path(os.environ.get("LEDGER_PATH", "data/restricted/main_annotation_lot_management_ledger.json")),
        help="Đường dẫn tệp sổ cái cần kiểm",
    )

    args = parser.parse_args()

    try:
        if args.subcommand == "precheck":
            cmd_precheck(args.ledger_path, args.proposal_path)
        elif args.subcommand == "apply":
            cmd_apply(args.ledger_path, args.proposal_path, args.backup_path)
        elif args.subcommand == "verify":
            cmd_verify(args.ledger_path, args.proposal_path, args.backup_path)
        elif args.subcommand == "invariance-check":
            cmd_invariance_check(args.ledger_path)
    except Exception as exc:
        print(f"\n❌ [ERROR] THAO TÁC THẤT BẠI: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
