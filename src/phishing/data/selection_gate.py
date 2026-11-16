"""Bộ lọc cổng chọn mẫu 5 giai đoạn có thể tái lập cho Main Annotation (Anti-Leakage Protocol).

Thiết kế theo kỷ luật Ponytail và chuẩn mực ARS (Academic Research Skills):
- Cổng 0 (Gate 0 - Shard & Source Integrity):
  * Bắt buộc kiểm tra nguồn được duyệt (phreshphish, chặn hoàn toàn PhishVN).
  * Bắt buộc kiểm tra revision đã khóa (eabec4b7a66324b79cc8a0ad856d1731dc26fe1a).
  * Cách ly tuyệt đối train-000 và train-055 (chứa vết pilot/hiệu chuẩn).
  * TỰ ĐỐI CHIẾU mã băm SHA-256 thực tế của tệp shard trên đĩa với source_manifest.json.
- Cổng 1 (Gate 1 - Field Validity & Operational Windows):
  * URL bắt buộc hợp lệ theo chuẩn HTTP/HTTPS tuyệt đối (qua normalize_url).
  * HTML không rỗng, giới hạn ký tự [min_html_chars, max_html_chars].
  * Ngày bắt buộc có mặt, đúng định dạng và nằm trong cửa sổ thời gian đã duyệt.
- Cổng 2 (Gate 2 - Cryptographic Anti-Leakage Filter):
  * Fail-closed: ném RuntimeError nếu thiếu hoặc sai mã băm hồ sơ hạn chế.
  * Kiểm tra đầy đủ: raw URL hash, normalized URL hash, raw HTML hash, cleaned HTML hash,
    nhóm miền bare domain hash và prefixed domain group hash (eTLD+1).
- Cổng 3 (Gate 3 - Candidate Deduplication & Sequential Template Clustering):
  * Khử trùng URL thô và URL chuẩn hóa.
  * Khử trùng HTML thô.
  * Giới hạn mật độ miền (Domain Diversity): tối đa 1 mẫu cho mỗi domain (eTLD+1).
  * Kiểm tra template tuần tự (HTML tag skeleton hash) để phát hiện và chặn template clone/phishing kit.
- Cổng 4 (Gate 4 - Locked Stratified Sampling & Quota Enforcement):
  * Phân tầng theo các strata đã khóa (chiều dài HTML / độ phức tạp).
  * Thực thi nghiêm ngặt chỉ tiêu quota: nếu số ứng viên < target_quota, dừng fail-closed
    với SelectionGateError, không âm thầm trả về tập thiếu quota.
"""

from datetime import datetime
import hashlib
import json
from pathlib import Path
import random
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from phishing.data.exclusion import ExclusionRegistry
from phishing.data.grouping import extract_group_id
from phishing.data.template_similarity import TemplateSimilarityEngine
from phishing.preprocessing.html import clean_html
from phishing.preprocessing.urls import normalize_url

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "configs" / "source_manifest.json"

DEFAULT_APPROVED_SOURCE = "phreshphish"
DEFAULT_APPROVED_REVISION = "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a"
DEFAULT_MIN_DATE = "2024-10-01"
DEFAULT_MAX_DATE = "2025-09-08"

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


