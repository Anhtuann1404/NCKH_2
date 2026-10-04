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


def compute_summary_fingerprint_hash(sample: Dict[str, Any]) -> str:
    """Tính mã băm dấu vân tay cấu trúc tóm tắt (summary fingerprint hash) từ các trường thống kê của mẫu pilot.

    LƯU Ý KHOA HỌC: Đây là mã băm từ các siêu dữ liệu cấu trúc (độ dài, số lượng forms/inputs),
    KHÔNG PHẢI mã băm nội dung thô (raw HTML/URL). Khi có bản pilot gốc, cần băm URL/HTML
    theo quy tắc cố định chuẩn hóa để đối chiếu 1-1.
    """
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


# Bí danh tương thích ngược
compute_sample_fingerprint_hash = compute_summary_fingerprint_hash


class ExclusionRegistry:
    """Bộ nạp và kiểm tra các điều kiện loại trừ từ exclusion_registry.json.

    Quy chuẩn ARS bắt buộc:
    1. Đường dẫn mặc định phải trỏ chính xác về thư mục data/ của dự án.
    2. Nếu không tìm thấy file registry, ném lỗi FileNotFoundError ngay lập tức, không âm thầm bỏ qua.
    3. Chặn hoàn toàn huấn luyện chính (assert_training_allowed) chừng nào ánh xạ pilot còn unresolved,
       kiểm tra trực tiếp mapping_status và rows_api_revision_pinned của từng lô, không phụ thuộc vào cờ training_blocked.
    """

    def __init__(self, registry_path: Path | str | None = None) -> None:
        self.path = Path(registry_path) if registry_path else DEFAULT_REGISTRY_PATH
        self._raw_exclusions: List[Dict[str, Any]] = []
        self._excluded_batches: Set[str] = set()
        self._summary_fingerprint_hashes: Set[str] = set()
        self._sample_fingerprints: Set[Tuple[Any, ...]] = set()
        self._url_hashes: Set[str] = set()
        self._html_hashes: Set[str] = set()
        self._group_hashes: Set[str] = set()
        self.training_blocked: bool = True
        self.training_block_reason: str = ""
        self._load_registry()

    @property
    def _sample_hashes(self) -> Set[str]:
        """Thuộc tính tương thích ngược với các kiểm thử cũ."""
        return self._summary_fingerprint_hashes

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

        self._raw_exclusions = data.get("exclusions", [])
        for excl in self._raw_exclusions:
            batch_sha = excl.get("batch_sha256")
            if batch_sha:
                self._excluded_batches.add(batch_sha)
            for sample in excl.get("samples", []):
                for key, destination in (("url_sha256", self._url_hashes), ("html_sha256", self._html_hashes), ("group_sha256", self._group_hashes)):
                    if sample.get(key):
                        destination.add(sample[key])
                # Lưu hash fingerprint cấu trúc tóm tắt
                s_hash = sample.get("summary_fingerprint_hash") or sample.get("sample_content_hash")
                if s_hash:
                    self._summary_fingerprint_hashes.add(s_hash)
                elif "html_chars" in sample:
                    self._summary_fingerprint_hashes.add(compute_summary_fingerprint_hash(sample))

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
                if "html_chars" in sample:
                    self._sample_fingerprints.add(fp)

        if not any((self._sample_fingerprints, self._summary_fingerprint_hashes, self._url_hashes, self._html_hashes, self._group_hashes)):
            raise ValueError(
                f"LỖI CẤU TRÚC: Exclusion registry tại '{self.path}' không chứa bất kỳ mẫu loại trừ nào."
            )

    def is_excluded(self, sample: Dict[str, Any]) -> bool:
        """Kiểm tra xem mẫu có thuộc danh mục loại trừ hay không."""
        url = sample.get("url")
        html = sample.get("html")
        url_hash = sample.get("url_sha256") or (hashlib.sha256(url.encode()).hexdigest() if isinstance(url, str) else None)
        html_hash = sample.get("html_sha256") or (hashlib.sha256(html.encode()).hexdigest() if isinstance(html, str) else None)
        if url_hash in self._url_hashes or html_hash in self._html_hashes:
            return True
        if self._group_hashes and isinstance(url, str):
            import tldextract
            # Offline bundled PSL, including private tenant suffixes; no network.
            extractor = tldextract.TLDExtract(suffix_list_urls=(), include_psl_private_domains=True)
            domain = extractor(url).top_domain_under_public_suffix
            if domain and hashlib.sha256(domain.encode()).hexdigest() in self._group_hashes:
                return True
        if sample.get("group_sha256") in self._group_hashes:
            return True
        # 1. Kiểm tra trực tiếp theo summary_fingerprint_hash (hoặc alias sample_content_hash) đã khai báo
        s_hash = sample.get("summary_fingerprint_hash") or sample.get("sample_content_hash")
        if s_hash and s_hash in self._summary_fingerprint_hashes:
            return True

        # 2. Tính summary fingerprint hash động từ thông tin mẫu
        computed_hash = compute_summary_fingerprint_hash(sample)
        if computed_hash in self._summary_fingerprint_hashes:
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
        """Ném lỗi RuntimeError chặn huấn luyện mô hình chính nếu có bất kỳ lô loại trừ nào chưa giải quyết ánh xạ.

        Cơ chế phòng vệ chiều sâu (Defense-in-depth):
        1. Kiểm tra cờ training_blocked tổng thể.
        2. Duyệt trực tiếp từng lô trong exclusion registry:
           Nếu bất kỳ lô nào có mapping_status != 'resolved' hoặc rows_api_revision_pinned is not True,
           bắt buộc ném lỗi chặn huấn luyện kể cả khi cờ training_blocked bị can thiệp thành False.
        """
        if self.training_blocked:
            raise RuntimeError(
                f"LỆNH CHẶN HUẤN LUYỆN CHÍNH (Anti-Leakage Protocol): {self.training_block_reason}"
            )

        for excl in self._raw_exclusions:
            excl_id = excl.get("exclusion_id", "UNKNOWN")
            mapping_status = excl.get("mapping_status")
            rows_pinned = excl.get("rows_api_revision_pinned", False)

            if mapping_status != "resolved" or not rows_pinned:
                raise RuntimeError(
                    f"LỆNH CHẶN HUẤN LUYỆN CHÍNH (Anti-Leakage Protocol): Lô loại trừ '{excl_id}' "
                    f"có trạng thái mapping='{mapping_status}' (rows_api_revision_pinned={rows_pinned}). "
                    f"Bắt buộc giải quyết ánh xạ 1-1 và có bằng chứng xác minh byte trước khi huấn luyện."
                )
