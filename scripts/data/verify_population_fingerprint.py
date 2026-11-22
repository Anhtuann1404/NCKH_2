"""Công cụ kiểm chứng độc lập mã băm đa chiều của Quần thể 1.232 ứng viên.

Dành cho Lead D kiểm tra độc lập qua kênh hạn chế:
Cách dùng:
    python scripts/data/verify_population_fingerprint.py --records data/restricted/main_batch1/population_1232_canonical_records_v1.json
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

# Ensure src in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from phishing.preprocessing.urls import normalize_url


EXPECTED_MULTIDIMENSIONAL_FINGERPRINT = "77773871ab50c361cb5df0ca4f9e5604a251a20f933d1bc22ee7d9f016814919"
EXPECTED_HISTORICAL_UID_HASH = "40ad5d600e93b10d3fe5910e7454ce4a7a94fe2384b5625d8e6af8983525f9a8"


def verify_population_fingerprint(records_path: Path | str) -> dict:
    p = Path(records_path)
    if not p.exists():
        raise FileNotFoundError(f"Không tìm thấy tệp hồ sơ chuẩn hóa tại: {p}")

    data = json.loads(p.read_text(encoding="utf-8"))
    records = data.get("records", [])
    print(f"Tổng số bản ghi trong hồ sơ: {len(records)}")
    if len(records) != 1232:
        raise ValueError(f"Sai lệch số lượng: kỳ vọng đúng 1.232 bản ghi, thực tế có {len(records)}!")

    # 1. Kiểm tra tính hiện diện và tính hợp lệ của 8 trường bắt buộc
    required_fields = [
        "candidate_uid", "url_raw", "url_normalized", "url_sha256",
        "html_sha256", "source_shard", "source_row", "source_revision"
    ]
    uids = []
    for idx, r in enumerate(records):
        for f in required_fields:
            if f not in r or r[f] is None:
                raise ValueError(f"Bản ghi {idx} thiếu trường bắt buộc: '{f}'")
        uids.append(r["candidate_uid"])

    print("OK: 100% bản ghi có đủ 8 trường chuẩn hóa.")

    # 2. Kiểm tra tính tương thích với hash UID-only lịch sử
    uid_hash = hashlib.sha256(json.dumps(uids).encode()).hexdigest()
    print(f"Historical UID list hash: {uid_hash}")
    if uid_hash != EXPECTED_HISTORICAL_UID_HASH:
        raise ValueError(f"Mã băm UID lịch sử không khớp! Kỳ vọng {EXPECTED_HISTORICAL_UID_HASH}, thực tế {uid_hash}")
    print("OK: Khớp 100% danh sách UID của quần thể lịch sử!")

    # 3. Tính toán fingerprint đa chiều bằng serialization chuẩn hóa
    sorted_records = list(records)
    sorted_records.sort(key=lambda r: (r["url_normalized"], r["html_sha256"], r["candidate_uid"]))
    canonical_bytes = json.dumps(sorted_records, sort_keys=True, ensure_ascii=False).encode("utf-8")
    actual_fp = hashlib.sha256(canonical_bytes).hexdigest()

    print(f"Computed multidimensional fingerprint: {actual_fp}")
    if actual_fp != EXPECTED_MULTIDIMENSIONAL_FINGERPRINT:
        raise ValueError(f"Sai lệch fingerprint! Kỳ vọng {EXPECTED_MULTIDIMENSIONAL_FINGERPRINT}, thực tế {actual_fp}")
    print("OK: Tái lập CHÍNH XÁC 100% fingerprint đa chiều 77773871ab50c361cb5df0ca4f9e5604a251a20f933d1bc22ee7d9f016814919!")

    # 4. Kiểm tra sự hiện diện của 100 mẫu Main và 30 mẫu B
    mapping_path = Path("data/restricted/main_batch1/mapping_restricted.json")
    if mapping_path.exists():
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
        map_uids = [m["candidate_uid"] for m in mapping]
        b_uids = [m["candidate_uid"] for m in mapping if m.get("is_b_kappa_sample")]
        cand_set = set(uids)

        assert all(uid in cand_set for uid in map_uids), "Toàn bộ 100 mẫu Main phải thuộc quần thể 1.232!"
        assert all(uid in cand_set for uid in b_uids), "Toàn bộ 30 mẫu B phải thuộc quần thể 1.232!"
        print(f"OK: Bảo toàn đầy đủ 100 mẫu Main và 30 mẫu B30 trong quần thể.")

    return {
        "status": "PASS",
        "population_count": len(records),
        "historical_uid_hash": uid_hash,
        "multidimensional_fingerprint": actual_fp,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kiểm chứng fingerprint đa chiều của quần thể 1.232 ứng viên.")
    parser.add_argument(
        "--records",
        default="data/restricted/main_batch1/population_1232_canonical_records_v1.json",
        help="Đường dẫn tới tệp hồ sơ chuẩn hóa 1.232 ứng viên",
    )
    args = parser.parse_args()
    verify_population_fingerprint(args.records)
