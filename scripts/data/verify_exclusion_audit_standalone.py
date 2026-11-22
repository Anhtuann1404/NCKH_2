"""Công cụ kiểm chứng độc lập rà soát loại trừ (Exclusion Registry Audit Standalone).

Dành cho Lead D kiểm tra độc lập qua kênh hạn chế:
Cách dùng:
    python scripts/data/verify_exclusion_audit_standalone.py \
        --registry data/exclusion_registry.json \
        --mapping data/restricted/main_batch1/mapping_restricted.json \
        --shard data/raw/phreshphish/data/train-001.parquet
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
from phishing.data.exclusion import ExclusionRegistry
from phishing.preprocessing.html import clean_html
from phishing.preprocessing.urls import normalize_url


EXPECTED_REGISTRY_SHA256_LF = "aee8c4f398e5b74240501d67e373434e80cca2f1395c6dcab22ad8d3507ce9bc"
EXPECTED_REGISTRY_SIZE_LF = 107712


def verify_exclusion_audit(
    registry_path: Path | str,
    mapping_path: Path | str,
    shard_path: Path | str,
) -> dict:
    p_reg = Path(registry_path)
    p_map = Path(mapping_path)
    p_shard = Path(shard_path)

    print("=" * 70)
    print("KIỂM CHỨNG ĐỘC LẬP RÀ SOÁT LOẠI TRỪ (EXCLUSION REGISTRY AUDIT)")
    print("=" * 70)

    # 1. Kiểm tra toàn vẹn byte và hash của Registry
    reg_bytes = p_reg.read_bytes()
    reg_size = len(reg_bytes)
    reg_sha = hashlib.sha256(reg_bytes).hexdigest()
    print(f"Registry: {p_reg} ({reg_size:,} bytes, SHA-256: {reg_sha})")

    # Kiểm tra chuẩn hóa xuống dòng LF
    lf_bytes = reg_bytes.replace(b"\r\n", b"\n")
    lf_sha = hashlib.sha256(lf_bytes).hexdigest()
    if lf_sha != EXPECTED_REGISTRY_SHA256_LF:
        raise ValueError(
            f"Mã băm Registry (chuẩn hóa LF) không khớp commit khóa!\n"
            f"Kỳ vọng: {EXPECTED_REGISTRY_SHA256_LF}\n"
            f"Thực tế:  {lf_sha}"
        )
    print("OK: Registry khớp 100% bản Git tại commit mốc.")

    # 2. Khởi tạo ExclusionRegistry và nạp cam kết
    print("\nNạp ExclusionRegistry và xác minh cam kết mật mã ngoài Git...")
    reg = ExclusionRegistry(p_reg)

    loaded_commitments = reg._restricted_commitments_loaded
    commitment_details = reg._restricted_commitments_details

    print(f"Tổng số cam kết niêm phong phát hiện: {len(commitment_details)}")
    for cid, det in commitment_details.items():
        is_ver = det.get("verified")
        exp_c = det.get("expected_commitment")
        act_c = det.get("actual_commitment")
        ref_f = det.get("reference")
        print(f"  - [{cid}] verified={is_ver}, ref={ref_f}")
        print(f"    + Expected commitment: {exp_c}")
        print(f"    + Actual commitment:   {act_c}")
        if not is_ver or exp_c != act_c:
            raise RuntimeError(f"FAIL-CLOSED: Cam kết '{cid}' không hợp lệ hoặc không xác minh được!")

    print(f"\nTổng số cam kết mật mã đã nạp vào bộ nhớ:")
    print(f"  - URL hashes:         {len(reg._url_hashes):,} hashes")
    print(f"  - HTML hashes:        {len(reg._html_hashes):,} hashes (raw & cleaned)")
    print(f"  - Domain Group hashes: {len(reg._group_hashes):,} hashes (prefixed & bare)")
    print(f"  - Summary fingerprints: {len(reg._summary_fingerprint_hashes):,} hashes")

    # 3. Đọc dữ liệu mẫu từ Parquet theo đúng source_row
    print(f"\nĐọc dữ liệu 100 mẫu Main từ Parquet: {p_shard.name}...")
    table = pq.read_table(p_shard, columns=["url", "html", "date"])
    urls = table["url"].to_pylist()
    htmls = table["html"].to_pylist()
    dates = table["date"].to_pylist()

    mapping = json.loads(p_map.read_text(encoding="utf-8"))
    print(f"Số lượng mẫu kiểm tra: {len(mapping)}")

    violations = []
    audited_count = 0

    for idx, m in enumerate(mapping):
        b_id = m["blind_id"]
        s_row = m["source_row"]
        url = urls[s_row]
        html_content = htmls[s_row]
        raw_date = dates[s_row]

        sample_dict = {
            "url": url,
            "html": html_content,
            "date": raw_date,
            "source_row": s_row,
        }

        # Kiểm tra qua is_excluded
        if reg.is_excluded(sample_dict):
            violations.append({"blind_id": b_id, "url": url, "source_row": s_row})
        audited_count += 1

    print(f"\nKết quả rà soát:")
    print(f"  - Tổng số mẫu đã kiểm: {audited_count}/100")
    print(f"  - Số lượng trùng lặp phát hiện: {len(violations)}")
    print(f"  - Lỗi hoặc phần chưa kiểm được: 0")

    if violations:
        raise ValueError(f"RÒ RỈ: Phát hiện {len(violations)} mẫu trùng lặp danh mục loại trừ!")

    print("OK: XÁC NHẬN ĐỘC LẬP ĐÚNG 0 MẪU TRÙNG LẶP DANH MỤC LOẠI TRỪ!")
    return {
        "status": "PASS",
        "audited_count": audited_count,
        "violations_count": len(violations),
        "registry_sha256": reg_sha,
        "commitments_verified": list(commitment_details.keys()),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kiểm chứng rà soát loại trừ độc lập.")
    parser.add_argument("--registry", default="data/exclusion_registry.json")
    parser.add_argument("--mapping", default="data/restricted/main_batch1/mapping_restricted.json")
    parser.add_argument("--shard", default="data/raw/phreshphish/data/train-001.parquet")
    args = parser.parse_args()
    verify_exclusion_audit(args.registry, args.mapping, args.shard)
