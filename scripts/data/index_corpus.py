#!/usr/bin/env python3
"""CLI Lập chỉ mục Corpus (Corpus Indexing Engine) cho Task DEV-01 (Thành viên C).

Đọc dữ liệu nguồn (PhreshPhish Parquet, PhishVN ZIP/CSV hoặc JSONL mô phỏng),
chuẩn hóa schema theo DATA_PROTOCOL.md, trích xuất group_id (eTLD+1 + tenant),
áp dụng chốt chặn ExclusionRegistry, và xuất:
1. `corpus_index.jsonl`: Chỉ mục kỹ thuật (locator, normalized_url, group_id, html_sha256... KHÔNG chứa raw URL hay nhãn).
2. `restricted_vault.jsonl`: Kho nhãn và nội dung hạn chế bảo mật.
3. `index_manifest.json`: Báo cáo kiểm kê phân bố lớp, nguồn, ngày, mã băm SHA-256, và trạng thái sẵn sàng.

Ví dụ sử dụng:
    python scripts/data/index_corpus.py --source phreshphish --input-path data/train-000.parquet --output-dir data/processed/index
    python scripts/data/index_corpus.py --source jsonl --input-path tests/fixtures/sample.jsonl --output-dir data/processed/test_index --allow-unverified-fixture
"""

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

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
    ADAPTER_VERSION,
    CorpusRecord,
    adapt_source_row_to_record,
    build_corpus_index,
    load_phishvn_records,
    load_phreshphish_shard,
)

class MaxLevelFilter(logging.Filter):
    def __init__(self, max_level: int) -> None:
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= self.max_level


stdout_h = logging.StreamHandler(sys.stdout)
stdout_h.setLevel(logging.INFO)
stdout_h.addFilter(MaxLevelFilter(logging.INFO))

stderr_h = logging.StreamHandler(sys.stderr)
stderr_h.setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[stdout_h, stderr_h],
)
logger = logging.getLogger("IndexCorpus")


