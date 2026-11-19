"""Kịch bản thực thi chuỗi vận hành Main Annotation Đợt 1 đầu-cuối (End-to-End Runner).

Tuân thủ nghiêm ngặt chỉ đạo của Lead D:
1. Quần thể 1.232 ứng viên đã khóa từ shard train-001.parquet qua Gates 0–3 (seed 42).
2. Lấy mẫu ngẫu nhiên không hoàn lại 100 mẫu Main cho A (seed 1017).
3. Rút ngẫu nhiên 30 mẫu cho B từ lô 100 để tính Cohen's Kappa chính (seed 2042).
4. Xáo trộn thứ tự hiển thị độc lập cho A và B (seed 2026).
5. Sinh ID trung tính BLIND-xxxxxxxx (8 hex).
6. Khởi tạo và ghi nhận vào Sổ cái quản lý lô append-only: data/restricted/main_annotation_lot_management_ledger.json.
7. Lưu ánh xạ hạn chế tại data/restricted/main_batch1/mapping_restricted.json.
8. Xuất gói Blind View v1.2.0 cho A (100 mẫu) và B (30 mẫu) trong thư mục hạn chế.
9. Xuất Báo cáo Release Manifest công khai tại artifacts/main_batch1_release_manifest.json.
10. Kiểm tra cách ly Git thực tế (Git Isolation Verification).
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

# Đảm bảo import được src/ và project root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from phishing.data.lot_ledger import LotManagementLedger
from phishing.data.main_sampling import (
    SamplingResult,
    compute_population_fingerprint,
    compute_seed_commitment,
    run_main_batch1_sampling,
)
from scripts.data.verify_git_isolation import verify_git_isolation


DEFAULT_SEED_POPULATION = 42
DEFAULT_SEED_LOT_100 = 1017
DEFAULT_SEED_B_SUBSET_30 = 2042
DEFAULT_SEED_RELEASE_SHUFFLE = 2026
DEFAULT_BLIND_SALT = "nckh2_main_batch1_blind_salt_secure_2026"


def export_main_batch1(
    candidates: List[Dict[str, Any]],
    output_dir_restricted: Path | str = "data/restricted/main_batch1",
    public_artifacts_dir: Path | str = "artifacts",
    *,
    seed_lot_100: int = DEFAULT_SEED_LOT_100,
    seed_b_subset_30: int = DEFAULT_SEED_B_SUBSET_30,
    seed_release_shuffle: int = DEFAULT_SEED_RELEASE_SHUFFLE,
    blind_salt: str = DEFAULT_BLIND_SALT,
    ledger_path: Path | str = "data/restricted/main_annotation_lot_management_ledger.json",
    actor: str = "Member C (Nguyễn Thắng)",
) -> Dict[str, Any]:
    """Thực thi toàn bộ quy trình đóng gói và niêm phong Main Annotation Đợt 1."""
    p_rest = Path(output_dir_restricted)
    p_rest.mkdir(parents=True, exist_ok=True)
    p_pub = Path(public_artifacts_dir)
    p_pub.mkdir(parents=True, exist_ok=True)

    # 1. Khởi tạo/tải Ledger
    ledger = LotManagementLedger(ledger_path)

    # 2. Chạy lấy mẫu ngẫu nhiên không hoàn lại
    res: SamplingResult = run_main_batch1_sampling(
        candidates,
        seed_lot_100=seed_lot_100,
        seed_b_subset_30=seed_b_subset_30,
        seed_release_shuffle=seed_release_shuffle,
        blind_salt=blind_salt,
        ledger=ledger,
        lot_id="main_lot_batch_001",
        actor=actor,
    )

    # 3. Lưu trữ gói hạn chế trong data/restricted/
    mapping_file = p_rest / "mapping_restricted.json"
    mapping_file.write_text(json.dumps(res.mapping_restricted, indent=2, ensure_ascii=False), encoding="utf-8")

    view_a_file = p_rest / "blind_view_a.json"
    view_a_file.write_text(json.dumps(res.blind_view_a, indent=2, ensure_ascii=False), encoding="utf-8")

    view_b_file = p_rest / "blind_view_b.json"
    view_b_file.write_text(json.dumps(res.blind_view_b, indent=2, ensure_ascii=False), encoding="utf-8")

    # Lưu danh sách quần thể niêm phong (dạng restricted)
    pop_file = p_rest / "population_1232_sealed.json"
    pop_metadata = {
        "population_count": len(candidates),
        "population_hash": res.population_hash,
        "sealed_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidates_uids": [
            c.get("candidate_uid") or c.get("sample_uid") or c.get("url")
            for c in candidates
        ],
    }
    pop_file.write_text(json.dumps(pop_metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    # 4. Tính toán SHA-256 các tệp
    view_a_hash = hashlib.sha256(view_a_file.read_bytes()).hexdigest()
    view_b_hash = hashlib.sha256(view_b_file.read_bytes()).hexdigest()
    mapping_hash = hashlib.sha256(mapping_file.read_bytes()).hexdigest()

    # 5. Xuất Release Manifest công khai (tuyệt đối không chứa ID nguồn hay mapping)
    manifest = {
        "manifest_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "lot_id": "main_lot_batch_001",
        "actor": actor,
        "contract_versions": {
            "codebook_version": "1.1.0",
            "blind_contract_version": "1.2.0",
        },
        "population": {
            "source_shard": "data/raw/phreshphish/data/train-001.parquet",
            "source_revision": "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a",
            "candidate_count": res.population_count,
            "population_fingerprint_sha256": res.population_hash,
            "seed_population": DEFAULT_SEED_POPULATION,
        },
        "sampling_specification": {
            "method": "Simple Random Sampling without Replacement (SRS)",
            "lot_size_a": 100,
            "b_subset_size": 30,
            "seed_commitment_sha256": res.seed_commitment,
            "id_format": "BLIND-xxxxxxxx (8 hex chars)",
        },
        "governance_flags": {
            "main_annotation_status": "LOCKED",
            "training_blocked": True,
            "official_test_used": False,
        },
        "restricted_package_fingerprints": {
            "blind_view_a_sha256": view_a_hash,
            "blind_view_b_sha256": view_b_hash,
            "mapping_restricted_sha256": mapping_hash,
            "ledger_event_sequence": res.ledger_event_seq,
        },
    }

    manifest_file = p_pub / "main_batch1_release_manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    # 6. Kiểm tra cách ly Git thực tế
    iso_res = verify_git_isolation(p_pub / "isolation_verification_report.json")

    return {
        "status": "SUCCESS",
        "manifest": manifest,
        "isolation_status": iso_res["overall_status"],
    }
