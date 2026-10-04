"""Module quản lý và kiểm tra mẫu bị loại trừ (Exclusion Registry Filter) theo Anti-Leakage Protocol.

Bảo vệ tính toàn vẹn của tập huấn luyện, xác thực và kiểm thử (train/val/test).
Bất kỳ mẫu nào thuộc danh mục pilot, kiểm tra sơ bộ hoặc bị đánh dấu loại trừ
đều bị chặn hoàn toàn khỏi pipeline thực nghiệm chính.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# parents[3] là thư mục gốc dự án NCKH_2:
# exclusion.py -> data -> phishing -> src -> NCKH_2
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "data" / "exclusion_registry.json"


def compute_sample_fingerprint_hash(sample: Dict[str, Any]) -> str:
    """Tính mã băm nội dung ổn định (stable content hash) từ các trường đặc trưng của mẫu."""
    canonical = json.dumps(
        {
            "pilot_row_idx": sample.get("pilot_row_idx", sample.get("row_idx")),
            "label": sample.get("label"),
            "lang": sample.get("lang"),
            "html_chars": sample.get("html_chars"),
            "text_chars": sample.get("text_chars"),
            "forms": sample.get("forms"),
            "inputs": sample.get("inputs"),
            "password_inputs": sample.get("password_inputs"),
        },
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ExclusionRegistry:
    """Bộ nạp và kiểm tra các điều kiện loại trừ từ exclusion_registry.json.

    Quy chuẩn ARS bắt buộc:
    1. Đường dẫn mặc định phải trỏ chính xác về thư mục data/ của dự án.
    2. Nếu không tìm thấy file registry, ném lỗi FileNotFoundError ngay lập tức, không âm thầm bỏ qua.
    3. Chặn hoàn toàn huấn luyện chính (assert_training_allowed) chừng nào ánh xạ pilot còn unresolved.
    """

    def __init__(self, registry_path: Path | str | None = None) -> None:
        self.path = Path(registry_path) if registry_path else DEFAULT_REGISTRY_PATH
        self._excluded_batches: Set[str] = set()
        self._sample_hashes: Set[str] = set()
        self._sample_fingerprints: Set[Tuple[Any, ...]] = set()
        self.training_blocked: bool = True
        self.training_block_reason: str = ""
        self._load_registry()

    def _load_registry(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(
                f"LỖI TOÀN VẸN DỮ LIỆU: Không tìm thấy tệp exclusion registry tại '{self.path}'. "
                f"Anti-leakage protocol bắt buộc phải có tệp registry để bảo vệ dữ liệu."
            )

        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.training_blocked = data.get("training_blocked", True)
        self.training_block_reason = data.get(
            "training_block_reason",
            "Pilot mapping remains unresolved. Main model training is strictly blocked.",
        )

        for excl in data.get("exclusions", []):
            batch_sha = excl.get("batch_sha256")
            if batch_sha:
                self._excluded_batches.add(batch_sha)
            for sample in excl.get("samples", []):
                # Lưu hash nội dung ổn định
                s_hash = sample.get("sample_content_hash")
                if s_hash:
                    self._sample_hashes.add(s_hash)
                else:
                    self._sample_hashes.add(compute_sample_fingerprint_hash(sample))

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

        if not self._sample_fingerprints and not self._sample_hashes:
            raise ValueError(
                f"LỖI CẤU TRÚC: Exclusion registry tại '{self.path}' không chứa bất kỳ mẫu loại trừ nào."
            )

    def is_excluded(self, sample: Dict[str, Any]) -> bool:
        """Kiểm tra xem mẫu có thuộc danh mục loại trừ hay không."""
        # 1. Kiểm tra trực tiếp theo sample_content_hash đã khai báo
        s_hash = sample.get("sample_content_hash")
        if s_hash and s_hash in self._sample_hashes:
            return True

        # 2. Tính hash nội dung động từ thông tin mẫu
        computed_hash = compute_sample_fingerprint_hash(sample)
        if computed_hash in self._sample_hashes:
            return True

        # 3. Kiểm tra mã băm lô
        batch_id = sample.get("batch_sha256") or sample.get("pilot_sha256")
        if batch_id and batch_id in self._excluded_batches:
            return True

        # 4. Kiểm tra theo ID mẫu loại trừ hoặc cờ pilot
        if sample.get("exclusion_id") or sample.get("is_pilot"):
            return True

        # 5. Kiểm tra theo fingerprint cấu trúc
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

    def assert_training_allowed(self) -> None:
        """Ném lỗi RuntimeError chặn huấn luyện mô hình chính nếu ánh xạ pilot chưa được giải quyết."""
        if self.training_blocked:
            raise RuntimeError(
                f"LỆNH CHẶN HUẤN LUYỆN CHÍNH (Anti-Leakage Protocol): {self.training_block_reason}"
            )
