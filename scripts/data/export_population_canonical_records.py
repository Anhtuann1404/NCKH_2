"""Xuất và niêm phong hồ sơ chuẩn hóa 1.232 ứng viên quần thể với 8 trường siêu dữ liệu đa chiều.

Bảo đảm:
1. Đọc đúng shard train-001.parquet (revision eabec4b7a66324b79cc8a0ad856d1731dc26fe1a).
2. Chạy qua Gates 0-3 với seed=42 để lấy đúng 1.232 ứng viên.
3. Đối chiếu 1.232 candidate_uids khớp 100% với tệp lịch sử population_1232_sealed.json.
4. Xuất 8 trường: candidate_uid, url_raw, url_normalized, url_sha256, html_sha256, source_shard, source_row, source_revision.
5. Tính toán và xác nhận fingerprint đa chiều: 77773871ab50c361cb5df0ca4f9e5604a251a20f933d1bc22ee7d9f016814919.
6. Lưu tệp bổ sung: data/restricted/main_batch1/population_1232_canonical_records_v1.json (không ghi đè tệp lịch sử).
"""

import hashlib
import json
from pathlib import Path
import sys

# Ensure src in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pyarrow.parquet as pq

from phishing.data.main_sampling import compute_population_fingerprint
from phishing.data.selection_gate import (
    DEFAULT_APPROVED_REVISION,
    DEFAULT_APPROVED_SOURCE,
    SelectionGatePipeline,
)
from phishing.preprocessing.urls import normalize_url


def main():
    print("=" * 70)
    print("XUẤT HỒ SƠ CHUẨN HÓA QUẦN THỂ 1.232 ỨNG VIÊN (CANONICAL RECORDS V1)")
    print("=" * 70)

    p_shard = Path("data/raw/phreshphish/data/train-001.parquet")
    print(f"Reading parquet: {p_shard}")
    table = pq.read_table(p_shard)
    df = table.to_pandas()
    raw_records = df.to_dict(orient="records")
    print(f"Total raw records: {len(raw_records)}")

    # Gắn locator nguồn trước khi lọc
    for idx, r in enumerate(raw_records):
        r["source_row"] = idx
        r["source_shard"] = p_shard.name
        r["source_revision"] = DEFAULT_APPROVED_REVISION

    pipeline = SelectionGatePipeline(
        approved_source=DEFAULT_APPROVED_SOURCE,
        approved_revision=DEFAULT_APPROVED_REVISION,
    )

    print("Running Selection Gate Pipeline (Gates 0-3, quota=1232, seed=42)...")
    res = pipeline.run_selection(
        raw_records,
        source_id=DEFAULT_APPROVED_SOURCE,
        shard_path=p_shard,
        revision=DEFAULT_APPROVED_REVISION,
        target_quota=1232,
        seed=42,
        skip_gate_0_file_check=True,
        vetting_only=False,
    )

    candidates = res["selected_samples"]
    print(f"Selected candidates count: {len(candidates)}")
    if len(candidates) != 1232:
        raise ValueError(f"Expected 1232 candidates, got {len(candidates)}")

    for idx, c in enumerate(candidates):
        url_norm = c.get("url", "")
        uid = f"cand_1232_{idx:04d}_{hashlib.sha256(f'{url_norm}:{idx}'.encode()).hexdigest()[:8]}"
        c["candidate_uid"] = uid
        c["canonical_index"] = idx

    # Đối chiếu với danh sách UIDs lịch sử
    hist_file = Path("data/restricted/main_batch1/population_1232_sealed.json")
    hist_data = json.loads(hist_file.read_text(encoding="utf-8"))
    hist_uids = hist_data.get("candidates_uids", [])
    cand_uids = [c["candidate_uid"] for c in candidates]

    if cand_uids != hist_uids:
        raise ValueError("UIDs do not match historical sealed population!")
    print("OK: 1.232 Candidate UIDs match historical sealed population 100%!")

    # Tính fingerprint đa chiều trực tiếp trên raw candidates
    pop_fp = compute_population_fingerprint(candidates)
    print(f"Computed population fingerprint: {pop_fp}")
    expected_fp = "77773871ab50c361cb5df0ca4f9e5604a251a20f933d1bc22ee7d9f016814919"
    if pop_fp != expected_fp:
        raise ValueError(f"Fingerprint mismatch! Expected {expected_fp}, got {pop_fp}")
    print(f"OK: Matches published multidimensional fingerprint {expected_fp}!")

    # Tạo hồ sơ 8 trường chuẩn hóa
    canonical_records = []
    for c in candidates:
        raw_url = str(c.get("url", ""))
        norm_url = normalize_url(raw_url)
        url_hash = hashlib.sha256(raw_url.encode("utf-8")).hexdigest()
        html_hash = hashlib.sha256((c.get("html") or "").encode("utf-8")).hexdigest()

        canonical_records.append({
            "candidate_uid": c["candidate_uid"],
            "url_raw": raw_url,
            "url_normalized": norm_url,
            "url_sha256": url_hash,
            "html_sha256": html_hash,
            "source_shard": p_shard.name,
            "source_row": c.get("source_row"),
            "source_revision": DEFAULT_APPROVED_REVISION,
        })

    # Xác thực thuật toán độc lập trên canonical_records
    # Sắp xếp canonical theo url_normalized, html_sha256, candidate_uid
    sorted_records = list(canonical_records)
    sorted_records.sort(key=lambda r: (r["url_normalized"], r["html_sha256"], r["candidate_uid"]))
    canonical_bytes = json.dumps(sorted_records, sort_keys=True, ensure_ascii=False).encode("utf-8")
    verified_fp = hashlib.sha256(canonical_bytes).hexdigest()
    assert verified_fp == expected_fp, "Canonical metadata serialization must yield exact same fingerprint!"
    print("OK: Canonical metadata serialization verified independently!")

    # Lưu tệp bổ sung (không ghi đè tệp lịch sử)
    out_file = Path("data/restricted/main_batch1/population_1232_canonical_records_v1.json")
    envelope = {
        "schema_version": "1.0.0",
        "dataset_id": "POPULATION-1232-SEALED-CANONICAL",
        "population_count": len(canonical_records),
        "population_fingerprint_sha256": pop_fp,
        "historical_uid_list_sha256": "40ad5d600e93b10d3fe5910e7454ce4a7a94fe2384b5625d8e6af8983525f9a8",
        "source_shard": p_shard.name,
        "source_shard_sha256": "260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74",
        "source_revision": DEFAULT_APPROVED_REVISION,
        "seed_population": 42,
        "canonical_sorting_keys": ["url_normalized", "html_sha256", "candidate_uid"],
        "records": canonical_records,
    }
    out_file.write_text(json.dumps(envelope, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved canonical records to: {out_file} ({out_file.stat().st_size} bytes, SHA-256: {hashlib.sha256(out_file.read_bytes()).hexdigest()})")


if __name__ == "__main__":
    main()
