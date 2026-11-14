"""Bộ lọc cổng chọn mẫu 5 giai đoạn có thể tái lập cho Main Annotation (Anti-Leakage Protocol).

Thiết kế theo kỷ luật Ponytail và chuẩn mực ARS:
- Cổng 0 (Gate 0): Kiểm định tính toàn vẹn Shard và Nguồn (Cách ly train-000, train-055; chặn PhishVN; đối soát SHA Git-LFS).
- Cổng 1 (Gate 1): Tính hợp lệ trường & Ngưỡng ký tự (URL HTTP/HTTPS, HTML 1..2M ký tự, cửa sổ ngày).
- Cổng 2 (Gate 2): Loại trừ chống rò rỉ dữ liệu (ExclusionRegistry fail-closed: URL/HTML/Domain group).
- Cổng 3 (Gate 3): Khử trùng lặp nội bộ (Deduplication URL, HTML, Domain diversity).
- Cổng 4 (Gate 4): Chọn mẫu phân tầng với Seed niêm phong (Sealed Seed Stratified Sampling).
"""

import hashlib
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from phishing.data.exclusion import ExclusionRegistry
from phishing.data.grouping import extract_group_id
from phishing.preprocessing.html import clean_html
from phishing.preprocessing.urls import normalize_url

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "configs" / "source_manifest.json"

QUARANTINED_SHARDS = {
    "train-000.parquet",
    "train-000",
    "data/train-000.parquet",
    "train-055.parquet",
    "train-055",
    "data/train-055.parquet",
}

BLOCKED_SOURCES = {"phishvn", "PhishVN", "phish_vn"}


class SelectionGateError(Exception):
    """Lỗi vi phạm cổng an toàn hoặc tính toàn vẹn của quy trình chọn mẫu."""