def _compute_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def _load_jsonl_records(
    file_path: Path,
    exclusion_registry: ExclusionRegistry | None = None,
    limit: int | None = None,
    id_prefix: str = "SYNTH",
) -> Iterator[CorpusRecord]:
    """Nạp các bản ghi từ tệp JSONL mô phỏng/thực nghiệm."""
    count = 0
    with open(file_path, "r", encoding="utf-8") as f:
        for row_idx, line in enumerate(f):
            if limit is not None and count >= limit:
                break
            line_str = line.strip()
            if not line_str:
                continue
            row = json.loads(line_str)
            sample_id = row.get("sample_id") or f"{id_prefix}-R{row_idx:06d}"

            locator = {
                "source_id": "synthetic",
                "file": file_path.name,
                "row_offset": row_idx,
            }

            yield adapt_source_row_to_record(
                sample_id=sample_id,
                source_id=row.get("source_id", "synthetic"),
                source_revision=row.get("source_revision", "fixture-dev-0"),
                source_split=row.get("source_split", "train"),
                locator=locator,
                raw_url=row.get("url") or row.get("raw_url") or "",
                raw_html=row.get("html") or row.get("raw_html"),
                raw_date=row.get("date") or row.get("collected_at"),
                raw_label=row.get("label") or row.get("source_label"),
                target=row.get("target"),
                language=str(row.get("lang") or row.get("language") or "en"),
                capture_mode=row.get("capture_mode"),
                exclusion_registry=exclusion_registry,
                is_real_data_mode=False,
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
        default=None,
        help="Đường dẫn tới tệp nguồn dữ liệu đơn lẻ (parquet, csv, zip, hoặc jsonl)",
    )
    parser.add_argument(
        "--shards",
        default=None,
        help="Danh sách nhiều shard cách nhau bởi dấu phẩy, hoặc glob pattern (ví dụ data/train-*.parquet)",
    )
    parser.add_argument(
        "--source-manifest",
        default=str(PROJECT_ROOT / "configs" / "source_manifest.json"),
        help="Đường dẫn source_manifest.json để đối chiếu xuất xứ và danh sách shard",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "data" / "processed" / "index"),
        help="Thư mục xuất kết quả (chứa corpus_index.jsonl, restricted_vault.jsonl và index_manifest.json)",
    )
    parser.add_argument(
        "--exclusion-registry",
        default=str(PROJECT_ROOT / "data" / "exclusion_registry.json"),
        help="Đường dẫn tệp danh mục loại trừ pilot (chống rò rỉ dữ liệu)",
    )
    parser.add_argument(
        "--id-prefix",
        default=None,
        help="Tiền tố tùy chọn cho sample_id (mặc định gắn với shard name và row offset)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Giới hạn tổng số bản ghi nạp (dùng khi thử nghiệm nhanh)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Cho phép ghi đè nếu thư mục output đã chứa chỉ mục cũ",
    )
    parser.add_argument(
        "--allow-unverified-fixture",
        action="store_true",
        help="Chỉ cho phép bỏ qua exclusion registry đối với fixture thử nghiệm (jsonl/synthetic)",
    )

    args = parser.parse_args()

    # 1. Bảo vệ chống ghi đè (Atomic / Non-overwrite Protection - Khắc phục Probe 3)
    output_dir = Path(args.output_dir)
    index_file = output_dir / "corpus_index.jsonl"
    manifest_file = output_dir / "index_manifest.json"
    vault_file = output_dir / "restricted_vault.jsonl"

    if (index_file.exists() or manifest_file.exists()) and not args.overwrite:
        logger.error(
            f"Thư mục output '{output_dir}' đã chứa artifacts chỉ mục cũ. "
            "Yêu cầu dùng thư mục run mới hoặc truyền rõ cờ '--overwrite' để ghi đè."
        )
        sys.exit(1)

    # 2. Chốt chặn ExclusionRegistry nghiêm ngặt (Khắc phục Probe 1)
    is_real_data = args.source in {"phreshphish", "phishvn"}
    reg_path = Path(args.exclusion_registry)
    reg: Optional[ExclusionRegistry] = None

    if is_real_data:
        if not reg_path.is_file():
            logger.error(
                f"CHỐT CHẶN PHÒNG VỆ: Chế độ dữ liệu thật '{args.source}' bắt buộc phải có ExclusionRegistry "
                f"tại '{reg_path}'. Dừng thực thi ngay lập tức để chống rò rỉ pilot!"
            )
            sys.exit(1)
        logger.info(f"Kích hoạt chốt chặn phòng vệ ExclusionRegistry từ '{reg_path}'")
        reg = ExclusionRegistry(reg_path)
    else:
        if reg_path.is_file():
            logger.info(f"Kích hoạt ExclusionRegistry cho fixture từ '{reg_path}'")
            reg = ExclusionRegistry(reg_path)
        elif not args.allow_unverified_fixture:
            logger.error(
                f"Không tìm thấy exclusion registry tại '{reg_path}'. "
                "Đối với fixture thử nghiệm, truyền '--allow-unverified-fixture' để xác nhận."
            )
            sys.exit(1)
        else:
            logger.info("Chạy chế độ fixture bỏ qua exclusion registry (--allow-unverified-fixture).")

    # 3. Xác định danh sách tệp nguồn (Khắc phục Probe 3)
    input_files: List[Path] = []
    if args.shards:
        for shard_item in args.shards.split(","):
            s_item = shard_item.strip()
            if not s_item:
                continue
            p = Path(s_item)
            if "*" in s_item:
                input_files.extend(sorted(p.parent.glob(p.name)))
            elif p.is_file():
                input_files.append(p)
            else:
                logger.error(f"Shard không tồn tại: '{p}'")
                sys.exit(1)
    elif args.input_path:
        p = Path(args.input_path)
        if not p.is_file():
            logger.error(f"Tệp đầu vào không tồn tại: '{p}'")
            sys.exit(1)
        input_files.append(p)
    else:
        logger.error("Yêu cầu chỉ định ít nhất một trong '--input-path' hoặc '--shards'.")
        sys.exit(1)

    # 4. Tính toán mã băm của các tệp nguồn (Khắc phục Probe 4)
    file_hashes: List[Dict[str, Any]] = []
    for f in input_files:
        sha = _compute_file_sha256(f)
        file_hashes.append({
            "file_name": f.name,
            "path": str(f),
            "byte_size": f.stat().st_size,
            "sha256": sha,
        })
        logger.info(f"Xác nhận tệp nguồn: {f.name} ({f.stat().st_size} bytes, SHA-256: {sha[:12]}...)")

    source_manifest_path = Path(args.source_manifest) if args.source_manifest else None
    source_manifest_sha = None
    if source_manifest_path and source_manifest_path.is_file():
        source_manifest_sha = _compute_file_sha256(source_manifest_path)

    reg_sha = _compute_file_sha256(reg_path) if reg_path.is_file() else None

    # 5. Khởi tạo Stream Reader tuần tự
    def record_generator() -> Iterator[CorpusRecord]:
        remaining_limit = args.limit
        for f in input_files:
            if remaining_limit is not None and remaining_limit <= 0:
                break
            if args.source == "phreshphish":
                shard_iter = load_phreshphish_shard(
                    f,
                    source_manifest_path=source_manifest_path,
                    exclusion_registry=reg,
                    limit=remaining_limit,
                    is_real_data_mode=is_real_data,
                )
            elif args.source == "phishvn":
                shard_iter = load_phishvn_records(
                    f,
                    exclusion_registry=reg,
                    limit=remaining_limit,
                    is_real_data_mode=is_real_data,
                )
            else:
                shard_iter = _load_jsonl_records(
                    f,
                    exclusion_registry=reg,
                    limit=remaining_limit,
                    id_prefix=args.id_prefix or "SYNTH",
                )

            for rec in shard_iter:
                yield rec
                if remaining_limit is not None:
                    remaining_limit -= 1

    # 6. Lập chỉ mục tuần tự dạng STREAMING không giữ toàn bộ HTML trong RAM
    logger.info(f"Bắt đầu lập chỉ mục và xuất ra '{output_dir}'...")

    provenance_metadata = {
        "adapter_version": ADAPTER_VERSION,
        "source_type": args.source,
        "input_files": file_hashes,
        "source_manifest_path": str(source_manifest_path) if source_manifest_path else None,
        "source_manifest_sha256": source_manifest_sha,
        "exclusion_registry_path": str(reg_path) if reg_path.is_file() else None,
        "exclusion_registry_sha256": reg_sha,
    }

    training_blocked = True
    if reg is not None:
        training_blocked = reg.training_blocked

    total_records, manifest = build_corpus_index(
        record_generator(),
        output_index_path=index_file,
        output_vault_path=vault_file,
        output_manifest_path=manifest_file,
        training_blocked=training_blocked,
        additional_metadata=provenance_metadata,
    )

    logger.info("=== KẾT QUẢ LẬP CHỈ MỤC CORPUS ===")
    logger.info(f"Tổng số bản ghi: {manifest['total_records']}")
    logger.info(f"URLs hợp lệ: {manifest['valid_urls']} | URLs lỗi: {manifest['invalid_urls']}")
    logger.info(f"Trạng thái ngày: {manifest['date_status_distribution']}")
    logger.info(f"Phân bố lớp: {manifest['class_distribution']}")
    logger.info(f"Phân bố nhãn: {manifest['label_status_distribution']}")
    logger.info(f"Số bản ghi bị loại trừ: {manifest['total_excluded_records']}")
    logger.info(f"Sẵn sàng huấn luyện: {manifest['ready_for_training']} ({manifest['training_readiness_status']})")
    logger.info(f"Chỉ mục kỹ thuật: {index_file} (SHA-256: {manifest.get('index_file_sha256')})")
    logger.info(f"Kho nhãn bảo mật: {vault_file} (SHA-256: {manifest.get('vault_file_sha256')})")
    logger.info(f"Manifest xuất xứ: {manifest_file}")


if __name__ == "__main__":
    main()