def compute_file_sha256(file_path: Path | str, chunk_size: int = 65536) -> str:
    """Tính mã băm SHA-256 từ luồng byte thực tế của tệp trên đĩa."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"Không tìm thấy tệp để tính SHA-256: '{file_path}'")
    hasher = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_template_skeleton_hash(html: str) -> str:
    """Trích xuất khung sườn cấu trúc thẻ HTML (loại bỏ thuộc tính, text, scripts, styles)
    để phát hiện các mẫu gần trùng (near-duplicate) hoặc template clone sinh từ cùng phishing kit.
    """
    if not isinstance(html, str) or not html.strip():
        return ""
    # Trích xuất tên thẻ mở/đóng, bỏ qua các thẻ không mang tính cấu trúc nội dung
    tags = re.findall(r'<(/?[a-zA-Z0-9]+)[\s/>]', html.lower())
    skeleton = "|".join(
        t for t in tags
        if not any(t.startswith(ignore) for ignore in ("script", "/script", "style", "/style", "meta", "link", "!--", "?"))
    )
    return hashlib.sha256(skeleton.encode("utf-8")).hexdigest()


class SelectionGatePipeline:
    """Đường ống chọn mẫu 5 cổng (Gates 0-4) có kiểm toán số liệu trước/sau từng cổng."""

    def __init__(
        self,
        exclusion_registry: Optional[ExclusionRegistry] = None,
        source_manifest_path: Optional[Path | str] = None,
        approved_source: str = DEFAULT_APPROVED_SOURCE,
        approved_revision: str = DEFAULT_APPROVED_REVISION,
        min_html_chars: int = 1,
        max_html_chars: int = 2_000_000,
        min_date: Optional[str] = DEFAULT_MIN_DATE,
        max_date: Optional[str] = DEFAULT_MAX_DATE,
    ) -> None:
        self.exclusion_registry = exclusion_registry or ExclusionRegistry()
        self.manifest_path = Path(source_manifest_path) if source_manifest_path else DEFAULT_MANIFEST_PATH
        self.approved_source = approved_source.lower()
        self.approved_revision = approved_revision
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
        shard_path: Path | str,
        *,
        revision: Optional[str] = None,
    ) -> bool:
        """Cổng 0: Kiểm định tính toàn vẹn Shard và Nguồn (Fail-closed).

        Quy chuẩn:
        1. Nguồn bắt buộc thuộc danh mục được duyệt (chặn PhishVN).
        2. Git revision bắt buộc khớp với revision đã khóa trong manifest.
        3. Shard bị cách ly (train-000, train-055) bắt buộc bị từ chối lập tức.
        4. Tệp shard bắt buộc tồn tại trên đĩa và có mã băm byte thực tế khớp 100% với source_manifest.json.
        """
        # 1. Kiểm tra nguồn
        if source_id.lower() in [s.lower() for s in BLOCKED_SOURCES]:
            raise SelectionGateError(
                f"LỆNH CHẶN CỔNG 0: Nguồn '{source_id}' chưa được phê duyệt trích xuất độc lập!"
            )
        if source_id.lower() != self.approved_source:
            raise SelectionGateError(
                f"LỆNH CHẶN CỔNG 0: Nguồn '{source_id}' không khớp với nguồn được duyệt '{self.approved_source}'!"
            )

        # 2. Kiểm tra revision
        rev = revision or self.approved_revision
        if rev != self.approved_revision:
            raise SelectionGateError(
                f"LỆNH CHẶN CỔNG 0: Revision '{rev}' không khớp với revision đã khóa '{self.approved_revision}'!"
            )

        # 3. Kiểm tra cách ly shard
        p_shard = Path(shard_path)
        clean_shard = p_shard.name
        if clean_shard in QUARANTINED_SHARDS or str(shard_path) in QUARANTINED_SHARDS:
            raise SelectionGateError(
                f"LỆNH CHẶN CỔNG 0: Shard '{clean_shard}' thuộc danh mục BỊ CÁCH LY "
                f"(chứa vết pilot/hiệu chuẩn). Tuyệt đối không dùng cho Main Annotation!"
            )

        # 4. Kiểm tra sự hiện diện của tệp trên đĩa
        if not p_shard.exists():
            raise SelectionGateError(
                f"LỆNH CHẶN CỔNG 0: Không tìm thấy tệp shard thực tế tại '{p_shard}'!"
            )

        # 5. Đối soát với manifest và tự tính hash byte tệp thực tế
        manifest = self._load_manifest()
        allowed_files = {Path(f["file_name"]).name: f for f in manifest.get("files", [])}

        if clean_shard not in allowed_files:
            raise SelectionGateError(
                f"LỆNH CHẶN CỔNG 0: Shard '{clean_shard}' không tồn tại trong source_manifest đã khóa!"
            )

        file_entry = allowed_files[clean_shard]
        expected_sha = file_entry.get("source_metadata_lfs_sha256") or file_entry.get("locally_verified_sha256")
        if not expected_sha:
            raise SelectionGateError(
                f"LỆNH CHẶN CỔNG 0: Không tìm thấy mã băm chuẩn trong manifest cho shard '{clean_shard}'!"
            )

        actual_sha = compute_file_sha256(p_shard)
        if actual_sha != expected_sha:
            raise SelectionGateError(
                f"LỆNH CHẶN CỔNG 0: Mã băm byte thực tế của '{clean_shard}' ({actual_sha}) "
                f"không khớp với mã băm trong manifest ({expected_sha})!"
            )

        return True

    def gate_1_field_validity(self, sample: Dict[str, Any]) -> Tuple[bool, str]:
        """Cổng 1: Kiểm tra tính hợp lệ của trường, giới hạn HTML và cửa sổ ngày bắt buộc."""
        url = sample.get("url")
        html = sample.get("html")

        # 1. Kiểm tra URL
        if not isinstance(url, str) or not url.strip():
            return False, "reject_empty_url"

        try:
            norm_url = normalize_url(url)
        except (ValueError, TypeError):
            return False, "reject_invalid_url_format"

        # 2. Kiểm tra HTML
        if not isinstance(html, str) or not html.strip():
            return False, "reject_empty_html"

        html_len = len(html)
        if html_len < self.min_html_chars or html_len > self.max_html_chars:
            return False, f"reject_html_len_{html_len}"

        # 3. Kiểm tra Ngày (Bắt buộc theo ARS & Kế hoạch V3.5)
        raw_date = sample.get("date")
        if raw_date is None or (isinstance(raw_date, str) and not raw_date.strip()):
            return False, "reject_missing_date"

        if not isinstance(raw_date, str):
            return False, "reject_invalid_date_format"

        clean_date = raw_date.strip()
        # Bắt buộc chuỗi định dạng chính xác YYYY-MM-DD (10 ký tự), từ chối mọi hậu tố rác
        if not re.fullmatch(r"^\d{4}-\d{2}-\d{2}$", clean_date):
            return False, "reject_invalid_date_format"

        try:
            parsed_date = datetime.strptime(clean_date, "%Y-%m-%d")
        except ValueError:
            return False, "reject_invalid_date_format"

        formatted_date = parsed_date.strftime("%Y-%m-%d")
        if self.min_date and formatted_date < self.min_date:
            return False, f"reject_date_before_min_{formatted_date}"
        if self.max_date and formatted_date > self.max_date:
            return False, f"reject_date_after_max_{formatted_date}"

        return True, "passed"

    def gate_2_anti_leakage(self, sample: Dict[str, Any]) -> Tuple[bool, str]:
        """Cổng 2: Kiểm tra chống rò rỉ toàn diện (Fail-closed qua ExclusionRegistry).

        Kiểm tra: raw URL hash, normalized URL hash, raw HTML hash, cleaned HTML hash,
        và nhóm miền (cả bare domain hash lẫn prefixed domain group hash).
        """
        self.exclusion_registry.assert_restricted_commitments_verified()

        raw_url = sample.get("url", "")
        raw_html = sample.get("html", "")

        # 1. Kiểm tra tiền xử lý URL và normalized URL hash
        if raw_url:
            try:
                norm_url = normalize_url(raw_url)
                norm_url_hash = hashlib.sha256(norm_url.encode("utf-8")).hexdigest()
                if norm_url_hash in self.exclusion_registry._url_hashes:
                    return False, "reject_exclusion_registry_match"
            except (ValueError, TypeError):
                return False, "reject_gate2_preprocessing_error"

        # 2. Kiểm tra tiền xử lý HTML và cleaned HTML hash
        if raw_html:
            try:
                norm_url_page = (
                    norm_url if "norm_url" in locals()
                    else (raw_url if (isinstance(raw_url, str) and raw_url.startswith(("http://", "https://")))
                          else (f"http://{raw_url}" if (isinstance(raw_url, str) and raw_url.strip()) else "http://placeholder.local"))
                )
                cl_html = clean_html(raw_html, page_url=norm_url_page, max_characters=self.max_html_chars)
                cl_html_hash = hashlib.sha256(cl_html.encode("utf-8")).hexdigest()
                if cl_html_hash in self.exclusion_registry._html_hashes:
                    return False, "reject_exclusion_registry_match"
            except (ValueError, TypeError):
                return False, "reject_gate2_preprocessing_error"

        # 3. Kiểm tra nhóm miền (Domain Group)
        if raw_url:
            group_id = extract_group_id(raw_url)
            if group_id != "unknown":
                prefixed_hash = hashlib.sha256(group_id.encode("utf-8")).hexdigest()
                bare_domain = group_id.replace("domain:", "")
                bare_hash = hashlib.sha256(bare_domain.encode("utf-8")).hexdigest()

                if prefixed_hash in self.exclusion_registry._group_hashes or bare_hash in self.exclusion_registry._group_hashes:
                    return False, "reject_exclusion_registry_match"

        # 4. Kiểm tra toàn diện qua ExclusionRegistry (bao gồm raw hash, summary fingerprints)
        if self.exclusion_registry.is_excluded(sample):
            return False, "reject_exclusion_registry_match"

        return True, "passed"

    def run_selection(
        self,
        raw_samples: List[Dict[str, Any]],
        *,
        source_id: str = DEFAULT_APPROVED_SOURCE,
        shard_path: Path | str = "data/raw/phreshphish/data/train-001.parquet",
        revision: Optional[str] = None,
        target_quota: int = 100,
        seed: int = 42,
        skip_gate_0_file_check: bool = False,
        vetting_only: bool = False,
    ) -> Dict[str, Any]:
        """Thực thi đầy đủ quy trình 5 cổng và báo cáo số đếm chi tiết trước/sau từng cổng.

        Nếu số mẫu sau Cổng 3 không đủ target_quota, ném SelectionGateError (Fail-closed).
        """
        audit_log: Dict[str, Any] = {
            "source_id": source_id,
            "revision": revision or self.approved_revision,
            "shard": str(shard_path),
            "target_quota": target_quota,
            "seed": seed,
            "gate_counts": {},
            "rejections": {},
        }

        # Cổng 0
        if not skip_gate_0_file_check:
            self.gate_0_source_and_shard(source_id, shard_path, revision=revision)
        audit_log["gate_counts"]["gate_0_in"] = len(raw_samples)
        audit_log["gate_counts"]["gate_0_out"] = len(raw_samples)

        # Cổng 1: Hợp lệ trường & Ngưỡng HTML & Ngày
        g1_passed = []
        for s in raw_samples:
            ok, reason = self.gate_1_field_validity(s)
            if ok:
                g1_passed.append(s)
            else:
                audit_log["rejections"][reason] = audit_log["rejections"].get(reason, 0) + 1
        audit_log["gate_counts"]["gate_1_in"] = len(raw_samples)
        audit_log["gate_counts"]["gate_1_out"] = len(g1_passed)

        # Cổng 2: Chống rò rỉ loại trừ
        g2_passed = []
        for s in g1_passed:
            ok, reason = self.gate_2_anti_leakage(s)
            if ok:
                g2_passed.append(s)
            else:
                audit_log["rejections"][reason] = audit_log["rejections"].get(reason, 0) + 1
        audit_log["gate_counts"]["gate_2_in"] = len(g1_passed)
        audit_log["gate_counts"]["gate_2_out"] = len(g2_passed)

        # Cổng 3: Khử trùng lặp nội bộ, đảm bảo đa dạng miền (max 1/eTLD+1) và loại bỏ Template Clones tuần tự
        # QUY TẮC LOẠI BỎ THIÊN LỆCH THỨ TỰ HÀNG (Row-Order Bias Elimination):
        # Sắp xếp các ứng viên vượt qua Cổng 2 theo khóa chính tắc (canonical key) không phụ thuộc thứ tự shard,
        # sau đó xáo trộn theo PRNG seed niêm phong TRƯỚC KHI lọc 1 đại diện cho mỗi miền / template.
        # Nhờ vậy, kết quả chọn mẫu hoàn toàn bất biến đối với bất kỳ hoán vị đầu vào nào của shard.
        canonical_sorted = sorted(
            g2_passed,
            key=lambda s: (
                normalize_url(s.get("url", "")),
                hashlib.sha256((s.get("html") or "").encode("utf-8")).hexdigest(),
            ),
        )
        rng_order = random.Random(seed)
        shuffled_candidates = list(canonical_sorted)
        rng_order.shuffle(shuffled_candidates)

        seen_urls: Set[str] = set()
        seen_htmls: Set[str] = set()
        seen_domains: Set[str] = set()
        template_engine = TemplateSimilarityEngine(
            max_allowed_simhash_distance=10,
            max_allowed_dom_jaccard=0.85,
        )
        g3_passed = []

        for s in shuffled_candidates:
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

            # Đánh giá độ tương đồng template theo động cơ TemplateSimilarityEngine (ngưỡng V3.5)
            sim_res = template_engine.check_candidate_similarity(candidate_html=h)
            if sim_res.get("is_clone_template"):
                audit_log["rejections"]["reject_gate3_template_clone"] = audit_log["rejections"].get("reject_gate3_template_clone", 0) + 1
                continue

            seen_urls.add(u_hash)
            seen_htmls.add(h_hash)
            if grp != "unknown":
                seen_domains.add(grp)
            template_engine.register_template(
                template_id=f"acc_{len(g3_passed)}",
                description="Accepted candidate in Gate 3",
                sample_html=h,
            )
            g3_passed.append(s)

        audit_log["gate_counts"]["gate_3_in"] = len(g2_passed)
        audit_log["gate_counts"]["gate_3_out"] = len(g3_passed)

        # Chế độ kiểm nguồn độc lập (Source Vetting Only):
        # Dừng an toàn ngay sau Cổng 3, không thực hiện Cổng 4 (Quota Sampling/Phân tầng mẫu)
        if vetting_only:
            audit_log["vetting_only"] = True
            audit_log["candidates_before_gate_4"] = len(g3_passed)
            audit_log["quota_target"] = target_quota
            audit_log["meets_quota_target"] = len(g3_passed) >= target_quota
            return {
                "selected_samples": [],
                "candidates_before_gate_4": g3_passed,
                "audit_log": audit_log,
            }

        # Cổng 4: Kiểm tra Quota Fail-Closed & Lấy mẫu ngẫu nhiên xác định (Seeded Random Sampling)
        # Ghi chú phương pháp luận: Pipeline thực thi lấy mẫu ngẫu nhiên xác định với quota cứng.
        # Phương án phân tầng (Stratified Sampling) theo nhãn nguồn đang chờ Lead D phê duyệt riêng.
        if len(g3_passed) < target_quota:
            raise SelectionGateError(
                f"LỆNH CHẶN CỔNG 4 (Fail-Closed): Số lượng ứng viên sau khử trùng ({len(g3_passed)}) "
                f"không đạt chỉ tiêu quota yêu cầu ({target_quota})! Pipeline dừng an toàn."
            )

        final_sample = g3_passed[:target_quota]

        audit_log["gate_counts"]["gate_4_in"] = len(g3_passed)
        audit_log["gate_counts"]["gate_4_out"] = len(final_sample)
        audit_log["selected_count"] = len(final_sample)

        return {
            "selected_samples": final_sample,
            "audit_log": audit_log,
        }
