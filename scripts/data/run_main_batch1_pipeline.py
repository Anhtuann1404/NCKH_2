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
from typing import Any, Dict, List, Optional

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


def load_private_sampling_params(
    config_path: Path | str = "data/restricted/seeds_and_salts.json",
) -> Dict[str, Any]:
    """Tải cấu hình seed và salt bí mật từ thư mục restricted hoặc biến môi trường."""
    p = Path(config_path)
    res = {}
    if p.exists():
        try:
            res = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass

    import os
    if "MAIN_BLIND_SALT" in os.environ:
        res["blind_salt"] = os.environ["MAIN_BLIND_SALT"]
    if "MAIN_SEED_LOT_100" in os.environ:
        res["seed_lot_100"] = int(os.environ["MAIN_SEED_LOT_100"])
    if "MAIN_SEED_B_SUBSET_30" in os.environ:
        res["seed_b_subset_30"] = int(os.environ["MAIN_SEED_B_SUBSET_30"])
    if "MAIN_SEED_RELEASE_SHUFFLE" in os.environ:
        res["seed_release_shuffle"] = int(os.environ["MAIN_SEED_RELEASE_SHUFFLE"])

    return res


def export_main_batch1(
    candidates: List[Dict[str, Any]],
    output_dir_restricted: Path | str = "data/restricted/main_batch1",
    public_artifacts_dir: Path | str = "artifacts",
    *,
    seed_lot_100: Optional[int] = None,
    seed_b_subset_30: Optional[int] = None,
    seed_release_shuffle: Optional[int] = None,
    blind_salt: Optional[str] = None,
    ledger_path: Path | str = "data/restricted/main_annotation_lot_management_ledger.json",
    actor: str = "Member C (Nguyễn Thắng)",
) -> Dict[str, Any]:
    """Thực thi toàn bộ quy trình đóng gói và niêm phong Main Annotation Đợt 1."""
    # Nạp tham số bảo mật từ cấu hình hạn chế hoặc biến môi trường nếu không truyền trực tiếp
    cfg = load_private_sampling_params()
    s_lot = seed_lot_100 if seed_lot_100 is not None else cfg.get("seed_lot_100")
    s_b = seed_b_subset_30 if seed_b_subset_30 is not None else cfg.get("seed_b_subset_30")
    s_shuf = seed_release_shuffle if seed_release_shuffle is not None else cfg.get("seed_release_shuffle")
    b_salt = blind_salt if blind_salt is not None else cfg.get("blind_salt")

    if not b_salt or s_lot is None or s_b is None or s_shuf is None:
        raise ValueError(
            "BẮT BUỘC: blind_salt và các seed lựa chọn (seed_lot_100, seed_b_subset_30, seed_release_shuffle) "
            "phải được cung cấp qua tham số, biến môi trường (MAIN_BLIND_SALT, ...) hoặc tệp hạn chế data/restricted/seeds_and_salts.json!"
        )

    p_rest = Path(output_dir_restricted)
    p_rest.mkdir(parents=True, exist_ok=True)
    p_pub = Path(public_artifacts_dir)
    p_pub.mkdir(parents=True, exist_ok=True)

    # 0. Kiểm tra cách ly Git TRƯỚC KHI XUẤT (Fail-closed)
    iso_preflight = verify_git_isolation()
    if iso_preflight["overall_status"] != "PASS":
        raise RuntimeError(
            f"EXPORT BLOCKED: Kiểm tra cách ly Git thất bại trước khi đóng gói! {iso_preflight['conclusion']}"
        )

    # 1. Khởi tạo/tải Ledger
    ledger = LotManagementLedger(ledger_path)

    # 2. Chạy lấy mẫu ngẫu nhiên không hoàn lại
    res: SamplingResult = run_main_batch1_sampling(
        candidates,
        seed_lot_100=s_lot,
        seed_b_subset_30=s_b,
        seed_release_shuffle=s_shuf,
        blind_salt=b_salt,
        ledger=ledger,
        lot_id="main_lot_batch_001",
        actor=actor,
    )

    # 3. Lưu trữ gói hạn chế trong data/restricted/
    mapping_file = p_rest / "mapping_restricted.json"
    mapping_file.write_text(json.dumps(res.mapping_restricted, indent=2, ensure_ascii=False), encoding="utf-8")

    view_a_file = p_rest / "blind_view_a.json"
    view_a_file.write_text(json.dumps(res.blind_view_a_envelope, indent=2, ensure_ascii=False), encoding="utf-8")

    view_b_file = p_rest / "blind_view_b.json"
    view_b_file.write_text(json.dumps(res.blind_view_b_envelope, indent=2, ensure_ascii=False), encoding="utf-8")

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

    # Tạo role-specific manifests cho Annotator A và B
    codebook_path = Path("docs/CODEBOOK_V1_1.md")
    dictionary_path = Path("configs/dictionary_v1.json")
    cb_sha256 = hashlib.sha256(codebook_path.read_bytes()).hexdigest() if codebook_path.exists() else ""
    dict_sha256 = hashlib.sha256(dictionary_path.read_bytes()).hexdigest() if dictionary_path.exists() else ""

    manifest_a = {
        "dataset_id": "MAIN-BATCH1-A",
        "sample_count": 100,
        "sampling_plan_version": "MAIN-PLAN-V1.0",
        "codebook_version": "1.1.0",
        "codebook_status": "locked",
        "dictionary_version": "1.0.0",
        "dictionary_status": "locked",
        "acceptance": {"B": "pending", "D": "pending"},
        "ready_for_annotation": False,
        "blind_view_sha256": view_a_hash,
        "codebook_sha256": cb_sha256,
        "dictionary_sha256": dict_sha256,
        "blind_contract_version": "1.2.0",
    }
    manifest_b = {
        "dataset_id": "MAIN-BATCH1-B",
        "sample_count": 30,
        "sampling_plan_version": "MAIN-PLAN-V1.0",
        "codebook_version": "1.1.0",
        "codebook_status": "locked",
        "dictionary_version": "1.0.0",
        "dictionary_status": "locked",
        "acceptance": {"B": "pending", "D": "pending"},
        "ready_for_annotation": False,
        "blind_view_sha256": view_b_hash,
        "codebook_sha256": cb_sha256,
        "dictionary_sha256": dict_sha256,
        "blind_contract_version": "1.2.0",
    }
    (p_rest / "manifest_a.json").write_text(json.dumps(manifest_a, indent=2, ensure_ascii=False), encoding="utf-8")
    (p_rest / "manifest_b.json").write_text(json.dumps(manifest_b, indent=2, ensure_ascii=False), encoding="utf-8")

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

    # 6. Kiểm tra cách ly Git sau khi ghi
    iso_res = verify_git_isolation(p_pub / "isolation_verification_report.json")
    if iso_res["overall_status"] != "PASS":
        raise RuntimeError("EXPORT BLOCKED: Vi phạm quy tắc cách ly Git sau khi xuất tệp!")

    return {
        "status": "SUCCESS",
        "manifest": manifest,
        "isolation_status": iso_res["overall_status"],
    }
