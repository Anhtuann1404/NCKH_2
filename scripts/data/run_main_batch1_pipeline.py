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
import os
from pathlib import Path
import shutil
import sys
from typing import Any, Dict, List, Optional
import uuid

# Đảm bảo import được src/ và project root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from phishing.annotation.blind_view import assert_no_label_leak

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
    lot_id: str = "main_lot_batch_001",
) -> Dict[str, Any]:
    """Thực thi toàn bộ quy trình đóng gói và niêm phong Main Annotation Đợt 1 với Staging và Atomic Publishing."""
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
    p_pub = Path(public_artifacts_dir)
    p_ledger = Path(ledger_path)

    # 0. Kiểm tra cách ly Git TRƯỚC KHI XUẤT (Preflight Check)
    iso_preflight = verify_git_isolation()
    if iso_preflight.get("overall_status") != "PASS":
        raise RuntimeError(
            f"EXPORT BLOCKED: Kiểm tra cách ly Git thất bại trước khi đóng gói! {iso_preflight.get('conclusion', '')}"
        )

    # Sao lưu byte của Ledger cũ để khôi phục nguyên vẹn nếu xảy ra lỗi trong quá trình xuất gói
    ledger_bytes_backup = p_ledger.read_bytes() if p_ledger.exists() else None

    # Khởi tạo thư mục STAGING biệt lập trong data/restricted/ và artifacts/
    stage_uuid = uuid.uuid4().hex[:8]
    stage_base = p_rest.parent / f".staging_{lot_id}_{stage_uuid}"
    stage_rest = stage_base / "restricted"
    stage_pub = stage_base / "public"
    stage_rest.mkdir(parents=True, exist_ok=True)
    stage_pub.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Khởi tạo/tải Ledger
        ledger = LotManagementLedger(p_ledger)

        # 2. Chạy lấy mẫu ngẫu nhiên không hoàn lại
        res: SamplingResult = run_main_batch1_sampling(
            candidates,
            seed_lot_100=s_lot,
            seed_b_subset_30=s_b,
            seed_release_shuffle=s_shuf,
            blind_salt=b_salt,
            ledger=ledger,
            lot_id=lot_id,
            actor=actor,
        )

        # 3. Ghi toàn bộ hiện vật vào STAGING trước
        stg_mapping = stage_rest / "mapping_restricted.json"
        stg_mapping.write_text(json.dumps(res.mapping_restricted, indent=2, ensure_ascii=False), encoding="utf-8")

        stg_view_a = stage_rest / "blind_view_a.json"
        stg_view_a.write_text(json.dumps(res.blind_view_a_envelope, indent=2, ensure_ascii=False), encoding="utf-8")

        stg_view_b = stage_rest / "blind_view_b.json"
        stg_view_b.write_text(json.dumps(res.blind_view_b_envelope, indent=2, ensure_ascii=False), encoding="utf-8")

        stg_pop = stage_rest / "population_1232_sealed.json"
        pop_metadata = {
            "population_count": len(candidates),
            "population_hash": res.population_hash,
            "sealed_at_utc": datetime.now(timezone.utc).isoformat(),
            "candidates_uids": [
                c.get("candidate_uid") or c.get("sample_uid") or c.get("url")
                for c in candidates
            ],
        }
        stg_pop.write_text(json.dumps(pop_metadata, indent=2, ensure_ascii=False), encoding="utf-8")

        # Tính toán SHA-256 các tệp trong staging
        view_a_hash = hashlib.sha256(stg_view_a.read_bytes()).hexdigest()
        view_b_hash = hashlib.sha256(stg_view_b.read_bytes()).hexdigest()
        mapping_hash = hashlib.sha256(stg_mapping.read_bytes()).hexdigest()

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
        (stage_rest / "manifest_a.json").write_text(json.dumps(manifest_a, indent=2, ensure_ascii=False), encoding="utf-8")
        (stage_rest / "manifest_b.json").write_text(json.dumps(manifest_b, indent=2, ensure_ascii=False), encoding="utf-8")

        # Xuất Release Manifest công khai
        manifest = {
            "manifest_version": "1.0.0",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "lot_id": lot_id,
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
        stg_manifest = stage_pub / "main_batch1_release_manifest.json"
        stg_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        # 4. HẬU KIỂM (Postflight Checks) trên các file STAGING trước khi publish
        assert_no_label_leak(json.loads(stg_view_a.read_text(encoding="utf-8")))
        assert_no_label_leak(json.loads(stg_view_b.read_text(encoding="utf-8")))

        # Kiểm tra manifest công khai không rò rỉ nhãn hoặc mô hình
        stg_manifest_text = stg_manifest.read_text(encoding="utf-8")
        for forbidden in ("\"source_label\"", "\"model_score\"", "\"is_phish\""):
            if forbidden in stg_manifest_text:
                raise ValueError(f"Release manifest không được chứa trường nhãn: {forbidden}")

        iso_res = verify_git_isolation()
        if iso_res.get("overall_status") != "PASS":
            raise RuntimeError(f"EXPORT BLOCKED: Vi phạm quy tắc cách ly Git sau khi chuẩn bị staging! {iso_res.get('conclusion', '')}")

        # 5. ATOMIC PUBLISHING: Chuyển toàn bộ các tệp từ staging sang thư mục đích
        p_rest.mkdir(parents=True, exist_ok=True)
        p_pub.mkdir(parents=True, exist_ok=True)

        for f_src in stage_rest.iterdir():
            f_dst = p_rest / f_src.name
            f_tmp = p_rest / f".{f_src.name}_{stage_uuid}.tmp"
            shutil.copy2(f_src, f_tmp)
            os.replace(f_tmp, f_dst)

        for f_src in stage_pub.iterdir():
            f_dst = p_pub / f_src.name
            f_tmp = p_pub / f".{f_src.name}_{stage_uuid}.tmp"
            shutil.copy2(f_src, f_tmp)
            os.replace(f_tmp, f_dst)

        # Ghi nhận báo cáo kiểm toán cách ly chính thức
        verify_git_isolation(p_pub / "isolation_verification_report.json")

        return {
            "status": "SUCCESS",
            "manifest": manifest,
            "isolation_status": iso_res["overall_status"],
        }
    except Exception as exc:
        # Nếu có bất kỳ lỗi nào, khôi phục nguyên vẹn byte của ledger cũ
        if ledger_bytes_backup is not None:
            p_ledger.write_bytes(ledger_bytes_backup)
        elif p_ledger.exists():
            try:
                p_ledger.unlink()
            except OSError:
                pass
        raise exc
    finally:
        # Dọn dẹp triệt để thư mục staging
        if stage_base.exists():
            shutil.rmtree(stage_base, ignore_errors=True)
