"""Module quản lý và xuất giao diện gán nhãn mù an toàn (Blind View) theo Anti-Leakage Protocol.

Quy chuẩn ARS bắt buộc:
1. Zero Data Peeking / Anti-Leakage:
   - Ẩn hoàn toàn nhãn gốc (source_label, label), mục tiêu (target), điểm mô hình (score),
     và kết quả của đánh giá viên còn lại.
   - Kiểm tra rò rỉ dữ liệu triệt để (assert_no_label_leak) trước khi xuất view.
2. Safety First:
   - Không bao giờ thực thi JavaScript hoặc render HTML sống của trang phishing.
   - Loại bỏ toàn bộ script, iframe, inline event handlers, form prefilled values.
3. Codebook v1 Compliance:
   - Chuẩn hóa cấu trúc bản ghi gán nhãn (AnnotationRecord) với đầy đủ taxonomy và trường bấm giờ seconds_spent.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Literal, Optional, Sequence, Set, Tuple
from urllib.parse import urljoin, urlparse

from phishing.preprocessing.html import clean_html
from phishing.preprocessing.urls import normalize_url


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


def assert_no_label_leak(data: Any, path: str = "root") -> None:
    """Kiểm tra đệ quy đảm bảo không có bất kỳ trường nhãn hoặc metadata cấm nào xuất hiện trong Blind View."""
    if isinstance(data, dict):
        for key, value in data.items():
            k_lower = str(key).lower()
            if k_lower in FORBIDDEN_LEAK_KEYS:
                raise ValueError(
                    f"RÒ RỈ DỮ LIỆU PHÁT HIỆN: Khóa cấm '{key}' xuất hiện tại vị trí '{path}.{key}'! "
                    f"Quy chuẩn Blind View cấm hoàn toàn nhãn nguồn, target hoặc điểm mô hình."
                )
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
        # Nối văn bản và chuẩn hóa khoảng trắng thừa
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


def extract_safe_view_content(html_content: str | None, page_url: str) -> Tuple[str, Dict[str, Any]]:
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

    # Tiền xử lý chuẩn qua clean_html để loại bỏ prefilled values và inline event handlers
    pre_cleaned = clean_html(html_content, page_url)
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

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "sample_id": self.sample_id,
            "url": self.url,
            "page_text": self.page_text,
            "structure_summary": self.structure_summary,
        }
        assert_no_label_leak(d)
        return d


def create_blind_sample(raw_sample: Dict[str, Any], sample_id: str | None = None) -> BlindSample:
    """Tạo mẫu BlindSample an toàn từ bản ghi thô, loại bỏ triệt để mọi nhãn nguồn."""
    sid = sample_id or raw_sample.get("sample_id") or raw_sample.get("id") or str(raw_sample.get("row_idx", "S000"))
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

    blind = BlindSample(
        sample_id=str(sid),
        url=norm_url,
        page_text=extracted_text,
        structure_summary=summary,
    )
    # Tự kiểm tra không rò rỉ nhãn
    assert_no_label_leak(blind.to_dict())
    return blind


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

    # Kiểm tra enum
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
        timestamp_utc=str(timestamp),
    )


def export_blind_view(
    samples: Sequence[BlindSample | Dict[str, Any]],
    output_path: Path | str,
    *,
    version: str = "1.0.0",
    description: str = "Gói dữ liệu Blind View phục vụ gán nhãn mù độc lập (Task LABEL-01)",
) -> Dict[str, Any]:
    """Xuất danh sách mẫu thành gói JSON Blind View an toàn cho A và B."""
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    clean_samples: List[Dict[str, Any]] = []
    for item in samples:
        if isinstance(item, BlindSample):
            clean_samples.append(item.to_dict())
        elif isinstance(item, dict):
            blind = create_blind_sample(item)
            clean_samples.append(blind.to_dict())
        else:
            raise TypeError(f"Mẫu không hợp lệ: kiểu {type(item)}")

    # Kiểm tra tổng thể toàn bộ gói dữ liệu không được rò rỉ nhãn
    payload = {
        "version": version,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "description": description,
        "total_samples": len(clean_samples),
        "samples": clean_samples,
    }
    assert_no_label_leak(payload)

    with open(out_file, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return payload