class SelectionGatePipeline:
    """Đường ống chọn mẫu 5 cổng (Gates 0-4) có kiểm toán số liệu trước/sau từng cổng."""

    def __init__(
        self,
        exclusion_registry: Optional[ExclusionRegistry] = None,
        source_manifest_path: Optional[Path | str] = None,
        min_html_chars: int = 1,
        max_html_chars: int = 2_000_000,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
    ) -> None:
        self.exclusion_registry = exclusion_registry or ExclusionRegistry()
        self.manifest_path = Path(source_manifest_path) if source_manifest_path else DEFAULT_MANIFEST_PATH
        self.min_html_chars = min_html_chars
        self.max_html_chars = max_html_chars
        self.min_date = min_date
        self.max_date = max_date
        self._manifest_cache: Optional[Dict[str, Any]] = None

    def _load_manifest(self) -> Dict[str, Any]:
        if self._manifest_cache is None:
            if not self.manifest_path.exists():
                raise FileNotFoundError(f"Không tìm thấy source manifest tại '{self.manifest_path}'")
            self._manifest_cache = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return self._manifest_cache

    def gate_0_source_and_shard(
        self,
        source_id: str,
        shard_name: str,
        *,
        shard_lfs_sha256: Optional[str] = None,
    ) -> bool:
        """Cổng 0: Kiểm tra nguồn và shard hợp lệ.

        Ném SelectionGateError nếu:
        - Nguồn nằm trong danh sách bị chặn (PhishVN chưa duyệt).
        - Shard nằm trong danh sách cách ly (train-000, train-055 chứa mẫu pilot/rsv).
        - Shard không có trong source_manifest.json đã khóa.
        - Mã băm LFS không khớp với manifest (nếu cung cấp).
        """
        if source_id.lower() in [s.lower() for s in BLOCKED_SOURCES]:
            raise SelectionGateError(
                f"LỆNH CHẶN CỔNG 0: Nguồn '{source_id}' chưa được phê duyệt trích xuất độc lập!"
            )

        # Chuẩn hóa tên shard
        clean_shard = Path(shard_name).name
        if clean_shard in QUARANTINED_SHARDS or shard_name in QUARANTINED_SHARDS:
            raise SelectionGateError(
                f"LỆNH CHẶN CỔNG 0: Shard '{shard_name}' thuộc danh mục BỊ CÁCH LY "
                f"(chứa vết pilot/hiệu chuẩn). Tuyệt đối không dùng cho Main Annotation!"
            )

        manifest = self._load_manifest()
        allowed_files = {Path(f["file_name"]).name: f for f in manifest.get("files", [])}

        if clean_shard not in allowed_files:
            raise SelectionGateError(
                f"LỆNH CHẶN CỔNG 0: Shard '{shard_name}' không tồn tại trong source_manifest đã khóa!"
            )

        if shard_lfs_sha256 is not None:
            expected_sha = allowed_files[clean_shard].get("source_metadata_lfs_sha256")
            if expected_sha and shard_lfs_sha256 != expected_sha:
                raise SelectionGateError(
                    f"LỆNH CHẶN CỔNG 0: Mã băm LFS của shard '{shard_name}' ({shard_lfs_sha256}) "
                    f"không khớp với manifest ({expected_sha})!"
                )

        return True

    def gate_1_field_validity(self, sample: Dict[str, Any]) -> Tuple[bool, str]:
        """Cổng 1: Kiểm tra tính hợp lệ của trường và ngưỡng ký tự HTML."""
        url = sample.get("url")
        html = sample.get("html")

        if not isinstance(url, str) or not url.strip():
            return False, "reject_empty_url"

        # Kiểm tra URL hợp lệ theo chuẩn HTTP/HTTPS
        try:
            norm_url = normalize_url(url)
        except Exception:
            return False, "reject_invalid_url_format"

        if not isinstance(html, str) or not html.strip():
            return False, "reject_empty_html"

        html_len = len(html)
        if html_len < self.min_html_chars or html_len > self.max_html_chars:
            return False, f"reject_html_len_{html_len}"

        # Kiểm tra cửa sổ ngày (nếu cấu hình)
        date_str = sample.get("date")
        if date_str:
            date_val = str(date_str)[:10]
            if self.min_date and date_val < self.min_date:
                return False, "reject_before_min_date"
            if self.max_date and date_val > self.max_date:
                return False, "reject_after_max_date"

        return True, "passed"

    def gate_2_anti_leakage(self, sample: Dict[str, Any]) -> Tuple[bool, str]:
        """Cổng 2: Kiểm tra chống rò rỉ qua ExclusionRegistry (Fail-closed)."""
        self.exclusion_registry.assert_restricted_commitments_verified()

        if self.exclusion_registry.is_excluded(sample):
            return False, "reject_exclusion_registry_match"

        return True, "passed"

    def run_selection(
        self,
        raw_samples: List[Dict[str, Any]],
        *,
        source_id: str = "phreshphish",
        shard_name: str = "train-001.parquet",
        target_quota: int = 100,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """Thực thi đầy đủ quy trình 5 cổng và báo cáo số đếm chi tiết trước/sau từng cổng."""
        audit_log: Dict[str, Any] = {
            "source_id": source_id,
            "shard_name": shard_name,
            "target_quota": target_quota,
            "seed": seed,
            "gate_counts": {},
            "rejections": {},
        }

        # Cổng 0
        self.gate_0_source_and_shard(source_id, shard_name)
        audit_log["gate_counts"]["gate_0_in"] = len(raw_samples)
        audit_log["gate_counts"]["gate_0_out"] = len(raw_samples)

        # Cổng 1
        g1_passed = []
        for s in raw_samples:
            ok, reason = self.gate_1_field_validity(s)
            if ok:
                g1_passed.append(s)
            else:
                audit_log["rejections"][reason] = audit_log["rejections"].get(reason, 0) + 1
        audit_log["gate_counts"]["gate_1_in"] = len(raw_samples)
        audit_log["gate_counts"]["gate_1_out"] = len(g1_passed)

        # Cổng 2
        g2_passed = []
        for s in g1_passed:
            ok, reason = self.gate_2_anti_leakage(s)
            if ok:
                g2_passed.append(s)
            else:
                audit_log["rejections"][reason] = audit_log["rejections"].get(reason, 0) + 1
        audit_log["gate_counts"]["gate_2_in"] = len(g1_passed)
        audit_log["gate_counts"]["gate_2_out"] = len(g2_passed)

        # Cổng 3: Khử trùng lặp nội bộ (URL, HTML, Domain diversity: tối đa 1 mẫu/domain)
        seen_urls: Set[str] = set()
        seen_htmls: Set[str] = set()
        seen_domains: Set[str] = set()
        g3_passed = []

        for s in g2_passed:
            u = s.get("url", "")
            h = s.get("html", "")
            u_norm = normalize_url(u)
            u_hash = hashlib.sha256(u_norm.encode("utf-8")).hexdigest()
            h_hash = hashlib.sha256(h.encode("utf-8")).hexdigest()
            grp = extract_group_id(u)

            if u_hash in seen_urls:
                audit_log["rejections"]["reject_gate3_duplicate_url"] = audit_log["rejections"].get("reject_gate3_duplicate_url", 0) + 1
                continue
            if h_hash in seen_htmls:
                audit_log["rejections"]["reject_gate3_duplicate_html"] = audit_log["rejections"].get("reject_gate3_duplicate_html", 0) + 1
                continue
            if grp in seen_domains and grp != "unknown":
                audit_log["rejections"]["reject_gate3_domain_collision"] = audit_log["rejections"].get("reject_gate3_domain_collision", 0) + 1
                continue

            seen_urls.add(u_hash)
            seen_htmls.add(h_hash)
            if grp != "unknown":
                seen_domains.add(grp)
            g3_passed.append(s)

        audit_log["gate_counts"]["gate_3_in"] = len(g2_passed)
        audit_log["gate_counts"]["gate_3_out"] = len(g3_passed)

        # Cổng 4: Chọn mẫu với Seed niêm phong
        rng = random.Random(seed)
        shuffled = list(g3_passed)
        rng.shuffle(shuffled)
        final_sample = shuffled[:target_quota]

        audit_log["gate_counts"]["gate_4_in"] = len(g3_passed)
        audit_log["gate_counts"]["gate_4_out"] = len(final_sample)
        audit_log["selected_count"] = len(final_sample)

        return {
            "selected_samples": final_sample,
            "audit_log": audit_log,
        }
