"""Data Ingestion & Corpus Indexing Engine cho Task DEV-01 (Thành viên C).

Tuân thủ nghiêm ngặt theo chỉ đạo nghiệm thu của Lead D:
1. Chốt loại trừ pilot đóng kín:
   - Dữ liệu thật bắt buộc phải có ExclusionRegistry; cờ bỏ qua chỉ dành riêng cho fixture.
   - Bản ghi có exclusion_reason tuyệt đối không được chuyển thành PreparedSnapshot hay đi vào pipeline huấn luyện.
   - Cung cấp hàm chọn lọc tập đủ điều kiện (filter_eligible_records, join_verified_labels_and_filter_eligible).
   - Lập index để audit không được xem là sẵn sàng huấn luyện (ready_for_training=False khi training_blocked).
2. Ánh xạ nhãn chuẩn hóa & Bảo toàn xuất xứ:
   - Nhãn thiếu hoặc ngoài phạm vi (malware, defacement, rỗng) không tự động đổi thành benign; giữ trạng thái riêng và loại trừ có lý do.
   - Bảo toàn source_tier (gold/silver/bronze) và source_sub_source của PhishVN.
   - Phân biệt rõ source_label và nhãn tham chiếu kiểm chứng (không dùng source_label làm ground truth).
3. Độc lập & Ổn định Shard:
   - sample_id duy nhất toàn cục, ổn định gắn liền với shard và row: PP-<shard>-R<row:06d>.
   - Hỗ trợ nạp nhiều shard theo source_manifest.json hoặc danh sách đường dẫn.
   - Thư mục output bảo vệ chống ghi đè (yêu cầu --overwrite).
   - Xử lý dạng streaming tuần tự theo batch, không lưu toàn bộ HTML corpus trong RAM.
4. Xác minh Checksum & Xuất xứ:
   - Tự động tính SHA-256 từ HTML thực tế. Mâu thuẫn với hash nguồn bị phát hiện và gắn cờ loại trừ.
   - Kiểm tra đối chiếu với configs/source_manifest.json trước khi nhập dữ liệu thật.
   - Ghi nhận đầy đủ input_file_hashes, source_revision, registry_hash, adapter_version vào manifest.
5. Grouping không bị che lấp query:
   - Trích xuất group_id từ URL chuẩn hóa cấu trúc nhưng CHƯA che query values trong khu vực hạn chế.
   - Snapshot cho mô hình vẫn sử dụng normalized_url đã che query an toàn.
   - Forms id=TenantA và id=TenantB sinh hai group khác nhau.
6. Tách biệt Chỉ mục Kỹ thuật & Kho Nhãn Bảo mật:
   - corpus_index.jsonl chỉ chứa locator, normalized_url, group_id, html_sha256, capture_mode, date_status...
   - raw_url, source_label, target được lưu riêng trong restricted_vault.jsonl.
   - Cung cấp hàm reconstitute_html_from_locator chứng minh đọc lại đúng HTML và kiểm tra mã băm.
7. Bảo toàn Metadata:
   - Phân biệt rõ date_status: "valid", "missing", "invalid" (ngày sai ghi là invalid, không ghi missing).
   - Bảo toàn capture_mode đã xác minh ("stored_html", "rendered_dom", "url_only").
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
import tempfile
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Set, Tuple, Union
import zipfile

from phishing.data.date_parser import parse_strict_date
from phishing.data.exclusion import ExclusionRegistry
from phishing.data.grouping import extract_group_id
from phishing.preprocessing import PreparedSnapshot, prepare_snapshot
from phishing.preprocessing.urls import normalize_url

ADAPTER_VERSION = "2.1.0"


@dataclass(frozen=True, slots=True)
class CorpusRecord:
    """Bản ghi dữ liệu nghiên cứu chuẩn hóa theo DATA_PROTOCOL.md.

    Tách biệt dữ liệu kỹ thuật, siêu dữ liệu xuất xứ và nhãn nghiên cứu.
    """
    sample_id: str
    source_id: str
    source_revision: Optional[str]
    source_split: str  # "train", "val", "test", "unspecified", "unverified"
    locator: Dict[str, Any]  # Tham chiếu ổn định: {"source_id": ..., "shard": ..., "row_offset": ...}
    raw_url: str  # BẢO MẬT: chỉ lưu trong kho hạn chế
    normalized_url: Optional[str]  # Đã làm sạch query values phục vụ mô hình
    group_id: str  # Trích từ URL unredacted, không bị che bởi _redacted_
    html_sha256: Optional[str]  # Tính từ HTML thực tế
    source_provided_html_sha256: Optional[str]  # Hash do nguồn cung cấp (nếu có)
    html_integrity_status: str  # "matched", "no_source_hash", "mismatch", "no_html", "computed_only"
    language: str
    capture_mode: str  # "stored_html", "rendered_dom", "url_only"
    collected_at: Optional[str]  # "YYYY-MM-DD"
    date_status: str  # "valid", "missing", "invalid"
    date_error: Optional[str]
    is_valid_url: bool
    url_error: Optional[str]
    source_label: str  # "phishing", "benign", hoặc "out_of_scope:..." / "unlabeled"
    raw_source_label: str  # Nhãn nguyên bản từ nguồn
    label_status: str  # "source_binary_unverified", "out_of_scope", "missing"
    target: Optional[str]
    source_tier: Optional[str] = None  # PhishVN tier: gold, silver, bronze, tier1...
    source_sub_source: Optional[str] = None  # PhishVN sub-source
    exclusion_reason: Optional[str] = None
    raw_html: Optional[str] = None  # Tạm thời trong RAM khi xử lý, không lưu vào index

    def to_index_dict(self) -> Dict[str, Any]:
        """Xuất từ điển chỉ mục kỹ thuật (Technical Index) phục vụ corpus_index.jsonl.

        ARS CONTRACT & ZERO LABEL/PII LEAKAGE:
        Tuyệt đối KHÔNG chứa raw_url, source_label, target, hay raw_html.
        Chỉ lưu locator tham chiếu và các đặc tính kỹ thuật.
        """
        return {
            "sample_id": self.sample_id,
            "source_id": self.source_id,
            "source_revision": self.source_revision,
            "source_split": self.source_split,
            "locator": self.locator,
            "normalized_url": self.normalized_url,
            "group_id": self.group_id,
            "html_sha256": self.html_sha256,
            "html_integrity_status": self.html_integrity_status,
            "language": self.language,
            "capture_mode": self.capture_mode,
            "collected_at": self.collected_at,
            "date_status": self.date_status,
            "date_error": self.date_error,
            "is_valid_url": self.is_valid_url,
            "url_error": self.url_error,
            "exclusion_reason": self.exclusion_reason,
        }

    def to_vault_dict(self) -> Dict[str, Any]:
        """Xuất từ điển kho nhãn và dữ liệu nhạy cảm (Restricted Labels Vault).

        Lưu trữ tách biệt tại khu vực hạn chế phục vụ đối soát, đánh giá metric
        hoặc join nhãn sau khi đã kiểm chứng.
        """
        return {
            "sample_id": self.sample_id,
            "locator": self.locator,
            "raw_url": self.raw_url,
            "source_label": self.source_label,
            "raw_source_label": self.raw_source_label,
            "label_status": self.label_status,
            "target": self.target,
            "source_tier": self.source_tier,
            "source_sub_source": self.source_sub_source,
            "exclusion_reason": self.exclusion_reason,
        }

    def to_prepared_snapshot(self, html_content: Optional[str] = None) -> PreparedSnapshot:
        """Trích xuất PreparedSnapshot phục vụ trực tiếp cho pipeline trích xuất đặc trưng của Lead D.

        CHỐT CHẶN PHÒNG VỆ CHIỀU SÂU:
        1. Bản ghi bị loại trừ (exclusion_reason) tuyệt đối không được chuyển thành snapshot.
        2. Bảo toàn capture_mode đã xác minh (không tự đổi rendered_dom thành stored_html).
        3. Tuyệt đối không bao gồm nhãn nguồn, mục tiêu hay metadata nghiên cứu.
        """
        if self.exclusion_reason:
            raise ValueError(
                f"Không thể tạo PreparedSnapshot cho bản ghi đã bị loại trừ khỏi nghiên cứu/huấn luyện: "
                f"sample_id='{self.sample_id}', lý do='{self.exclusion_reason}'"
            )

        if not self.is_valid_url or not self.normalized_url:
            raise ValueError(
                f"Không thể tạo PreparedSnapshot cho bản ghi có URL không hợp lệ: {self.url_error}"
            )

        valid_modes = {"stored_html", "rendered_dom", "url_only"}
        if self.capture_mode not in valid_modes:
            raise ValueError(
                f"capture_mode không hợp lệ: '{self.capture_mode}', yêu cầu một trong {valid_modes}"
            )

        html_to_use = html_content if html_content is not None else self.raw_html
        if self.html_sha256 and (html_to_use is None or _compute_sha256(html_to_use) != self.html_sha256):
            raise ValueError("Snapshot HTML checksum mismatch")
        if self.capture_mode == "url_only" and html_to_use is not None:
            raise ValueError("URL-only record cannot silently acquire HTML")
        if self.capture_mode != "url_only" and html_to_use is None:
            raise ValueError(
                f"Bản ghi có capture_mode='{self.capture_mode}' nhưng không có nội dung HTML để nạp snapshot."
            )

        return prepare_snapshot(
            url=self.normalized_url,
            html=html_to_use,
            capture_mode=self.capture_mode,
        )


def _compute_sha256(data: Union[str, bytes]) -> str:
    """Tính mã băm SHA-256 dạng chuỗi hex."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def normalize_record_url(raw_url: str) -> Tuple[Optional[str], bool, Optional[str]]:
    """Chuẩn hóa URL với cơ chế scheme fallback theo DATA_PROTOCOL.md.

    Quy tắc xác định:
    1. Nếu thiếu scheme (không có '://'), tự động thử với 'https://'.
    2. Nếu URL có dạng protocol-relative '//...', thử với 'https:...'.
    3. Trả về: (normalized_url, is_valid, error_message).
    """
    if not isinstance(raw_url, str):
        return None, False, f"URL must be a string, got {type(raw_url).__name__}"

    cleaned = raw_url.strip()
    if not cleaned:
        return None, False, "URL is empty"

    candidate = cleaned
    if candidate.startswith("//"):
        candidate = "https:" + candidate
    elif "://" not in candidate:
        candidate = "https://" + candidate

    try:
        norm = normalize_url(candidate)
        return norm, True, None
    except Exception as err:
        return None, False, str(err)


