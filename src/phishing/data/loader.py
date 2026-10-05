"""Data Ingestion & Corpus Indexing Engine cho Task DEV-01 (Thành viên C).

Tuân thủ nghiêm ngặt:
1. DATA_PROTOCOL.md: Chuẩn hóa 11 trường bản ghi nghiên cứu, lưu index và nhãn tách biệt.
2. Anti-Leakage Protocol: Tách biệt tuyệt đối PreparedSnapshot (chỉ chứa URL + HTML đã làm sạch)
   khỏi nhãn nguồn (source_label), mục tiêu (target), split hay metadata.
3. Defense-in-depth: Tích hợp chốt chặn ExclusionRegistry, tự động phát hiện và loại trừ mẫu pilot.
4. Xử lý an toàn: Không thực thi HTML, không gọi mạng (offline PSL), chuẩn hóa URL có scheme fallback xác định.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union
import zipfile

from phishing.data.date_parser import parse_strict_date
from phishing.data.exclusion import ExclusionRegistry
from phishing.data.grouping import extract_group_id
from phishing.preprocessing import PreparedSnapshot, prepare_snapshot
from phishing.preprocessing.urls import normalize_url


@dataclass(frozen=True, slots=True)
class CorpusRecord:
    """Bản ghi dữ liệu nghiên cứu chuẩn hóa theo DATA_PROTOCOL.md.
    
    Tách biệt dữ liệu kỹ thuật, siêu dữ liệu xuất xứ và nhãn nghiên cứu.
    """
    sample_id: str
    source_id: str
    source_revision: Optional[str]
    source_split: str  # "train", "val", "test", "unspecified"
    collected_at: Optional[str]  # "YYYY-MM-DD" hoặc None
    raw_url: str
    normalized_url: Optional[str]
    html_sha256: Optional[str]
    language: str
    capture_mode: str  # "stored_html", "url_only"
    source_label: str  # "phishing", "benign", "unknown"
    target: Optional[str]
    group_id: str
    exclusion_reason: Optional[str] = None
    is_valid_url: bool = True
    url_error: Optional[str] = None
    raw_html: Optional[str] = None  # Có thể lưu trong bộ nhớ khi streaming, bỏ qua khi ghi index

    def to_index_dict(self) -> Dict[str, Any]:
        """Xuất từ điển chỉ mục (index) phục vụ lưu trữ corpus_index.jsonl.
        
        Tuyệt đối không lưu raw_html trong index để bảo đảm hiệu năng và tách bạch lưu trữ.
        """
        return {
            "sample_id": self.sample_id,
            "source_id": self.source_id,
            "source_revision": self.source_revision,
            "source_split": self.source_split,
            "collected_at": self.collected_at,
            "date_status": "valid" if self.collected_at else "missing",
            "raw_url": self.raw_url,
            "normalized_url": self.normalized_url,
            "html_sha256": self.html_sha256,
            "language": self.language,
            "capture_mode": self.capture_mode,
            "source_label": self.source_label,
            "target": self.target,
            "group_id": self.group_id,
            "is_valid_url": self.is_valid_url,
            "url_error": self.url_error,
            "exclusion_reason": self.exclusion_reason,
        }

    def to_prepared_snapshot(self, html_content: Optional[str] = None) -> PreparedSnapshot:
        """Trích xuất PreparedSnapshot phục vụ trực tiếp cho pipeline trích xuất đặc trưng của Lead D.
        
        ANTI-LEAKAGE GUARANTEE:
        Chỉ trả về URL chuẩn hóa và HTML đã làm sạch. Tuyệt đối không bao gồm:
        - source_label, target
        - collected_at, source_split, group_id
        - exclusion_reason
        """
        if not self.is_valid_url or not self.normalized_url:
            raise ValueError(f"Không thể tạo PreparedSnapshot cho bản ghi có URL không hợp lệ: {self.url_error}")
        
        html_to_use = html_content if html_content is not None else self.raw_html
        mode = "stored_html" if html_to_use is not None else "url_only"
        
        return prepare_snapshot(
            url=self.normalized_url,
            html=html_to_use,
            capture_mode=mode,
        )


def _compute_sha256(data: Union[str, bytes]) -> str:
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
        return None, False, "URL must be a string"
    
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
    raw_url: str,
    raw_html: Optional[str],
    raw_date: Any,
    source_label: str,
    target: Optional[str] = None,
    language: str = "unknown",
    capture_mode: Optional[str] = None,
    exclusion_registry: Optional[ExclusionRegistry] = None,
    precomputed_html_sha256: Optional[str] = None,
) -> CorpusRecord:
    """Chuyển đổi một dòng dữ liệu thô từ nguồn thành CorpusRecord chuẩn hóa."""
    norm_url, is_valid, url_err = normalize_record_url(raw_url)
    
    # 1. Parse date nghiêm ngặt
    parsed_date = parse_strict_date(raw_date)
    collected_at = parsed_date.isoformat() if parsed_date else None
    
    # 2. Tính hash HTML
    html_sha = precomputed_html_sha256
    if html_sha is None and raw_html is not None:
        html_sha = _compute_sha256(raw_html)
        
    # 3. Trích xuất group_id (eTLD+1 + tenant) bảo thủ
    url_for_group = norm_url or raw_url
    try:
        group_id = extract_group_id(url_for_group)
    except Exception:
        # Nếu URL quá dị biệt không parse được group, phân loại nhóm lỗi
        group_id = "unknown_domain"
        
    # 4. Xác định capture_mode
    actual_capture_mode = capture_mode or ("stored_html" if raw_html is not None else "url_only")
    
    # 5. Kiểm tra ExclusionRegistry chống rò rỉ pilot
    exclusion_reason = None
    if not is_valid:
        exclusion_reason = f"invalid_url: {url_err}"
    elif exclusion_registry is not None:
        sample_query = {
            "url": raw_url,
            "html": raw_html,
            "url_sha256": _compute_sha256(raw_url),
            "html_sha256": html_sha,
            "group_sha256": _compute_sha256(group_id) if group_id else None,
        }
        if exclusion_registry.is_excluded(sample_query):
            exclusion_reason = "pilot_exclusion_registry_match"
            
    return CorpusRecord(
        sample_id=sample_id,
        source_id=source_id,
        source_revision=source_revision,
        source_split=source_split,
        collected_at=collected_at,
        raw_url=raw_url,
        normalized_url=norm_url,
        html_sha256=html_sha,
        language=language or "unknown",
        capture_mode=actual_capture_mode,
        source_label=source_label,
        target=target,
        group_id=group_id,
        exclusion_reason=exclusion_reason,
        is_valid_url=is_valid,
        url_error=url_err,
        raw_html=raw_html,
    )


def load_phreshphish_shard(
    shard_path: Union[str, Path],
    *,
    source_revision: Optional[str] = "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a",
    id_prefix: str = "PP-TRAIN",
    start_index: int = 1,
    exclusion_registry: Optional[ExclusionRegistry] = None,
    limit: Optional[int] = None,
) -> Iterator[CorpusRecord]:
    """Nạp các bản ghi từ một tệp Parquet của PhreshPhish.
    
    Cột nguồn PhreshPhish: url, html, label, sha256, date, lang.
    """
    import pyarrow.parquet as pq

    path = Path(shard_path)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy shard PhreshPhish tại '{path}'")
        
    table = pq.read_table(
        path,
        columns=["url", "html", "label", "sha256", "date", "lang"],
    )
    
    count = 0
    for idx, row in enumerate(table.to_pylist(), start=start_index):
        if limit is not None and count >= limit:
            break
            
        sample_id = f"{id_prefix}-{idx:06d}"
        
        # Nhãn PhreshPhish: 'phish' -> 'phishing', 'benign' -> 'benign'
        raw_label = str(row.get("label") or "").strip().lower()
        std_label = "phishing" if raw_label in {"phish", "phishing", "1", "true"} else "benign"
        
        record = adapt_source_row_to_record(
            sample_id=sample_id,
            source_id="phreshphish",
            source_revision=source_revision,
            source_split="train",
            raw_url=row.get("url") or "",
            raw_html=row.get("html"),
            raw_date=row.get("date"),
            source_label=std_label,
            target=None,
            language=str(row.get("lang") or "unknown"),
            capture_mode="stored_html" if row.get("html") is not None else "url_only",
            exclusion_registry=exclusion_registry,
            precomputed_html_sha256=row.get("sha256"),
        )
        yield record
        count += 1


def load_phishvn_records(
    source_path: Union[str, Path],
    *,
    id_prefix: str = "PVN",
    start_index: int = 1,
    exclusion_registry: Optional[ExclusionRegistry] = None,
    limit: Optional[int] = None,
) -> Iterator[CorpusRecord]:
    """Nạp các bản ghi từ nguồn PhishVN (tệp ZIP hoặc CSV).
    
    Cột nguồn PhishVN: url, label, source, tier, scenario, split, lang, domain.
    """
    path = Path(source_path)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy tệp PhishVN tại '{path}'")
        
    csv_bytes = b""
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            # Tìm file CSV chứa dataset
            candidate_files = [f for f in archive.namelist() if f.endswith("dataset_url.csv")]
            if not candidate_files:
                raise ValueError("Không tìm thấy tệp 'dataset_url.csv' trong kho lưu trữ ZIP PhishVN.")
            csv_bytes = archive.read(candidate_files[0])
    elif path.suffix.lower() == ".csv":
        csv_bytes = path.read_bytes()
    else:
        raise ValueError(f"Định dạng nguồn PhishVN không được hỗ trợ: '{path.suffix}'")
        
    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig")))
    
    count = 0
    for idx, row in enumerate(reader, start=start_index):
        if limit is not None and count >= limit:
            break
            
        sample_id = f"{id_prefix}-{idx:06d}"
        raw_label = str(row.get("label") or "").strip().lower()
        std_label = "phishing" if raw_label in {"phishing", "phish", "1"} else "benign"
        
        record = adapt_source_row_to_record(
            sample_id=sample_id,
            source_id="phishvn",
            source_revision="v3.1.0_open",
            source_split=row.get("split") or "train",
            raw_url=row.get("url") or "",
            raw_html=None,  # PhishVN URL dataset chỉ có URL, không có HTML trực tiếp trong CSV
            raw_date=None,
            source_label=std_label,
            target=row.get("scenario"),  # Kịch bản / nhóm ngành
            language=str(row.get("lang") or "vi"),
            capture_mode="url_only",
            exclusion_registry=exclusion_registry,
        )
        yield record
        count += 1


def build_corpus_index(
    records: Iterable[CorpusRecord],
    *,
    output_index_path: Optional[Union[str, Path]] = None,
    output_manifest_path: Optional[Union[str, Path]] = None,
) -> Tuple[List[CorpusRecord], Dict[str, Any]]:
    """Xây dựng và tùy chọn xuất tệp chỉ mục `corpus_index.jsonl` và `index_manifest.json`.
    
    Kiểm tra tính toàn vẹn, tính duy nhất của sample_id, và thống kê tổng hợp.
    """
    indexed_records: List[CorpusRecord] = []
    seen_ids: set[str] = set()
    
    class_counts: Dict[str, int] = {}
    source_counts: Dict[str, int] = {}
    exclusion_counts: Dict[str, int] = {}
    valid_url_count = 0
    invalid_url_count = 0
    valid_date_count = 0
    missing_date_count = 0
    
    for r in records:
        if r.sample_id in seen_ids:
            raise ValueError(f"Phát hiện sample_id trùng lặp trong tập chỉ mục: '{r.sample_id}'")
        seen_ids.add(r.sample_id)
        indexed_records.append(r)
        
        class_counts[r.source_label] = class_counts.get(r.source_label, 0) + 1
        source_counts[r.source_id] = source_counts.get(r.source_id, 0) + 1
        
        if r.is_valid_url:
            valid_url_count += 1
        else:
            invalid_url_count += 1
            
        if r.collected_at:
            valid_date_count += 1
        else:
            missing_date_count += 1
            
        if r.exclusion_reason:
            exclusion_counts[r.exclusion_reason] = exclusion_counts.get(r.exclusion_reason, 0) + 1
            
    manifest = {
        "dataset_type": "corpus_index_manifest",
        "total_records": len(indexed_records),
        "valid_urls": valid_url_count,
        "invalid_urls": invalid_url_count,
        "valid_dates": valid_date_count,
        "missing_dates": missing_date_count,
        "class_distribution": class_counts,
        "source_distribution": source_counts,
        "total_excluded_records": sum(exclusion_counts.values()),
        "exclusion_breakdown": exclusion_counts,
    }
    
    if output_index_path is not None:
        idx_p = Path(output_index_path)
        idx_p.parent.mkdir(parents=True, exist_ok=True)
        with open(idx_p, "w", encoding="utf-8") as f:
            for rec in indexed_records:
                f.write(json.dumps(rec.to_index_dict(), ensure_ascii=False) + "\n")
        manifest["index_file_sha256"] = _compute_sha256(idx_p.read_bytes())
        manifest["index_relative_path"] = str(idx_p)
        
    if output_manifest_path is not None:
        man_p = Path(output_manifest_path)
        man_p.parent.mkdir(parents=True, exist_ok=True)
        man_p.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        
    return indexed_records, manifest


def extract_labels_vault(records: Iterable[CorpusRecord]) -> Dict[str, Dict[str, Any]]:
    """Trích xuất kho nhãn mặt đất (Ground Truth Labels Vault) bảo mật của Thành viên C.
    
    Dùng để đối soát, tính toán metric hoặc phục vụ Lead D huấn luyện mô hình.
    """
    return {
        r.sample_id: {
            "source_label": r.source_label,
            "target": r.target,
            "source_id": r.source_id,
            "source_split": r.source_split,
            "group_id": r.group_id,
            "collected_at": r.collected_at,
            "exclusion_reason": r.exclusion_reason,
        }
        for r in records
    }
