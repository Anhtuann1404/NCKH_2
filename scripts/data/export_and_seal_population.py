"""Kịch bản trích xuất, niêm phong quần thể 1.232 ứng viên và chạy Main Annotation Đợt 1.

Tuân thủ nghiêm ngặt chỉ đạo của Lead D:
1. Shard: data/raw/phreshphish/data/train-001.parquet
2. Revision: eabec4b7a66324b79cc8a0ad856d1731dc26fe1a
3. Gates 0–3 với seed xử lý quần thể = 42
4. Số đếm kiểm chứng: 5.780 -> 2.752 -> 2.321 -> 1.232
5. Niêm phong quần thể tại data/restricted/population_1232_sealed.json
6. Thực thi quy trình sampling 100 mẫu Main và 30 mẫu cho B
7. Đóng gói Blind View v1.2.0 và Release Manifest
"""

import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Đảm bảo import được src/ và project root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import pyarrow.parquet as pq

from phishing.data.selection_gate import (
    DEFAULT_APPROVED_REVISION,
    DEFAULT_APPROVED_SOURCE,
    SelectionGatePipeline,
)
from scripts.data.run_main_batch1_pipeline import export_main_batch1


def extract_and_seal_main_batch1(
    shard_path: Path | str = "data/raw/phreshphish/data/train-001.parquet",
    output_dir_restricted: Path | str = "data/restricted/main_batch1",
    public_artifacts_dir: Path | str = "artifacts",
    seed_population: int = 42,
    seed_lot_100: Optional[int] = None,
    seed_b_subset_30: Optional[int] = None,
    seed_release_shuffle: Optional[int] = None,
    blind_salt: Optional[str] = None,
) -> Dict[str, Any]:
    p_shard = Path(shard_path)
    print("=" * 70)
    print("BƯỚC 1: TÁI LẬP VÀ KHÓA QUẦN THỂ 1.232 ỨNG VIÊN TỪ SHARD TRAIN-001")
    print(f"Shard: {p_shard}")
    print(f"Seed xử lý quần thể: {seed_population}")

    pipeline = SelectionGatePipeline(
        approved_source=DEFAULT_APPROVED_SOURCE,
        approved_revision=DEFAULT_APPROVED_REVISION,
    )

    # 1. Gate 0
    pipeline.gate_0_source_and_shard(DEFAULT_APPROVED_SOURCE, p_shard, revision=DEFAULT_APPROVED_REVISION)

    # 2. Đọc bảng parquet
    table = pq.read_table(p_shard)
    df = table.to_pandas()
    raw_records = df.to_dict(orient="records")
    print(f"Số bản ghi đọc từ parquet: {len(raw_records)}")

    # 3. Chạy qua Gates 1 - 4 với quota = 1232 để lấy toàn bộ 1232 ứng viên
    res = pipeline.run_selection(
        raw_records,
        source_id=DEFAULT_APPROVED_SOURCE,
        shard_path=p_shard,
        revision=DEFAULT_APPROVED_REVISION,
        target_quota=1232,
        seed=seed_population,
        skip_gate_0_file_check=True,
        vetting_only=False,
    )

    candidates = res["selected_samples"]
    gate_counts = res["audit_log"]["gate_counts"]
    print(f"Số lượng ứng viên qua Cổng 3: {len(candidates)}")
    print(f"Số đếm các cổng: {gate_counts}")

    if len(candidates) != 1232:
        raise ValueError(f"SAI LỆCH QUẦN THỂ: Kỳ vọng đúng 1.232 ứng viên, thực tế nhận {len(candidates)}!")

    # 4. Gắn candidate_uid chuẩn hóa cho từng ứng viên
    for idx, c in enumerate(candidates):
        url_norm = c.get("url", "")
        h_norm = c.get("html", "")
        uid = f"cand_1232_{idx:04d}_{hashlib.sha256(f'{url_norm}:{idx}'.encode()).hexdigest()[:8]}"
        c["candidate_uid"] = uid
        c["canonical_index"] = idx

    print("=" * 70)
    print("BƯỚC 2: RÚT MẪU NGẪU NHIÊN KHÔNG HOÀN LẠI VÀ ĐÓNG GÓI NIÊM PHONG")
    batch_res = export_main_batch1(
        candidates,
        output_dir_restricted=output_dir_restricted,
        public_artifacts_dir=public_artifacts_dir,
        seed_lot_100=seed_lot_100,
        seed_b_subset_30=seed_b_subset_30,
        seed_release_shuffle=seed_release_shuffle,
        blind_salt=blind_salt,
    )

    print("=" * 70)
    print("HOÀN TẤT ĐÓNG GÓI MAIN ANNOTATION ĐỢT 1 THÀNH CÔNG!")
    print(f"Trạng thái cách ly Git: {batch_res['isolation_status']}")
    print(f"Release manifest: {public_artifacts_dir}/main_batch1_release_manifest.json")
    print(f"Gói hạn chế: {output_dir_restricted}")
    return batch_res


if __name__ == "__main__":
    extract_and_seal_main_batch1()