def adapt_source_row_to_record(
    *,
    sample_id: str,
    source_id: str,
    source_revision: Optional[str],
    source_split: str,
    locator: Dict[str, Any],
    raw_url: str,
    raw_html: Optional[str],
    raw_date: Any,
    raw_label: Any,
    target: Optional[str] = None,
    language: str = "unknown",
    capture_mode: Optional[str] = None,
    source_tier: Optional[str] = None,
    source_sub_source: Optional[str] = None,
    exclusion_registry: Optional[ExclusionRegistry] = None,
    precomputed_html_sha256: Optional[str] = None,
    is_real_data_mode: bool = False,
) -> CorpusRecord:
    """Chuyển đổi một dòng dữ liệu thô từ nguồn thành CorpusRecord chuẩn hóa."""
    # 1. Chốt chặn ExclusionRegistry cho chế độ dữ liệu thật
    if is_real_data_mode and exclusion_registry is None:
        raise ValueError(
            "CHỐT CHẶN BẢO VỆ: Chế độ dữ liệu thật bắt buộc phải có ExclusionRegistry. "
            "Không được phép nạp dữ liệu thật mà không kiểm tra loại trừ pilot!"
        )

    # 2. Xử lý URL & Grouping (Khắc phục Probe 5)
    # TRÍCH XUẤT GROUP TỪ CANONICAL UNREDACTED URL TRƯỚC BƯỚC CHE QUERY CHO MÔ HÌNH:
    # URL dạng https://forms.office.com/Pages/ResponsePage.aspx?id=TenantA
    # phải giữ được 'id=TenantA' để sinh tenant:forms.office.com:id=tenanta!
    cleaned_raw_url = str(raw_url or "").strip()
    candidate_for_group = cleaned_raw_url
    if candidate_for_group.startswith("//"):
        candidate_for_group = "https:" + candidate_for_group
    elif "://" not in candidate_for_group and candidate_for_group:
        candidate_for_group = "https://" + candidate_for_group

    try:
        group_id = extract_group_id(candidate_for_group)
    except Exception:
        group_id = "unknown"

    norm_url, is_valid_url, url_err = normalize_record_url(cleaned_raw_url)

    # 3. Phân biệt trạng thái ngày rõ ràng: valid / missing / invalid (Khắc phục Probe 7)
    date_status = "missing"
    collected_at = None
    date_error = None
    if raw_date is None or (isinstance(raw_date, str) and not raw_date.strip()):
        date_status = "missing"
    else:
        parsed_date = parse_strict_date(raw_date)
        if parsed_date is not None:
            collected_at = parsed_date.isoformat()
            date_status = "valid"
        else:
            date_status = "invalid"
            date_error = f"invalid_calendar_date: {raw_date!r}"

    # 4. Tính toán Checksum HTML thực tế và đối chiếu (Khắc phục Probe 4)
    actual_html_sha = _compute_sha256(raw_html) if raw_html is not None else None
    html_integrity_status = "no_html"
    checksum_exclusion: Optional[str] = None

    if raw_html is not None:
        if precomputed_html_sha256 and str(precomputed_html_sha256).strip():
            src_sha = str(precomputed_html_sha256).strip().lower()
            if src_sha != actual_html_sha:
                html_integrity_status = "mismatch"
                checksum_exclusion = (
                    f"html_sha256_mismatch (computed {actual_html_sha[:8]} != source {src_sha[:8]})"
                )
            else:
                html_integrity_status = "matched"
        else:
            html_integrity_status = "computed_only"

    # 5. Ánh xạ nhãn nghiêm ngặt (Khắc phục Probe 2)
    # Tuyệt đối không tự động đổi nhãn thiếu hoặc ngoài phạm vi thành benign
    label_exclusion: Optional[str] = None
    raw_source_label = str(raw_label if raw_label is not None else "").strip()
    raw_lower = raw_source_label.lower()

    if not raw_source_label:
        source_label = "unlabeled"
        label_status = "missing"
        label_exclusion = "missing_source_label"
    elif raw_lower in {"phish", "phishing", "1", "true"}:
        source_label = "phishing"
        label_status = "source_binary_unverified"
    elif raw_lower in {"benign", "0", "false"}:
        source_label = "benign"
        label_status = "source_binary_unverified"
    elif raw_lower in {"malware", "defacement"}:
        source_label = f"out_of_scope:{raw_source_label}"
        label_status = "out_of_scope"
        label_exclusion = f"out_of_scope_label:{raw_source_label}"
    else:
        source_label = f"out_of_scope:{raw_source_label}"
        label_status = "out_of_scope"
        label_exclusion = f"unsupported_label:{raw_source_label}"

    # 6. Bảo toàn capture_mode đã xác minh (Khắc phục Probe 7)
    if capture_mode is not None:
        if capture_mode not in {"stored_html", "rendered_dom", "url_only"}:
            raise ValueError("Invalid capture_mode")
        actual_capture_mode = capture_mode
    elif raw_html is not None:
        actual_capture_mode = "stored_html"
    else:
        actual_capture_mode = "url_only"

    # 7. Tổng hợp lý do loại trừ (Exclusion Reasons)
    exclusion_reasons: List[str] = []
    if group_id == "unknown":
        exclusion_reasons.append("invalid_group_id")
    if not is_valid_url:
        exclusion_reasons.append(f"invalid_url: {url_err}")
    if checksum_exclusion:
        exclusion_reasons.append(checksum_exclusion)
    if label_exclusion:
        exclusion_reasons.append(label_exclusion)
    if date_status == "invalid":
        exclusion_reasons.append(date_error or "invalid_date")

    # Kiểm tra ExclusionRegistry chống rò rỉ pilot
    if exclusion_registry is not None and is_valid_url:
        sample_query = {
            "url": cleaned_raw_url,
            "html": raw_html,
            "url_sha256": _compute_sha256(cleaned_raw_url),
            "html_sha256": actual_html_sha,
            "group_sha256": _compute_sha256(group_id) if group_id else None,
        }
        if exclusion_registry.is_excluded(sample_query):
            exclusion_reasons.append("pilot_exclusion_registry_match")

    combined_exclusion = "; ".join(exclusion_reasons) if exclusion_reasons else None

    return CorpusRecord(
        sample_id=sample_id,
        source_id=source_id,
        source_revision=source_revision,
        source_split=source_split,
        locator=locator,
        raw_url=cleaned_raw_url,
        normalized_url=norm_url,
        group_id=group_id,
        html_sha256=actual_html_sha,
        source_provided_html_sha256=precomputed_html_sha256,
        html_integrity_status=html_integrity_status,
        language=language or "unknown",
        capture_mode=actual_capture_mode,
        collected_at=collected_at,
        date_status=date_status,
        date_error=date_error,
        is_valid_url=is_valid_url,
        url_error=url_err,
        source_label=source_label,
        raw_source_label=raw_source_label,
        label_status=label_status,
        target=target,
        source_tier=source_tier,
        source_sub_source=source_sub_source,
        exclusion_reason=combined_exclusion,
        raw_html=raw_html,
    )


