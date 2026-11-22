"""Công cụ đối chiếu và kiểm chứng độc lập Provenance cấp dòng từ shard Parquet gốc.

Dành cho Lead D kiểm tra độc lập qua kênh hạn chế:
Cách dùng:
    python scripts/data/verify_provenance_from_parquet.py --shard data/raw/phreshphish/data/train-001.parquet --mapping data/restricted/main_batch1/mapping_restricted.json
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

# Ensure src in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pyarrow.parquet as pq
from phishing.annotation.blind_view import compute_sample_content_hash
from phishing.preprocessing.urls import normalize_url


EXPECTED_SHARD_SHA256 = "260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74"
EXPECTED_SHARD_SIZE = 322018201
EXPECTED_REVISION = "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a"


def verify_provenance(shard_path: Path | str, mapping_path: Path | str) -> dict:
    p_shard = Path(shard_path)
    p_mapping = Path(mapping_path)

    if not p_shard.exists():
        raise FileNotFoundError(f"Không tìm thấy shard tại: {p_shard}")
    if not p_mapping.exists():
        raise FileNotFoundError(f"Không tìm thấy mapping tại: {p_mapping}")

    print("=" * 70)
    print("KIỂM CHỨNG ĐỘC LẬP PROVENANCE CẤP DÒNG TỪ PARQUET GỐC")
    print("=" * 70)

    # 1. Kiểm tra toàn vẹn byte và hash của Shard nguồn
    actual_size = p_shard.stat().st_size
    print(f"Shard: {p_shard.name} ({actual_size:,} bytes)")
    if actual_size != EXPECTED_SHARD_SIZE:
        raise ValueError(f"Kích thước shard không khớp: kỳ vọng {EXPECTED_SHARD_SIZE}, thực tế {actual_size}")

    actual_shard_sha = hashlib.sha256(p_shard.read_bytes()).hexdigest()
    print(f"SHA-256 Shard: {actual_shard_sha}")
    if actual_shard_sha != EXPECTED_SHARD_SHA256:
        raise ValueError(f"Mã băm shard không khớp source_manifest.json! Kỳ vọng {EXPECTED_SHARD_SHA256}, thực tế {actual_shard_sha}")
    print("OK: Shard byte stream khớp 100% với revision khóa eabec4b7a66324b79cc8a0ad856d1731dc26fe1a.")

    # 2. Đọc bảng parquet
    print("Đọc cột url, html từ parquet...")
    table = pq.read_table(p_shard, columns=["url", "html"])
    urls = table["url"].to_pylist()
    htmls = table["html"].to_pylist()
    total_rows = len(urls)
    print(f"Tổng số bản ghi trong parquet: {total_rows}")

    # Xây dựng chỉ mục tra cứu URL
    url_to_rows = {}
    for idx, u in enumerate(urls):
        url_to_rows.setdefault(u, []).append(idx)

    # 3. Đọc mapping
    mapping = json.loads(p_mapping.read_text(encoding="utf-8"))
    print(f"Tổng số mẫu trong mapping: {len(mapping)}")

    exact_matches = 0
    multiple_matches = 0
    no_matches = 0
    audit_records = []

    for idx, m in enumerate(mapping):
        b_id = m["blind_id"]
        c_uid = m["candidate_uid"]
        m_url = m["url"]
        recorded_s_row = m.get("source_row")

        if recorded_s_row is None:
            no_matches += 1
            audit_records.append({"blind_id": b_id, "status": "FAIL_SOURCE_ROW_NULL"})
            continue

        matching_rows = url_to_rows.get(m_url, [])
        if len(matching_rows) == 1:
            row_idx = matching_rows[0]
            if row_idx == recorded_s_row:
                # Kiểm tra đối chiếu mã băm HTML
                actual_html_hash = hashlib.sha256((htmls[row_idx] or "").encode("utf-8")).hexdigest()
                recorded_html_hash = m.get("html_sha256")
                if recorded_html_hash and recorded_html_hash != actual_html_hash:
                    raise ValueError(f"Mẫu {b_id}: html_sha256 không khớp! Ghi nhận {recorded_html_hash}, thực tế {actual_html_hash}")

                exact_matches += 1
                audit_records.append({
                    "blind_id": b_id,
                    "candidate_uid": c_uid,
                    "url": m_url,
                    "source_row": row_idx,
                    "html_sha256": actual_html_hash,
                    "match_type": "EXACT_UNIQUE",
                })
            else:
                multiple_matches += 1
                audit_records.append({
                    "blind_id": b_id,
                    "status": "FAIL_ROW_INDEX_MISMATCH",
                    "recorded": recorded_s_row,
                    "actual": row_idx,
                })
        elif len(matching_rows) > 1:
            multiple_matches += 1
            audit_records.append({"blind_id": b_id, "status": "MULTIPLE_ROWS", "rows": matching_rows})
        else:
            no_matches += 1
            audit_records.append({"blind_id": b_id, "status": "URL_NOT_FOUND_IN_PARQUET"})

    print(f"\nKết quả kiểm chứng Provenance:")
    print(f"  - Khớp duy nhất 1-1: {exact_matches}/{len(mapping)} ({exact_matches/len(mapping)*100:.1f}%)")
    print(f"  - Nhiều khớp (đa nghĩa): {multiple_matches}")
    print(f"  - Không khớp: {no_matches}")

    if exact_matches != 100:
        raise ValueError(f"Chưa đạt 100/100 khớp duy nhất: chỉ đạt {exact_matches}")

    print("OK: Provenance cấp dòng được xác nhận 100/100 khớp duy nhất với parquet gốc!")
    return {
        "status": "PASS",
        "total_samples": len(mapping),
        "exact_matches": exact_matches,
        "shard_sha256": actual_shard_sha,
        "audit_records": audit_records,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kiểm chứng provenance cấp dòng từ parquet.")
    parser.add_argument(
        "--shard",
        default="data/raw/phreshphish/data/train-001.parquet",
        help="Đường dẫn tới tệp train-001.parquet",
    )
    parser.add_argument(
        "--mapping",
        default="data/restricted/main_batch1/mapping_restricted.json",
        help="Đường dẫn tới tệp mapping_restricted.json",
    )
    args = parser.parse_args()
    verify_provenance(args.shard, args.mapping)
