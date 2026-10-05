#!/usr/bin/env python3
"""CLI Lập chỉ mục Corpus (Corpus Indexing Engine) cho Task DEV-01 (Thành viên C).

Đọc dữ liệu nguồn (PhreshPhish Parquet, PhishVN ZIP/CSV hoặc JSONL mô phỏng),
chuẩn hóa schema theo DATA_PROTOCOL.md, trích xuất group_id (eTLD+1 + tenant),
áp dụng chốt chặn ExclusionRegistry, và xuất:
1. `corpus_index.jsonl`: Chỉ mục bản ghi nghiên cứu hoàn chỉnh (không chứa raw HTML).
2. `index_manifest.json`: Báo cáo kiểm kê phân bố lớp, nguồn, ngày và mã băm SHA-256.

Ví dụ sử dụng:
    python scripts/data/index_corpus.py --source phreshphish --input-path data/train-000.parquet --output-dir data/processed/index
    python scripts/data/index_corpus.py --source jsonl --input-path tests/fixtures/sample.jsonl --output-dir data/processed/test_index
"""

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Iterator

# Đảm bảo stdout / stderr luôn dùng utf-8 trên mọi nền tảng kể cả Windows console cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Đưa src vào sys.path để import phishing
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from phishing.data.exclusion import ExclusionRegistry
from phishing.data.loader import (
    CorpusRecord,
    adapt_source_row_to_record,
    build_corpus_index,
    load_phishvn_records,
    load_phreshphish_shard,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("IndexCorpus")


def _load_jsonl_records(
    file_path: Path,
    exclusion_registry: ExclusionRegistry | None = None,
    limit: int | None = None,
    id_prefix: str = "SYNTH",
) -> Iterator[CorpusRecord]:
    """Nạp các bản ghi từ tệp JSONL mô phỏng/thực nghiệm."""
    count = 0
    with open(file_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            if limit is not None and count >= limit:
                break
            line_str = line.strip()
            if not line_str:
                continue
            row = json.loads(line_str)
            sample_id = row.get("sample_id") or f"{id_prefix}-{idx:06d}"
            
            raw_label = str(row.get("label") or row.get("source_label") or "benign").strip().lower()
            std_label = "phishing" if raw_label in {"phish", "phishing", "1", "true"} else "benign"
            
            yield adapt_source_row_to_record(
                sample_id=sample_id,
                source_id=row.get("source_id", "synthetic"),
                source_revision=row.get("source_revision", "fixture-dev-0"),
                source_split=row.get("source_split", "train"),
                raw_url=row.get("url") or row.get("raw_url") or "",
                raw_html=row.get("html") or row.get("raw_html"),
                raw_date=row.get("date") or row.get("collected_at"),
                source_label=std_label,
                target=row.get("target"),
                language=str(row.get("lang") or row.get("language") or "en"),
                capture_mode=row.get("capture_mode"),
                exclusion_registry=exclusion_registry,
            )
            count += 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lập chỉ mục và kiểm kê nguồn dữ liệu nghiên cứu (Task DEV-01)",
    )
    parser.add_argument(
        "--source",
        choices=["phreshphish", "phishvn", "jsonl", "synthetic"],
        required=True,
        help="Loại nguồn dữ liệu (phreshphish, phishvn, jsonl, synthetic)",
    )
    parser.add_argument(
        "--input-path",
        required=True,
        help="Đường dẫn tới tệp nguồn dữ liệu (parquet, csv, zip, hoặc jsonl)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "data" / "processed" / "index"),
        help="Thư mục xuất kết quả (chứa corpus_index.jsonl và index_manifest.json)",
    )
    parser.add_argument(
        "--exclusion-registry",
        default=str(PROJECT_ROOT / "data" / "exclusion_registry.json"),
        help="Đường dẫn tệp danh mục loại trừ pilot (chống rò rỉ dữ liệu)",
    )
    parser.add_argument(
        "--id-prefix",
        default=None,
        help="Tiền tố cho sample_id (mặc định theo nguồn: PP-TRAIN, PVN, SYNTH)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Giới hạn số bản ghi nạp (dùng khi thử nghiệm nhanh)",
    )
    parser.add_argument(
        "--no-exclusion-filter",
        action="store_true",
        help="Bỏ qua kiểm tra exclusion registry (KHÔNG khuyến nghị trong nghiên cứu)",
    )

    args = parser.parse_args()

    input_path = Path(args.input_path)
    if not input_path.exists():
        logger.error(f"Tệp đầu vào không tồn tại: {input_path}")
        sys.exit(1)

    # 1. Khởi tạo ExclusionRegistry
    reg = None
    if not args.no_exclusion_filter:
        reg_path = Path(args.exclusion_registry)
        if reg_path.exists():
            logger.info(f"Kích hoạt chốt chặn phòng vệ ExclusionRegistry từ '{reg_path}'")
            reg = ExclusionRegistry(reg_path)
        else:
            logger.warning(f"Không tìm thấy exclusion registry tại '{reg_path}'. Bỏ qua kiểm tra loại trừ.")

    # 2. Lựa chọn reader theo nguồn
    output_dir = Path(args.output_dir)
    index_file = output_dir / "corpus_index.jsonl"
    manifest_file = output_dir / "index_manifest.json"

    logger.info(f"Bắt đầu nạp dữ liệu từ '{input_path}' (nguồn: {args.source})...")

    records_iter: Iterator[CorpusRecord]
    if args.source == "phreshphish":
        prefix = args.id_prefix or "PP-TRAIN"
        records_iter = load_phreshphish_shard(
            input_path,
            id_prefix=prefix,
            exclusion_registry=reg,
            limit=args.limit,
        )
    elif args.source == "phishvn":
        prefix = args.id_prefix or "PVN"
        records_iter = load_phishvn_records(
            input_path,
            id_prefix=prefix,
            exclusion_registry=reg,
            limit=args.limit,
        )
    else:  # jsonl hoặc synthetic
        prefix = args.id_prefix or "SYNTH"
        records_iter = _load_jsonl_records(
            input_path,
            exclusion_registry=reg,
            limit=args.limit,
            id_prefix=prefix,
        )

    # 3. Lập chỉ mục và xuất tệp
    indexed, manifest = build_corpus_index(
        records_iter,
        output_index_path=index_file,
        output_manifest_path=manifest_file,
    )

    logger.info("=== KẾT QUẢ LẬP CHỈ MỤC DỮ LIỆU ===")
    logger.info(f"Tổng số bản ghi: {manifest['total_records']}")
    logger.info(f"URLs hợp lệ: {manifest['valid_urls']} | URLs lỗi: {manifest['invalid_urls']}")
    logger.info(f"Ngày hợp lệ: {manifest['valid_dates']} | Ngày thiếu: {manifest['missing_dates']}")
    logger.info(f"Phân bố lớp: {manifest['class_distribution']}")
    logger.info(f"Tổng số bản ghi bị loại trừ: {manifest['total_excluded_records']}")
    if manifest["exclusion_breakdown"]:
        logger.info(f"Chi tiết loại trừ: {manifest['exclusion_breakdown']}")
    logger.info(f"Đã ghi chỉ mục ra: {index_file} (SHA-256: {manifest.get('index_file_sha256')})")
    logger.info(f"Đã ghi manifest ra: {manifest_file}")


if __name__ == "__main__":
    main()