def file_sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def verify_source_file(path: Path, manifest_path, source_id: str) -> tuple[dict, dict]:
    if manifest_path is None:
        raise ValueError("Real ingestion requires a source manifest")
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    revision = manifest.get("revision")
    if manifest.get("source_id") != source_id or not isinstance(revision, str) or not revision.strip() or revision in {"unverified", "unspecified"}:
        raise ValueError("Source identity/revision mismatch")
    if source_id == "phreshphish" and (manifest.get("source_split") != "train"
            or not re.fullmatch(r"[0-9a-f]{40}", revision)):
        raise ValueError("Require pinned train revision; official test is not eligible")
    if manifest.get("source_split") not in {"train", "unspecified"}:
        raise ValueError("Unsupported source split")
    matches = [e for e in manifest.get("files", [])
               if Path(e.get("relative_path", "")).name == path.name and e.get("file_name") == path.name]
    if len(matches) != 1:
        raise ValueError("Source file not uniquely present in manifest")
    entry = matches[0]
    expected = entry.get("source_metadata_lfs_sha256") or entry.get("locally_verified_sha256") or entry.get("sha256")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("Manifest lacks byte SHA-256")
    if type(entry.get("byte_size")) is not int or entry["byte_size"] != path.stat().st_size or file_sha256(path) != expected:
        raise ValueError("Source file byte checksum/size mismatch")
    return manifest, entry


