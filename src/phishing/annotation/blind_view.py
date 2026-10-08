"""Module quản lý và xuất giao diện gán nhãn mù an toàn (Blind View) theo Anti-Leakage Protocol.

Quy chuẩn ARS bắt buộc:
1. Zero Data Peeking / Anti-Leakage:
   - Ẩn hoàn toàn nhãn gốc (source_label, label), mục tiêu (target), điểm mô hình (score),
     và kết quả của đánh giá viên còn lại.
   - Kiểm tra rò rỉ dữ liệu triệt để (assert_no_label_leak) trước khi xuất view.
   - Bắt buộc kiểm tra allowlist chặt chẽ cho gói dữ liệu mù, ID mẫu trung tính do C cấp,
     cấm mọi tiền tố/hậu tố liên quan đến nhãn hoặc kết quả của người khác.
2. Safety First:
   - Không bao giờ thực thi JavaScript hoặc render HTML sống của trang phishing.
   - Loại bỏ toàn bộ script, iframe, inline event handlers, form prefilled values.
3. Codebook v1 Compliance:
   - Chuẩn hóa cấu trúc bản ghi gán nhãn (AnnotationRecord) với đầy đủ taxonomy và trường bấm giờ seconds_spent.
   - Tách biệt rạch ròi các bản ghi mô phỏng/dry-run qua cờ is_dry_run, cấm lẫn vào nhãn thật.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Literal, Optional, Sequence, Set, Tuple
from urllib.parse import urljoin, urlparse

from phishing.preprocessing.html import clean_html
from phishing.preprocessing.urls import normalize_url


# Danh mục các trường được phép xuất hiện trong một mẫu BlindSample (Allowlist)
ALLOWED_BLIND_SAMPLE_KEYS: Set[str] = frozenset({
    "sample_id",
    "url",
    "page_text",
    "structure_summary",
    "random_subset",
    "codebook_version",
    "translation_provided",
    "translated_text",
    "translation_source_language",
    "translation_tool",
    "translation_tool_version",
    "translation_sha256",
})

TRANSLATION_FIELDS = (
    "translation_provided", "translated_text", "translation_source_language",
    "translation_tool", "translation_tool_version", "translation_sha256",
)

# Danh mục các trường được phép trong structure_summary (Allowlist)
ALLOWED_STRUCTURE_SUMMARY_KEYS: Set[str] = frozenset({
    "title",
    "forms",
    "inputs",
    "password_inputs",
    "has_login_form",
    "buttons",
    "external_links",
})

# Danh mục các trường cấm tuyệt đối xuất hiện trong Blind View (Chống rò rỉ nhãn)
FORBIDDEN_LEAK_KEYS: Set[str] = frozenset({
    "label",
    "source_label",
    "target",
    "targets",
    "org_target",
    "org_targets",
    "primary_org",
    "primary_org_status",
    "matcher_score",
    "model_score",
    "score",
    "verdict",
    "ground_truth",
    "annotator_results",
    "is_phish",
    "pilot_row_idx",
})

# Các tiền tố bị cấm tuyệt đối (Chống rò rỉ kết quả của người khác hoặc nguồn)
FORBIDDEN_PREFIXES: Tuple[str, ...] = (
    "annotation_",
    "annotation.",
    "rater_",
    "rater.",
    "pass_",
    "label_",
    "result_",
    "source_",
    "annotator_",
    "review_",
    "model_",
)

# Các hậu tố bị cấm
FORBIDDEN_SUFFIXES: Tuple[str, ...] = (
    "_label",
    ".class_label",
    ".label",
    "_target",
    ".target",
    "_score",
    ".score",
    "_verdict",
)

# Danh mục từ khóa nhãn và thương hiệu nhạy cảm bị cấm trong sample_id (Bắt buộc ID trung tính)
SENSITIVE_BRAND_AND_LABEL_TERMS: Set[str] = frozenset({
    "phish", "phishing", "benign", "malicious", "clean", "ham", "suspicious",
    "microsoft", "google", "meta", "facebook", "apple", "amazon",
    "linkedin", "x_twitter", "twitter", "paypal", "adobe",
    "booking", "dhl", "spotify", "alibaba", "mastercard",
})

# Bộ giá trị enum chuẩn hóa theo docs/CODEBOOK_V1.md
VALID_CLASS_LABELS = frozenset({"phishing", "benign", "insufficient_evidence"})
VALID_PRIMARY_ORG_STATUSES = frozenset({"identified", "unknown", "no_clear_target", "multi_target"})
VALID_CATALOG_STATUSES = frozenset({"in_catalog", "outside_catalog", "unresolved"})
VALID_IDENTITY_ROLES = frozenset({"identity_claim", "mention_only", "unclear"})
VALID_DOMAIN_ROLES = frozenset({
    "first_party_identity",
    "first_party_content",
    "user_content_hosting",
    "authorized_service",
    "unverified",
})


def assert_pilot_review_status(manifest: Dict[str, Any]) -> None:
    """Common gate for annotation and evaluation; hashes alone do not confer approval."""
    if manifest.get("status") in {"invalidated", "blocked_rebuild_required"}:
        raise ValueError("PILOT BLOCKED: invalidated/unverified package cannot be opened")
    if manifest.get("dataset_id") == "REAL-PILOT-32-V2":
        if (manifest.get("status") != "approved"
                or manifest.get("source_verification_status") != "verified_pinned_train_rows"
                or manifest.get("exposure_review") != {"A": "approved", "B": "approved", "D": "approved"}
                or type(manifest.get("sample_count")) is not int or manifest["sample_count"] != 32):
            raise ValueError("PILOT V2 BLOCKED: source/exposure/count review incomplete")


def default_pilot_manifest_path(dataset_id: str, project_root: Path) -> Path:
    """Resolve only known real pilot versions; unknown real packages need --manifest."""
    names = {"REAL-PILOT-32-V1": "pilot_manifest.json",
             "REAL-PILOT-32-V2": "pilot_manifest_v2.json"}
    if dataset_id not in names:
        raise ValueError(f"LỖI MANIFEST: Gói thật '{dataset_id}' cần chỉ định --manifest.")
    return project_root / "configs" / names[dataset_id]


def assert_neutral_sample_id(sample_id: Any) -> None:
    """Kiểm tra mã định danh mẫu phải là ID trung tính do C cấp, cấm chứa nhãn hay tên tổ chức."""
    sid_str = str(sample_id).strip()
    if not sid_str:
        raise ValueError("sample_id không được để rỗng.")

    sid_lower = sid_str.lower()
    tokens = set(re.findall(r"[a-z0-9]+", sid_lower))
    matched_terms = [t for t in sorted(list(SENSITIVE_BRAND_AND_LABEL_TERMS)) if t in tokens or t in sid_lower]
    if matched_terms:
        raise ValueError(
            f"RÒ RỈ DỮ LIỆU PHÁT HIỆN: sample_id '{sample_id}' chứa từ khóa định danh/nhãn nhạy cảm {matched_terms}. "
            f"sample_id phải là mã trung tính do C cấp (ví dụ: PILOT-001, SMP-101)."
        )


def assert_no_label_leak(data: Any, path: str = "root") -> None:
    """Kiểm tra đệ quy đảm bảo không có bất kỳ trường nhãn hoặc metadata cấm nào xuất hiện trong Blind View."""
    if isinstance(data, dict):
        # 1. Nếu là từ điển của một mẫu (chứa sample_id và url), áp dụng Allowlist chặt chẽ
        if "sample_id" in data and "url" in data:
            extra_keys = set(data.keys()) - ALLOWED_BLIND_SAMPLE_KEYS
            if extra_keys:
                raise ValueError(
                    f"RÒ RỈ DỮ LIỆU PHÁT HIỆN: Mẫu tại '{path}' chứa các khóa ngoài allowlist: {sorted(list(extra_keys))}! "
                    f"Blind sample chỉ được phép chứa: {sorted(list(ALLOWED_BLIND_SAMPLE_KEYS))}."
                )
            assert_neutral_sample_id(data["sample_id"])
            if str(data.get("codebook_version") or "").lstrip("v").startswith("1.1.") and "translation_provided" not in data:
                raise ValueError(f"LỖI BẢN DỊCH: Mẫu v1.1 tại '{path}' thiếu translation_provided.")
            if "translation_provided" in data:
                provided = data["translation_provided"]
                if type(provided) is not bool:
                    raise ValueError(f"LỖI BẢN DỊCH: translation_provided tại '{path}' phải là boolean.")
                if provided:
                    for field in TRANSLATION_FIELDS[1:]:
                        if not isinstance(data.get(field), str) or not data[field].strip():
                            raise ValueError(f"LỖI BẢN DỊCH: Mẫu tại '{path}' thiếu {field}.")
                    actual_hash = hashlib.sha256(data["translated_text"].encode("utf-8")).hexdigest()
                    if data["translation_sha256"] != actual_hash:
                        raise ValueError(f"LỖI BẢN DỊCH: translation_sha256 tại '{path}' không khớp nội dung.")
                elif any(field in data for field in TRANSLATION_FIELDS[1:]):
                    raise ValueError(f"LỖI BẢN DỊCH: Mẫu tại '{path}' khai báo không dịch nhưng có metadata dịch.")
            elif any(field in data for field in TRANSLATION_FIELDS[1:]):
                raise ValueError(f"LỖI BẢN DỊCH: Mẫu tại '{path}' có bản dịch nhưng thiếu translation_provided.")

            summary = data.get("structure_summary")
            if isinstance(summary, dict):
                summary_extra = set(summary.keys()) - ALLOWED_STRUCTURE_SUMMARY_KEYS
                if summary_extra:
                    raise ValueError(
                        f"RÒ RỈ DỮ LIỆU PHÁT HIỆN: structure_summary tại '{path}' chứa khóa ngoài allowlist: {sorted(list(summary_extra))}."
                    )

        # 2. Kiểm tra từng cặp khóa-giá trị
        for key, value in data.items():
            k_lower = str(key).lower()
            if k_lower in FORBIDDEN_LEAK_KEYS:
                raise ValueError(
                    f"RÒ RỈ DỮ LIỆU PHÁT HIỆN: Khóa cấm '{key}' xuất hiện tại vị trí '{path}.{key}'! "
                    f"Quy chuẩn Blind View cấm hoàn toàn nhãn nguồn, target hoặc điểm mô hình."
                )

            for pfx in FORBIDDEN_PREFIXES:
                if k_lower.startswith(pfx):
                    raise ValueError(
                        f"RÒ RỈ DỮ LIỆU PHÁT HIỆN: Khóa '{key}' mang tiền tố cấm '{pfx}' tại '{path}.{key}'! "
                        f"Không được để lộ kết quả của người khác hoặc thông tin nguồn."
                    )

            for sfx in FORBIDDEN_SUFFIXES:
                if k_lower.endswith(sfx) or sfx in k_lower:
                    raise ValueError(
                        f"RÒ RỈ DỮ LIỆU PHÁT HIỆN: Khóa '{key}' chứa hậu tố nhãn/mô hình '{sfx}' tại '{path}.{key}'!"
                    )

            if k_lower == "sample_id":
                assert_neutral_sample_id(value)

            assert_no_label_leak(value, path=f"{path}.{key}")
    elif isinstance(data, (list, tuple)):
        for idx, item in enumerate(data):
            assert_no_label_leak(item, path=f"{path}[{idx}]")


class _SafeContentExtractor(HTMLParser):
    """Bộ bóc tách văn bản an toàn và cấu trúc DOM tóm tắt, loại bỏ script/iframe/event/style."""

    def __init__(self, page_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.title: str = ""
        self._in_title = False
        self._text_chunks: List[str] = []
        self._suppress_depth = 0
        self.forms_count = 0
        self.inputs_count = 0
        self.password_inputs_count = 0
        self.has_login_form = False
        self.buttons_count = 0
        self.external_links_count = 0

        parsed_url = urlparse(page_url)
        self.page_domain = parsed_url.hostname or ""

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        tag_lower = tag.lower()
        attr_dict = {k.lower(): v for k, v in attrs if k}

        # Bỏ qua hoàn toàn các khối script, style, iframe, noscript, svg, object, embed
        if tag_lower in {"script", "style", "iframe", "noscript", "svg", "object", "embed"}:
            self._suppress_depth += 1
            return

        if self._suppress_depth > 0:
            return

        if tag_lower == "title":
            self._in_title = True
        elif tag_lower == "form":
            self.forms_count += 1
        elif tag_lower == "input":
            self.inputs_count += 1
            itype = (attr_dict.get("type") or "text").lower()
            if itype == "password":
                self.password_inputs_count += 1
                self.has_login_form = True
        elif tag_lower in {"button"}:
            self.buttons_count += 1
        elif tag_lower == "a":
            href = attr_dict.get("href")
            if href:
                try:
                    full_url = urljoin(self.page_url, href)
                    parsed_href = urlparse(full_url)
                    if parsed_href.hostname and parsed_href.hostname != self.page_domain:
                        self.external_links_count += 1
                except Exception:
                    pass

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower in {"script", "style", "iframe", "noscript", "svg", "object", "embed"}:
            if self._suppress_depth > 0:
                self._suppress_depth -= 1
            return

        if tag_lower == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._suppress_depth > 0:
            return
        cleaned = data.strip()
        if not cleaned:
            return
        if self._in_title:
            self.title += " " + cleaned
        else:
            self._text_chunks.append(cleaned)

    def get_clean_text(self) -> str:
        raw_text = " ".join(self._text_chunks)
        return re.sub(r"\s+", " ", raw_text).strip()

    def get_structure_summary(self) -> Dict[str, Any]:
        return {
            "title": self.title.strip(),
            "forms": self.forms_count,
            "inputs": self.inputs_count,
            "password_inputs": self.password_inputs_count,
            "has_login_form": self.has_login_form,
            "buttons": self.buttons_count,
            "external_links": self.external_links_count,
        }


def extract_safe_view_content(html_content: str | None, page_url: str, *, max_html_characters: int = 1_000_000) -> Tuple[str, Dict[str, Any]]:
    """Trích xuất văn bản an toàn và cấu trúc DOM tóm tắt từ nội dung HTML đã cho.

    Không thực thi JavaScript, không nạp mạng, loại bỏ mọi thẻ nguy hiểm.
    """
    if not html_content:
        return "", {
            "title": "",
            "forms": 0,
            "inputs": 0,
            "password_inputs": 0,
            "has_login_form": False,
            "buttons": 0,
            "external_links": 0,
        }

    pre_cleaned = clean_html(html_content, page_url, max_characters=max_html_characters)
    parser = _SafeContentExtractor(page_url)
    parser.feed(pre_cleaned)
    parser.close()
    return parser.get_clean_text(), parser.get_structure_summary()


@dataclass(frozen=True, slots=True)
class BlindSample:
    """Mẫu dữ liệu mù an toàn trình bày cho đánh giá viên A và B."""
    sample_id: str
    url: str
    page_text: str
    structure_summary: Dict[str, Any]
    random_subset: bool = True
    codebook_version: str = "1.0.0"
    translated_text: str | None = None
    translation_source_language: str | None = None
    translation_tool: str | None = None
    translation_tool_version: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        if self.translated_text is None and any(value is not None for value in (
            self.translation_source_language, self.translation_tool, self.translation_tool_version,
        )):
            raise ValueError("LỖI BẢN DỊCH: Có metadata dịch nhưng không có translated_text.")
        d = {
            "sample_id": self.sample_id,
            "url": self.url,
            "page_text": self.page_text,
            "structure_summary": self.structure_summary,
            "random_subset": self.random_subset,
            "codebook_version": self.codebook_version,
        }
        if self.translated_text is not None:
            d.update({
                "translation_provided": True,
                "translated_text": self.translated_text,
                "translation_source_language": self.translation_source_language,
                "translation_tool": self.translation_tool,
                "translation_tool_version": self.translation_tool_version,
                "translation_sha256": hashlib.sha256(self.translated_text.encode("utf-8")).hexdigest(),
            })
        elif self.codebook_version.lstrip("v").startswith("1.1."):
            d["translation_provided"] = False
        assert_no_label_leak(d)
        return d


def create_blind_sample(
    raw_sample: Dict[str, Any],
    sample_id: str | None = None,
    random_subset: bool = True,
    codebook_version: str = "1.0.0",
    translated_text: str | None = None,
    translation_source_language: str | None = None,
    translation_tool: str | None = None,
    translation_tool_version: str | None = None,
) -> BlindSample:
    """Tạo mẫu BlindSample an toàn từ bản ghi thô, loại bỏ triệt để mọi nhãn nguồn."""
    if translated_text is None and raw_sample.get("translated_text") is not None:
        raise ValueError("LỖI BẢN DỊCH: Phải bàn giao translated_text bằng tham số tường minh.")
    sid = sample_id or raw_sample.get("sample_id") or raw_sample.get("id") or str(raw_sample.get("row_idx", "SMP-001"))
    assert_neutral_sample_id(sid)

    url = raw_sample.get("url", "https://unknown.local/")
    try:
        norm_url = normalize_url(url)
    except Exception:
        norm_url = url

    html_content = raw_sample.get("html") or raw_sample.get("html_content")
    page_text = raw_sample.get("text") or raw_sample.get("text_content")

    if html_content:
        extracted_text, summary = extract_safe_view_content(html_content, norm_url)
        if not extracted_text and page_text:
            extracted_text = re.sub(r"\s+", " ", str(page_text)).strip()
    else:
        extracted_text = re.sub(r"\s+", " ", str(page_text or "")).strip()
        summary = {
            "title": "",
            "forms": int(raw_sample.get("forms", 0)),
            "inputs": int(raw_sample.get("inputs", 0)),
            "password_inputs": int(raw_sample.get("password_inputs", 0)),
            "has_login_form": int(raw_sample.get("password_inputs", 0)) > 0,
            "buttons": 0,
            "external_links": 0,
        }

    is_random = raw_sample.get("random_subset", random_subset)
    cb_ver = raw_sample.get("codebook_version", codebook_version)

    blind = BlindSample(
        sample_id=str(sid),
        url=norm_url,
        page_text=extracted_text,
        structure_summary=summary,
        random_subset=bool(is_random),
        codebook_version=str(cb_ver),
        translated_text=translated_text,
        translation_source_language=translation_source_language,
        translation_tool=translation_tool,
        translation_tool_version=translation_tool_version,
    )
    assert_no_label_leak(blind.to_dict())
    return blind


def compute_sample_content_hash(sample: Any) -> str:
    """Tính mã băm toàn vẹn SHA-256 nội dung của một mẫu mà người gán nhãn nhìn thấy.

    Quy chuẩn ARS & Safety:
    Bao gồm toàn bộ các thành phần hiển thị thực tế cho annotator:
    - URL của trang (url)
    - Toàn bộ văn bản đã làm sạch an toàn (page_text)
    - Tóm tắt cấu trúc DOM (structure_summary), tuần tự hóa chuẩn canonical JSON
      với các khóa được sắp xếp (sort_keys=True, separators=(',', ':')).

    Hàm này được dùng chung thống nhất cho:
    1. Lưu trữ bản ghi gán nhãn (AnnotationRecord.sample_content_hash)
    2. Kiểm tra tính toàn vẹn khi tiếp tục phiên làm việc (Resume CLI)
    3. Đối soát khớp nội dung từng cặp mẫu giữa A và B trước khi tính Cohen's Kappa.
    """
    if hasattr(sample, "to_dict"):
        sample_dict = sample.to_dict()
    elif isinstance(sample, dict):
        sample_dict = sample
    else:
        sample_dict = {
            "url": getattr(sample, "url", ""),
            "page_text": getattr(sample, "page_text", ""),
            "structure_summary": getattr(sample, "structure_summary", None),
        }

    url_str = str(sample_dict.get("url") or "")
    text_str = str(sample_dict.get("page_text") or "")
    summary = sample_dict.get("structure_summary")
    if isinstance(summary, dict):
        summary_repr = json.dumps(summary, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    elif summary is not None:
        summary_repr = str(summary)
    else:
        summary_repr = ""

    payload = f"{url_str}\0{text_str}\0{summary_repr}".encode("utf-8")
    if sample_dict.get("translation_provided") is True:
        translation = {key: sample_dict.get(key) for key in TRANSLATION_FIELDS}
        payload += b"\0" + json.dumps(translation, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class AnnotationRecord:
    """Bản ghi gán nhãn độc lập chuẩn hóa theo đúng docs/CODEBOOK_V1.md."""
    annotator_id: str
    sample_id: str
    pass_id: int
    class_label: str
    primary_org_status: str
    catalog_status: str
    observed_service: str
    org_targets: List[str]
    primary_org: str
    identity_role: str
    domain_role: str
    evidence_note: str
    seconds_spent: float
    random_subset: bool
    difficult_case: bool
    codebook_version: str = "1.0.0"
    is_dry_run: bool = False
    is_synthetic: bool = False
    dataset_id: str = ""
    dataset_hash: str = ""
    codebook_hash: str = ""
    sampling_plan_version: str = ""
    sample_content_hash: str = ""
    timestamp_utc: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "annotator_id": self.annotator_id,
            "sample_id": self.sample_id,
            "pass_id": self.pass_id,
            "class_label": self.class_label,
            "primary_org_status": self.primary_org_status,
            "catalog_status": self.catalog_status,
            "observed_service": self.observed_service,
            "org_targets": list(self.org_targets),
            "primary_org": self.primary_org,
            "identity_role": self.identity_role,
            "domain_role": self.domain_role,
            "evidence_note": self.evidence_note,
            "seconds_spent": round(float(self.seconds_spent), 2),
            "random_subset": bool(self.random_subset),
            "difficult_case": bool(self.difficult_case),
            "codebook_version": self.codebook_version,
            "is_dry_run": bool(self.is_dry_run),
            "is_synthetic": bool(self.is_synthetic),
            "dataset_id": self.dataset_id,
            "dataset_hash": self.dataset_hash,
            "codebook_hash": self.codebook_hash,
            "sampling_plan_version": self.sampling_plan_version,
            "sample_content_hash": self.sample_content_hash,
            "timestamp_utc": self.timestamp_utc or datetime.now(timezone.utc).isoformat(),
        }


def validate_annotation_record(data: Dict[str, Any]) -> AnnotationRecord:
    """Xác thực và nạp bản ghi gán nhãn theo đúng các ràng buộc trong CODEBOOK_V1."""
    required_keys = {
        "annotator_id", "sample_id", "pass_id", "class_label", "primary_org_status",
        "catalog_status", "observed_service", "org_targets", "primary_org",
        "identity_role", "domain_role", "evidence_note", "seconds_spent",
        "random_subset", "difficult_case",
    }
    missing = required_keys - set(data.keys())
    if missing:
        raise ValueError(f"Bản ghi gán nhãn thiếu các trường bắt buộc: {sorted(list(missing))}")

    class_label = data["class_label"]
    if class_label not in VALID_CLASS_LABELS:
        raise ValueError(f"class_label '{class_label}' không hợp lệ. Phải thuộc: {sorted(list(VALID_CLASS_LABELS))}")

    primary_org_status = data["primary_org_status"]
    if primary_org_status not in VALID_PRIMARY_ORG_STATUSES:
        raise ValueError(f"primary_org_status '{primary_org_status}' không hợp lệ. Phải thuộc: {sorted(list(VALID_PRIMARY_ORG_STATUSES))}")

    catalog_status = data["catalog_status"]
    if catalog_status not in VALID_CATALOG_STATUSES:
        raise ValueError(f"catalog_status '{catalog_status}' không hợp lệ. Phải thuộc: {sorted(list(VALID_CATALOG_STATUSES))}")

    identity_role = data["identity_role"]
    if identity_role not in VALID_IDENTITY_ROLES:
        raise ValueError(f"identity_role '{identity_role}' không hợp lệ. Phải thuộc: {sorted(list(VALID_IDENTITY_ROLES))}")

    domain_role = data["domain_role"]
    if domain_role not in VALID_DOMAIN_ROLES:
        raise ValueError(f"domain_role '{domain_role}' không hợp lệ. Phải thuộc: {sorted(list(VALID_DOMAIN_ROLES))}")

    seconds_spent = float(data["seconds_spent"])
    if seconds_spent < 0.0:
        raise ValueError(f"Thời gian thao tác seconds_spent={seconds_spent} không được âm.")

    org_targets = data["org_targets"]
    if not isinstance(org_targets, list):
        raise TypeError("org_targets phải là danh sách (list) các chuỗi tổ chức.")

    timestamp = data.get("timestamp_utc") or datetime.now(timezone.utc).isoformat()
    is_dry = bool(data.get("is_dry_run", False))
    is_synth = bool(data.get("is_synthetic", False))
    ds_id = str(data.get("dataset_id", ""))
    ds_hash = str(data.get("dataset_hash", ""))
    cb_hash = str(data.get("codebook_hash", ""))
    plan_ver = str(data.get("sampling_plan_version", ""))
    sample_hash = str(data.get("sample_content_hash", ""))

    return AnnotationRecord(
        annotator_id=str(data["annotator_id"]),
        sample_id=str(data["sample_id"]),
        pass_id=int(data["pass_id"]),
        class_label=str(class_label),
        primary_org_status=str(primary_org_status),
        catalog_status=str(catalog_status),
        observed_service=str(data["observed_service"]),
        org_targets=[str(x) for x in org_targets],
        primary_org=str(data["primary_org"]),
        identity_role=str(identity_role),
        domain_role=str(domain_role),
        evidence_note=str(data["evidence_note"]),
        seconds_spent=seconds_spent,
        random_subset=bool(data["random_subset"]),
        difficult_case=bool(data["difficult_case"]),
        codebook_version=str(data.get("codebook_version", "1.0.0")),
        is_dry_run=is_dry,
        is_synthetic=is_synth,
        dataset_id=ds_id,
        dataset_hash=ds_hash,
        codebook_hash=cb_hash,
        sampling_plan_version=plan_ver,
        sample_content_hash=sample_hash,
        timestamp_utc=str(timestamp),
    )


def export_blind_view(
    samples: Sequence[BlindSample | Dict[str, Any]],
    output_path: Path | str,
    *,
    version: str = "1.0.0",
    dataset_id: str = "BLIND-VIEW-V1",
    dataset_type: str = "blind_view",
    is_synthetic: bool = False,
    purpose: str = "Gói dữ liệu Blind View phục vụ gán nhãn mù độc lập (Task LABEL-01)",
    description: str = "",
    sampling_plan_version: str | None = None,
) -> Dict[str, Any]:
    """Xuất danh sách mẫu thành gói JSON Blind View an toàn cho A và B."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    clean_samples: List[Dict[str, Any]] = []
    for item in samples:
        if isinstance(item, BlindSample):
            clean_samples.append(item.to_dict())
        elif isinstance(item, dict):
            if item.get("translation_provided") is True and item.get("translated_text") is None:
                raise ValueError("LỖI BẢN DỊCH: translation_provided=true nhưng thiếu translated_text.")
            if item.get("translation_provided") is False and item.get("translated_text") is not None:
                raise ValueError("LỖI BẢN DỊCH: translation_provided=false nhưng có translated_text.")
            if "translation_sha256" in item and item.get("translated_text") is not None:
                actual_hash = hashlib.sha256(str(item["translated_text"]).encode("utf-8")).hexdigest()
                if item["translation_sha256"] != actual_hash:
                    raise ValueError("LỖI BẢN DỊCH: translation_sha256 không khớp nội dung.")
            blind = create_blind_sample(
                item,
                translated_text=item.get("translated_text"),
                translation_source_language=item.get("translation_source_language"),
                translation_tool=item.get("translation_tool"),
                translation_tool_version=item.get("translation_tool_version"),
            )
            clean_samples.append(blind.to_dict())
        else:
            raise TypeError(f"Mẫu không hợp lệ: kiểu {type(item)}")

    payload = {
        "version": version,
        "dataset_id": dataset_id,
        "dataset_type": dataset_type,
        "is_synthetic": is_synthetic,
        "purpose": purpose,
        "description": description or purpose,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_samples": len(clean_samples),
        "samples": clean_samples,
    }
    if sampling_plan_version:
        payload["sampling_plan_version"] = sampling_plan_version
    assert_no_label_leak(payload)

    with open(out_file, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return payload
