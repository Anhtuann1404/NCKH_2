"""Module quản lý và kiểm tra mẫu bị loại trừ (Exclusion Registry Filter) theo Anti-Leakage Protocol.

Bảo vệ tính toàn vẹn của tập huấn luyện, xác thực và kiểm thử (train/val/test).
Bất kỳ mẫu nào thuộc danh mục pilot, kiểm tra sơ bộ hoặc bị đánh dấu loại trừ
đều bị chặn hoàn toàn khỏi pipeline thực nghiệm chính.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "data" / "exclusion_registry.json"


class ExclusionRegistry:
    """Bộ nạp và kiểm tra các điều kiện loại trừ từ exclusion_registry.json."""

    def __init__(self, registry_path: Path | str | None = None) -> None:
        self.path = Path(registry_path) if registry_path else DEFAULT_REGISTRY_PATH
        self._excluded_batches: set[str] = set()
        self._sample_fingerprints: set[Tuple[Any, ...]] = set()
        self._load_registry()

    def _load_registry(self) -> None:
        if not self.path.exists():
            return
        data = json.loads(self.path.read_text(encoding="utf-8"))
        for excl in data.get("exclusions", []):
            batch_sha = excl.get("batch_sha256")
            if batch_sha:
                self._excluded_batches.add(batch_sha)
            for sample in excl.get("samples", []):
                # Lưu fingerprint đặc trưng cấu trúc của mẫu pilot
                fp = (
                    sample.get("label"),
                    sample.get("lang"),
                    sample.get("html_chars"),
                    sample.get("text_chars"),
                    sample.get("forms"),
                    sample.get("inputs"),
                    sample.get("password_inputs"),
                )
                self._sample_fingerprints.add(fp)

    def is_excluded(self, sample: Dict[str, Any]) -> bool:
        """Kiểm tra xem mẫu có thuộc danh mục loại trừ hay không."""
        # 1. Kiểm tra mã băm lô nếu mẫu có mang thông tin lô
        batch_id = sample.get("batch_sha256") or sample.get("pilot_sha256")
        if batch_id and batch_id in self._excluded_batches:
            return True

        # 2. Kiểm tra theo ID mẫu loại trừ
        if sample.get("exclusion_id") or sample.get("is_pilot"):
            return True

        # 3. Kiểm tra theo fingerprint cấu trúc
        fp = (
            sample.get("label"),
            sample.get("lang"),
            sample.get("html_chars"),
            sample.get("text_chars"),
            sample.get("forms"),
            sample.get("inputs"),
            sample.get("password_inputs"),
        )
        if fp in self._sample_fingerprints:
            return True

        return False

    def filter_split(self, samples: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Tách danh sách mẫu thành 2 tập: tập giữ lại (kept) và tập bị loại (excluded)."""
        kept = []
        excluded = []
        for s in samples:
            if self.is_excluded(s):
                excluded.append(s)
            else:
                kept.append(s)
        return kept, excluded

    def assert_no_leakage(self, split_name: str, samples: List[Dict[str, Any]]) -> None:
        """Ném lỗi ValueError nếu phát hiện mẫu bị loại trừ lọt vào tập train/val/test."""
        leaked = [s for s in samples if self.is_excluded(s)]
        if leaked:
            raise ValueError(
                f"RÒ RỈ DỮ LIỆU PHÁT HIỆN: Có {len(leaked)} mẫu thuộc exclusion registry "
                f"xuất hiện trong tập '{split_name}'!"
            )
