"""Runner thực thi Cổng chọn mẫu Main Annotation 5 giai đoạn (Fail-Closed Selection Runner).

Kết nối trực tiếp SelectionGatePipeline với dữ liệu trích xuất thực tế.
Ghi nhận đầy đủ audit log số đếm qua từng cổng và niêm phong tập mẫu trích xuất.
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict

# Đảm bảo import được src/
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import pyarrow.parquet as pq

from phishing.data.selection_gate import (
    DEFAULT_APPROVED_REVISION,
    DEFAULT_APPROVED_SOURCE,
    SelectionGateError,
    SelectionGatePipeline,
)


def run_main_selection_pipeline(
    shard_path: Path | str,
    output_dir: Path | str,
    *,
    source_id: str = DEFAULT_APPROVED_SOURCE,
    revision: str = DEFAULT_APPROVED_REVISION,
    target_quota: int = 100,
    seed: int = 42,
    min_date: str = "2024-07-04",
    max_date: str = "2025-09-08",
) -> Dict[str, Any]:
    """Chạy toàn bộ pipeline chọn mẫu trên shard dữ liệu và lưu báo cáo kiểm toán."""
    p_shard = Path(shard_path)
    p_out = Path(output_dir)
    p_out.mkdir(parents=True, exist_ok=True)

    pipeline = SelectionGatePipeline(
        approved_source=source_id,
        approved_revision=revision,
        min_date=min_date,
        max_date=max_date,
    )

    # 1. Cổng 0: Kiểm tra Shard và Nguồn trước khi đọc tệp
    pipeline.gate_0_source_and_shard(source_id, p_shard, revision=revision)

    # 2. Đọc dữ liệu từ file parquet
    table = pq.read_table(p_shard)
    df = table.to_pandas()
    raw_records = df.to_dict(orient="records")

    # 3. Chạy qua các cổng 1 đến 4
    result = pipeline.run_selection(
        raw_records,
        source_id=source_id,
        shard_path=p_shard,
        revision=revision,
        target_quota=target_quota,
        seed=seed,
        skip_gate_0_file_check=True,  # Đã kiểm tra ở bước 1
    )

    # 4. Ghi audit manifest
    manifest_path = p_out / "selection_audit_manifest.json"
    manifest_path.write_text(json.dumps(result["audit_log"], indent=2, ensure_ascii=False), encoding="utf-8")

    return result


def main():
    parser = argparse.ArgumentParser(description="Runner chọn mẫu Main Annotation 5 giai đoạn (Fail-Closed)")
    parser.add_argument("--shard-path", type=str, required=True, help="Đường dẫn tới tệp parquet của shard")
    parser.add_argument("--output-dir", type=str, default="data/selection_out", help="Thư mục ghi kết quả")
    parser.add_argument("--source", type=str, default=DEFAULT_APPROVED_SOURCE, help="ID nguồn dữ liệu")
    parser.add_argument("--revision", type=str, default=DEFAULT_APPROVED_REVISION, help="Git revision của nguồn")
    parser.add_argument("--quota", type=int, default=100, help="Chỉ tiêu quota mẫu cần chọn")
    parser.add_argument("--seed", type=int, default=42, help="Seed ngẫu nhiên xác định")
    parser.add_argument("--min-date", type=str, default="2024-07-04", help="Ngày bắt đầu cửa sổ")
    parser.add_argument("--max-date", type=str, default="2025-09-08", help="Ngày kết thúc cửa sổ")

    args = parser.parse_args()

    try:
        res = run_main_selection_pipeline(
            shard_path=args.shard_path,
            output_dir=args.output_dir,
            source_id=args.source,
            revision=args.revision,
            target_quota=args.quota,
            seed=args.seed,
            min_date=args.min_date,
            max_date=args.max_date,
        )
        print("✅ CHỌN MẪU THÀNH CÔNG!")
        print(f"Số lượng mẫu trích xuất: {len(res['selected_samples'])}")
        print("Chi tiết số đếm qua từng cổng:")
        for gate, count in res["audit_log"]["gate_counts"].items():
            print(f"  • {gate}: {count}")
    except SelectionGateError as e:
        print(f"🛑 DỪNG FAIL-CLOSED: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ LỖI HỆ THỐNG: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