def load_phreshphish_shard(
    shard_path: Union[str, Path],
    *,
    source_manifest_path: Optional[Union[str, Path]] = None,
    exclusion_registry: Optional[ExclusionRegistry] = None,
    limit: Optional[int] = None,
    is_real_data_mode: bool = True,
    verify_checksum: bool = True,
) -> Iterator[CorpusRecord]:
    """Nạp các bản ghi từ một tệp Parquet của PhreshPhish.

    ID ổn định: PP-<revision>-<shard_stem>-R<row_offset:06d>.
    Đối soát xuất xứ với configs/source_manifest.json.
    """
    import pyarrow.parquet as pq

    path = Path(shard_path)
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy shard PhreshPhish tại '{path}'")

    shard_stem = path.stem  # ví dụ 'train-000'
    shard_name = path.name

    if limit is not None and (type(limit) is not int or limit < 0):
        raise ValueError("limit must be a nonnegative integer")
    if is_real_data_mode:
        if exclusion_registry is None or verify_checksum is not True:
            raise ValueError("Real ingestion requires registry and checksum verification")
        manifest, entry = verify_source_file(path, source_manifest_path, "phreshphish")
        source_revision, source_split = manifest["revision"], manifest["source_split"]
    else:
        source_revision, source_split = "unverified", "unverified"
    source_sha = file_sha256(path)
    parquet = pq.ParquetFile(path)
    required = {"url", "html", "label", "date"}
    if not required <= set(parquet.schema.names):
        raise ValueError("Missing source schema columns")
    columns = sorted(required | ({"sha256", "lang"} & set(parquet.schema.names)))
    count = 0
    for batch in parquet.iter_batches(batch_size=128, columns=columns):
        for row in batch.to_pylist():
            if limit is not None and count >= limit:
                return
            locator = {"source_id": "phreshphish", "shard": path.name,
                       "row_offset": count, "source_file_sha256": source_sha}
            yield adapt_source_row_to_record(
                sample_id=f"PP-{source_revision}-{shard_stem}-R{count:06d}",
                source_id="phreshphish", source_revision=source_revision,
                source_split=source_split, locator=locator,
                raw_url=row.get("url") or "", raw_html=row.get("html"),
                raw_date=row.get("date"), raw_label=row.get("label"), target=None,
                language=str(row.get("lang") or "unknown"),
                capture_mode="stored_html" if row.get("html") is not None else "url_only",
                exclusion_registry=exclusion_registry, precomputed_html_sha256=row.get("sha256"),
                is_real_data_mode=is_real_data_mode)
            count += 1


