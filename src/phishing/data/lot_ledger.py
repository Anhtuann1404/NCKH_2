"""Module quản lý Sổ cái Quản lý Lô mẫu (Lot Management Ledger) dạng Append-Only.

Tuân thủ nghiêm ngặt chuẩn mực ARS và Kỷ luật Ponytail:
1. Khu vực lưu trữ: Lưu tại data/restricted/main_annotation_lot_management_ledger.json.
2. Bảo mật Git: Nằm hoàn toàn trong data/restricted/ (đã được .gitignore cách ly).
3. Append-Only & Hash-Chaining:
   - Mỗi sự kiện ghi nhận tuần tự (seq: 0, 1, 2, ...).
   - Mỗi sự kiện liên kết với sự kiện trước qua `prev_hash` và tính toán `event_hash` (SHA-256).
   - Tuyệt đối không cho phép ghi đè hay chỉnh sửa lịch sử.
4. Quản lý trạng thái vòng đời mẫu:
   - PREPARED (chuẩn bị), RESERVED (giữ chỗ/niêm phong), RELEASED (phát hành), COMPLETED (hoàn tất), REVOKED (thu hồi).
5. Chống chọn trùng giữa các đợt:
   - Quản lý tập candidate_id đã cấp cho Main Batch để loại trừ ở các đợt sau.
   - Tuyệt đối không đưa các mẫu Main vào exclusion_registry.json (vốn chỉ dành riêng cho pilot/hiệu chuẩn).
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


LEDGER_SCHEMA_VERSION = "1.0.0"
DEFAULT_LEDGER_PATH = Path("data/restricted/main_annotation_lot_management_ledger.json")


class LedgerIntegrityError(Exception):
    """Lỗi toàn vẹn dữ liệu trong Sổ cái quản lý lô."""


@dataclass
class LedgerEvent:
    seq: int
    event_id: str
    timestamp: str
    event_type: str
    actor: str
    lot_id: str
    status: str
    details: Dict[str, Any]
    prev_hash: str
    event_hash: str = ""

    def compute_hash(self) -> str:
        canonical_dict = {
            "seq": self.seq,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "actor": self.actor,
            "lot_id": self.lot_id,
            "status": self.status,
            "details": self.details,
            "prev_hash": self.prev_hash,
        }
        canonical_str = json.dumps(canonical_dict, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


class LotManagementLedger:
    """Quản lý Sổ cái Lô Mẫu Main Annotation (Append-only với chuỗi băm bảo vệ toàn vẹn)."""

    def __init__(self, ledger_path: Path | str = DEFAULT_LEDGER_PATH):
        self.ledger_path = Path(ledger_path)
        self.events: List[LedgerEvent] = []
        self._allocated_ids: Set[str] = set()

        if self.ledger_path.exists():
            self._load_and_verify()
        else:
            self._init_new_ledger()

    def _init_new_ledger(self) -> None:
        """Khởi tạo sổ cái mới với sự kiện GENESIS."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        genesis_event = LedgerEvent(
            seq=0,
            event_id="GENESIS",
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="LEDGER_INITIALIZED",
            actor="SYSTEM",
            lot_id="SYSTEM",
            status="PREPARED",
            details={"schema_version": LEDGER_SCHEMA_VERSION, "description": "Genesis block for Main Annotation Ledger"},
            prev_hash="0" * 64,
        )
        genesis_event.event_hash = genesis_event.compute_hash()
        self.events.append(genesis_event)
        self._save_to_disk()

    def _load_and_verify(self) -> None:
        """Đọc và kiểm tra tính toàn vẹn của chuỗi băm sổ cái."""
        data = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        raw_events = data.get("events", [])
        self.events = []
        self._allocated_ids = set()

        for idx, item in enumerate(raw_events):
            event = LedgerEvent(
                seq=item["seq"],
                event_id=item["event_id"],
                timestamp=item["timestamp"],
                event_type=item["event_type"],
                actor=item["actor"],
                lot_id=item["lot_id"],
                status=item["status"],
                details=item["details"],
                prev_hash=item["prev_hash"],
                event_hash=item.get("event_hash", ""),
            )
            # Kiểm tra thứ tự tuần tự
            if event.seq != idx:
                raise LedgerIntegrityError(f"Sai lệch sequence: kỳ vọng {idx}, thực tế {event.seq}")

            # Kiểm tra liên kết hash
            expected_prev = "0" * 64 if idx == 0 else self.events[idx - 1].event_hash
            if event.prev_hash != expected_prev:
                raise LedgerIntegrityError(
                    f"Sai lệch prev_hash tại seq {event.seq}: kỳ vọng {expected_prev}, thực tế {event.prev_hash}"
                )

            # Kiểm tra mã băm bản ghi
            computed = event.compute_hash()
            if event.event_hash != computed:
                raise LedgerIntegrityError(
                    f"Sai lệch event_hash tại seq {event.seq}: ghi nhận {event.event_hash}, tính toán {computed}"
                )

            self.events.append(event)

            # Cập nhật danh sách candidate_ids đã phân bổ
            if "allocated_candidate_ids" in event.details and event.status in ("PREPARED", "RESERVED", "RELEASED", "COMPLETED"):
                for cid in event.details["allocated_candidate_ids"]:
                    self._allocated_ids.add(cid)

    def _save_to_disk(self) -> None:
        """Ghi dữ liệu sổ cái xuống đĩa đảm bảo UTF-8."""
        data = {
            "schema_version": LEDGER_SCHEMA_VERSION,
            "last_updated_utc": datetime.now(timezone.utc).isoformat(),
            "total_events": len(self.events),
            "events": [
                {
                    "seq": e.seq,
                    "event_id": e.event_id,
                    "timestamp": e.timestamp,
                    "event_type": e.event_type,
                    "actor": e.actor,
                    "lot_id": e.lot_id,
                    "status": e.status,
                    "details": e.details,
                    "prev_hash": e.prev_hash,
                    "event_hash": e.event_hash,
                }
                for e in self.events
            ],
        }
        self.ledger_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def append_event(
        self,
        event_type: str,
        actor: str,
        lot_id: str,
        status: str,
        details: Dict[str, Any],
        event_id: Optional[str] = None,
    ) -> LedgerEvent:
        """Thêm sự kiện mới vào sổ cái (Append-Only)."""
        last_event = self.events[-1]
        seq = last_event.seq + 1
        prev_hash = last_event.event_hash
        eid = event_id or hashlib.sha256(f"{seq}:{datetime.now(timezone.utc).isoformat()}:{lot_id}".encode()).hexdigest()[:16]

        event = LedgerEvent(
            seq=seq,
            event_id=eid,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            actor=actor,
            lot_id=lot_id,
            status=status,
            details=details,
            prev_hash=prev_hash,
        )
        event.event_hash = event.compute_hash()
        self.events.append(event)

        # Cập nhật allocated_ids
        if "allocated_candidate_ids" in details and status in ("PREPARED", "RESERVED", "RELEASED", "COMPLETED"):
            for cid in details["allocated_candidate_ids"]:
                self._allocated_ids.add(cid)

        self._save_to_disk()
        return event

    def get_allocated_candidate_ids(self) -> Set[str]:
        """Trả về tập hợp tất cả các candidate_id đã được cấp cho bất kỳ lô nào."""
        return set(self._allocated_ids)

    def is_candidate_allocated(self, candidate_id: str) -> bool:
        """Kiểm tra xem candidate_id đã từng được phân bổ vào lô nào chưa."""
        return candidate_id in self._allocated_ids