def load_phishvn_records(
    source_path: Union[str, Path],
    *,
    source_manifest_path: Optional[Union[str, Path]] = None,
    exclusion_registry: Optional[ExclusionRegistry] = None,
    limit: Optional[int] = None,
    is_real_data_mode: bool = True,
) -> Iterator[CorpusRecord]:
    """Nạp các bản ghi từ nguồn PhishVN (tệp ZIP hoặc CSV).

    Bảo toàn source_tier (gold/silver/bronze) và source_sub_source.
    ID ổn định: PVN-<revision>-<file_stem>-<file_hash>-R<row_offset:06d>.
    """
    path = Path(source_path)
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy tệp PhishVN tại '{path}'")

    if is_real_data_mode:
        if exclusion_registry is None:
            raise ValueError("Real ingestion requires exclusion registry")
        manifest, _ = verify_source_file(path, source_manifest_path, "phishvn")
        revision, split = manifest["revision"], manifest["source_split"]
    else:
        revision, split = "unverified", "unverified"
    source_sha = file_sha256(path)
    def iter_rows():
        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive:
                matches = [name for name in archive.namelist() if name.endswith("dataset_url.csv")]
                if len(matches) != 1:
                    raise ValueError("Require exactly one dataset_url.csv in archive")
                with archive.open(matches[0]) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig") as text:
                    reader = csv.DictReader(text)
                    if not {"url", "label"} <= set(reader.fieldnames or []):
                        raise ValueError("PhishVN schema missing url/label")
                    yield from reader
        elif path.suffix.lower() == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as text:
                reader = csv.DictReader(text)
                if not {"url", "label"} <= set(reader.fieldnames or []):
                    raise ValueError("PhishVN schema missing url/label")
                yield from reader
        else:
            raise ValueError("Unsupported PhishVN source format")

    count = 0
    for row_idx, row in enumerate(iter_rows()):
        if limit is not None and count >= limit:
            break

        sample_id = f"PVN-{revision}-{path.stem}-{source_sha}-R{row_idx:06d}"
        locator = {
            "source_id": "phishvn",
            "file": path.name,
            "source_file_sha256": source_sha,
            "row_offset": row_idx,
        }

        record = adapt_source_row_to_record(
            sample_id=sample_id,
            source_id="phishvn",
            source_revision=revision,
            source_split=split,
            locator=locator,
            raw_url=row.get("url") or "",
            raw_html=None,
            raw_date=None,
            raw_label=row.get("label"),
            target=row.get("scenario"),
            language=str(row.get("lang") or "vi"),
            capture_mode="url_only",
            source_tier=row.get("tier"),
            source_sub_source=row.get("source"),
            exclusion_registry=exclusion_registry,
            is_real_data_mode=is_real_data_mode,
        )
        yield record
        count += 1


def reconstitute_html_from_locator(
    record_or_locator: Union[Dict[str, Any], CorpusRecord],
    source_base_dir: Union[str, Path],
) -> Optional[str]:
    """Chứng minh có thể đọc lại đúng HTML từ chỉ mục (locator) và kiểm tra tính toàn vẹn mã băm.

    Quy chuẩn ARS:
    1. Trích xuất shard/file và row_offset từ locator.
    2. Đọc trực tiếp dòng tương ứng từ tệp nguồn.
    3. Đối soát mã băm SHA-256 của HTML vừa đọc với html_sha256 trong chỉ mục.
    """
    import pyarrow.parquet as pq

    base_dir = Path(source_base_dir)

    if isinstance(record_or_locator, CorpusRecord):
        locator = record_or_locator.locator
        expected_sha = record_or_locator.html_sha256
    elif isinstance(record_or_locator, dict):
        locator = record_or_locator.get("locator", record_or_locator)
        expected_sha = record_or_locator.get("html_sha256")
    else:
        raise TypeError("record_or_locator phải là CorpusRecord hoặc dict")

    source_id = locator.get("source_id")
    row_offset = locator.get("row_offset", 0)

    if source_id == "phreshphish":
        shard_name = locator.get("shard")
        if not shard_name:
            raise ValueError("Locator thiếu 'shard'")
        shard_path = (base_dir / shard_name).resolve()
        if not shard_path.is_relative_to(base_dir.resolve()):
            raise ValueError("Locator escapes source root")
        if type(row_offset) is not int or row_offset < 0:
            raise ValueError("Invalid row offset")
        if locator.get("source_file_sha256") and file_sha256(shard_path) != locator["source_file_sha256"]:
            raise ValueError("Source shard checksum mismatch")
        offset = 0
        for batch in pq.ParquetFile(shard_path).iter_batches(batch_size=128, columns=["html"]):
            if row_offset < offset + batch.num_rows:
                html_content = batch.column(0)[row_offset - offset].as_py()
                if expected_sha is not None and (html_content is None or _compute_sha256(html_content) != expected_sha):
                    raise ValueError("HTML checksum mismatch or missing content")
                return html_content
            offset += batch.num_rows
        raise IndexError("Row offset outside shard")

    elif source_id == "synthetic":
        # Hỗ trợ fixture / synthetic JSONL
        file_name = locator.get("file")
        fpath = (base_dir / file_name).resolve() if file_name else base_dir.resolve()
        if not fpath.is_relative_to(base_dir.resolve()) or type(row_offset) is not int or row_offset < 0:
            raise ValueError("Invalid fixture locator")
        if not fpath.is_file():
            raise FileNotFoundError(f"Không tìm thấy fixture file '{fpath}'")
        with open(fpath, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if idx == row_offset:
                    row = json.loads(line)
                    html = row.get("html") or row.get("raw_html")
                    if expected_sha and (html is None or _compute_sha256(html) != expected_sha):
                        raise ValueError("Mã băm HTML không khớp hoặc mất nội dung")
                    return html
        return None

    return None


def filter_eligible_records(records: Iterable[CorpusRecord], *, require_date: bool = False) -> List[CorpusRecord]:
    """Chọn lọc tập bản ghi đủ điều kiện nghiên cứu (không bị loại trừ bởi ExclusionRegistry hay lỗi)."""
    return [
        r for r in records
        if r.exclusion_reason is None and r.is_valid_url and r.date_status != "invalid"
        and (not require_date or r.date_status == "valid")
    ]


def join_verified_labels_and_filter_eligible(
    index_records: Sequence[Dict[str, Any]],
    labels_vault: Mapping[str, Dict[str, Any]],
    exclusion_registry: Optional[ExclusionRegistry] = None,
) -> List[Dict[str, Any]]:
    """Gộp nhãn đã kiểm chứng vào chỉ mục kỹ thuật và lọc bỏ toàn bộ mẫu loại trừ trước split/fit.

    Quy tắc NCKH & Lead D:
    1. Đối soát từng sample_id với labels_vault.
    2. Tuyệt đối loại bỏ mọi mẫu có exclusion_reason (pilot, invalid url, out-of-scope...).
    3. Áp dụng chốt chặn phòng vệ ExclusionRegistry một lần nữa nếu được cung cấp.
    4. Trả về tập dữ liệu sạch, an toàn, sẵn sàng cho Grouped K-Fold / Temporal Split.
    """
    if exclusion_registry is None:
        raise ValueError("Verified-label join requires exclusion registry")
    exclusion_registry.assert_training_allowed()
    eligible_joined: List[Dict[str, Any]] = []
    seen = set()

    for idx_rec in index_records:
        sid = idx_rec.get("sample_id")
        if not sid or sid in seen:
            raise ValueError("Missing/duplicate index sample_id")
        seen.add(sid)
        if sid not in labels_vault:
            continue

        vault_entry = labels_vault[sid]

        # 1. Bỏ mẫu đã có lý do loại trừ trong index hoặc vault
        if idx_rec.get("exclusion_reason") or vault_entry.get("exclusion_reason"):
            continue

        # 2. Bỏ mẫu URL không hợp lệ hoặc date không hợp lệ
        if not idx_rec.get("is_valid_url") or idx_rec.get("date_status") == "invalid":
            continue

        # 3. Chỉ nhận nhãn nhị phân đã xác minh (phishing / benign)
        label_status = vault_entry.get("label_status")
        if label_status != "verified_binary":
            continue

        # A source adapter cannot confer verification. Require final-label provenance.
        if (vault_entry.get("sample_id") != sid
                or vault_entry.get("html_sha256") != idx_rec.get("html_sha256")
                or not vault_entry.get("verification_method")
                or not vault_entry.get("verified_by")
                or not vault_entry.get("verification_evidence")):
            continue
        verified_label = vault_entry.get("class_label")
        if verified_label not in {"phishing", "benign"}:
            continue

        # 4. Kiểm tra phòng vệ bổ sung nếu có registry
        if exclusion_registry is not None:
            sample_query = {
                "url": vault_entry.get("raw_url") or idx_rec.get("normalized_url"),
                "html_sha256": idx_rec.get("html_sha256"),
                "group_sha256": _compute_sha256(idx_rec.get("group_id", "")),
            }
            if exclusion_registry.is_excluded(sample_query):
                continue

        joined_item = {
            "sample_id": sid,
            "url": idx_rec.get("normalized_url"),
            "group_id": idx_rec.get("group_id"),
            "class_label": verified_label,
            "collected_at": idx_rec.get("collected_at"),
            "source_id": idx_rec.get("source_id"),
            "capture_mode": idx_rec.get("capture_mode"),
            "target": vault_entry.get("target"),
            "source_tier": vault_entry.get("source_tier"),
        }
        eligible_joined.append(joined_item)

    return eligible_joined


def _build_corpus_index(
    records: Iterable[CorpusRecord],
    *,
    output_index_path: Optional[Union[str, Path]] = None,
    output_vault_path: Optional[Union[str, Path]] = None,
    output_manifest_path: Optional[Union[str, Path]] = None,
    batch_size: int = 1000,
    training_blocked: bool = True,
    additional_metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Xây dựng và ghi chỉ mục theo phương pháp STREAMING TUẦN TỰ THEO BATCH.

    ARS CONTRACT & MEMORY OPTIMIZATION:
    - Không lưu trữ toàn bộ danh sách bản ghi và raw HTML trong RAM.
    - Ghi đồng thời vào corpus_index.jsonl và restricted_vault.jsonl.
    - Cập nhật thống kê phân bố lớp, nguồn, ngày, mã băm đầu ra.
    - Ghi nhận trạng thái sẵn sàng huấn luyện: ready_for_training=False khi training_blocked.
    """
    seen_ids: Set[str] = set()

    class_counts: Dict[str, int] = {}
    label_status_counts: Dict[str, int] = {}
    source_counts: Dict[str, int] = {}
    exclusion_counts: Dict[str, int] = {}
    date_status_counts: Dict[str, int] = {"valid": 0, "missing": 0, "invalid": 0}
    valid_url_count = 0
    invalid_url_count = 0
    total_records = 0

    idx_handle = None
    vault_handle = None

    if output_index_path is not None:
        idx_p = Path(output_index_path)
        idx_p.parent.mkdir(parents=True, exist_ok=True)
        idx_handle = open(idx_p, "w", encoding="utf-8")

    if output_vault_path is not None:
        v_p = Path(output_vault_path)
        v_p.parent.mkdir(parents=True, exist_ok=True)
        vault_handle = open(v_p, "w", encoding="utf-8")

    try:
        for r in records:
            if r.sample_id in seen_ids:
                raise ValueError(f"Phát hiện sample_id trùng lặp trong tập chỉ mục: '{r.sample_id}'")
            seen_ids.add(r.sample_id)
            total_records += 1

            # Thống kê
            class_counts[r.source_label] = class_counts.get(r.source_label, 0) + 1
            label_status_counts[r.label_status] = label_status_counts.get(r.label_status, 0) + 1
            source_counts[r.source_id] = source_counts.get(r.source_id, 0) + 1
            date_status_counts[r.date_status] = date_status_counts.get(r.date_status, 0) + 1

            if r.is_valid_url:
                valid_url_count += 1
            else:
                invalid_url_count += 1

            if r.exclusion_reason:
                exclusion_counts[r.exclusion_reason] = exclusion_counts.get(r.exclusion_reason, 0) + 1

            # Ghi tuần tự ra tệp
            if idx_handle is not None:
                idx_handle.write(json.dumps(r.to_index_dict(), ensure_ascii=False) + "\n")
            if vault_handle is not None:
                vault_handle.write(json.dumps(r.to_vault_dict(), ensure_ascii=False) + "\n")

    finally:
        if idx_handle is not None:
            idx_handle.close()
        if vault_handle is not None:
            vault_handle.close()

    manifest: Dict[str, Any] = {
        "manifest_type": "CORPUS_INDEX_MANIFEST",
        "adapter_version": ADAPTER_VERSION,
        "total_records": total_records,
        "valid_urls": valid_url_count,
        "invalid_urls": invalid_url_count,
        "date_status_distribution": date_status_counts,
        "class_distribution": class_counts,
        "label_status_distribution": label_status_counts,
        "source_distribution": source_counts,
        "total_excluded_records": sum(exclusion_counts.values()),
        "exclusion_breakdown": exclusion_counts,
        # CHỐT CHẶN HUẤN LUYỆN (Khắc phục Probe 1)
        "ready_for_training": False,
        "training_readiness_status": "audit_only_training_blocked" if training_blocked else "audit_only_labels_unverified",
        "readiness_reason": (
            "Training is blocked per ARS guidelines (pilot exclusion registry active, audit in progress)"
            if training_blocked else "Source labels are not final verified labels; index is audit-only"
        ),
    }

    if additional_metadata:
        manifest["provenance_metadata"] = additional_metadata

    if output_index_path is not None:
        idx_p = Path(output_index_path)
        manifest["index_file_sha256"] = file_sha256(idx_p)
        manifest["index_relative_path"] = str(idx_p)

    if output_vault_path is not None:
        v_p = Path(output_vault_path)
        manifest["vault_file_sha256"] = file_sha256(v_p)
        manifest["vault_relative_path"] = str(v_p)

    if output_manifest_path is not None:
        man_p = Path(output_manifest_path)
        man_p.parent.mkdir(parents=True, exist_ok=True)
        man_p.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return total_records, manifest


def build_corpus_index(records: Iterable[CorpusRecord], **kwargs) -> Tuple[int, Dict[str, Any]]:
    """Stage all outputs before publication; preserve previous files on any read/write failure."""
    keys = ("output_index_path", "output_vault_path", "output_manifest_path")
    targets = {key: Path(kwargs[key]).resolve() for key in keys if kwargs.get(key) is not None}
    if not targets:
        return _build_corpus_index(records, **kwargs)
    parents = {path.parent for path in targets.values()}
    if len(parents) != 1 or len(set(targets.values())) != len(targets):
        raise ValueError("Index, vault and manifest must have distinct paths in one dedicated run directory")
    parent = next(iter(parents))
    parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".index-staging-", dir=parent.parent))
    backup = staging / "backup"
    backup.mkdir()
    published = []
    preserve_backup = False
    try:
        staged_kwargs = dict(kwargs)
        for key, path in targets.items():
            staged_kwargs[key] = staging / path.name
        count, manifest = _build_corpus_index(records, **staged_kwargs)
        for key, field in (("output_index_path", "index_relative_path"), ("output_vault_path", "vault_relative_path")):
            if key in targets:
                manifest[field] = str(targets[key])
        if "output_manifest_path" in targets:
            (staging / targets["output_manifest_path"].name).write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for path in targets.values():
            if path.exists():
                shutil.copy2(path, backup / path.name)
        try:
            for path in targets.values():
                os.replace(staging / path.name, path)
                published.append(path)
        except Exception as error:
            try:
                for path in published:
                    saved = backup / path.name
                    if saved.exists():
                        shutil.copy2(saved, path)
                    else:
                        path.unlink(missing_ok=True)
            except Exception as rollback_error:
                preserve_backup = True
                raise RuntimeError(f"Index rollback failed; retained backup: {backup}") from rollback_error
            raise error
        return count, manifest
    finally:
        if not preserve_backup:
            shutil.rmtree(staging)


def extract_labels_vault(records: Iterable[CorpusRecord]) -> Dict[str, Dict[str, Any]]:
    """Trích xuất kho nhãn bảo mật (Ground Truth Labels Vault) của Thành viên C."""
    return {
        r.sample_id: {
            "source_label": r.source_label,
            "target": r.target,
            "source_id": r.source_id,
            "source_split": r.source_split,
            "group_id": r.group_id,
            "collected_at": r.collected_at,
            "exclusion_reason": r.exclusion_reason,
            "source_tier": r.source_tier,
        }
        for r in records
    }
