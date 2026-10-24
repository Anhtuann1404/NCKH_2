import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]


def update_exclusion_registry():
    candidates_file = ROOT / "data/clean_calibration_candidates.json"
    registry_file = ROOT / "data/exclusion_registry.json"
    leak_audit_file = ROOT / "data/source_audit/clean_calibration_git_leak_audit.json"

    candidates_data = json.loads(candidates_file.read_text(encoding="utf-8"))
    registry_data = json.loads(registry_file.read_text(encoding="utf-8"))

    # Kiểm tra xem batch này đã tồn tại chưa
    existing_ids = {e["exclusion_id"] for e in registry_data["exclusions"]}
    batch_id = "EXCL-CALIB-CLEAN-32-EXPOSED-ON-GIT"

    excluded_samples = []
    audit_samples = []

    for c in candidates_data["candidates"]:
        loc = c["locator"]
        sample_entry = {
            "sample_id": c["candidate_id"],
            "relative_path": loc["relative_path"],
            "row_offset": loc["row_offset"],
            "url_sha256": c["url_sha256"],
            "normalized_url_sha256": c["normalized_url_sha256"],
            "html_sha256": c["html_sha256"],
            "group_sha256": c["group_sha256"],
            "group_id": c.get("group_id", "unknown"),
            "source_date": c.get("source_date", ""),
            "role": c.get("role", "main_24"),
        }
        excluded_samples.append(sample_entry)
        audit_samples.append({
            "candidate_id": c["candidate_id"],
            "role": c.get("role", "main_24"),
            "locator": loc,
            "url_sha256": c["url_sha256"],
            "html_sha256": c["html_sha256"],
            "group_id": c.get("group_id", "unknown"),
        })

    if batch_id not in existing_ids:
        new_batch = {
            "exclusion_id": batch_id,
            "dataset_id": "CALIBRATION-CLEAN-32-EXPOSED",
            "source": "phreshphish",
            "split": "train",
            "source_metadata_revision": "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a",
            "rows_api_revision_pinned": False,
            "mapping_status": "mapped_to_shards",
            "action": "permanently_exclude_from_train_val_test",
            "n_samples": len(excluded_samples),
            "reason": "32 ứng viên hiệu chuẩn sạch (24 chính + 8 dự phòng) vô tình xuất hiện locator trên Git repository tại commit 226d422. Loại trừ vĩnh viễn khỏi toàn bộ tập huấn luyện, xác thực và kiểm thử (M0-M3) để phòng ngừa nguy cơ rò rỉ và bảo vệ nguyên tắc blind annotation tuyệt đối.",
            "samples": excluded_samples,
        }

        registry_data["exclusions"].append(new_batch)
        registry_data["total_excluded_entries"] = len(registry_data["exclusions"])
        registry_data["total_excluded_samples"] = sum(e["n_samples"] for e in registry_data["exclusions"])
        registry_data["updated_at_utc"] = datetime.now(timezone.utc).isoformat()

        registry_file.write_text(json.dumps(registry_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"-> Đã cập nhật exclusion_registry.json: {registry_data['total_excluded_entries']} lô, {registry_data['total_excluded_samples']} mẫu.")

    # Cập nhật tệp kiểm toán git leak
    leak_audit = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "audit_id": "CLEAN-CALIBRATION-GIT-LEAK-AUDIT-20261024",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "leak_contained_and_remediated",
        "governance": {
            "ready_for_annotation": False,
            "training_blocked": True,
            "force_push_used": False,
            "audit_trail_preserved": True,
        },
        "leak_incident": {
            "file_path": "data/clean_calibration_candidates.json",
            "first_committed_commit": "226d4226e5e84acd3437dd4573ca0b5d9d593c5b",
            "second_committed_commit": "fefb89ee5e11043efeb6cb45c0882ef9ff8ee301",
            "branch": "feat/c-calibration-v1-1-4-adjudication",
            "samples_exposed_count": len(audit_samples),
            "composition": "24 main samples + 8 reserve samples",
            "exposure_risk_assessment": "Tệp không chứa nhãn phân loại (label), nhưng chứa thông tin locator định vị dòng (relative_path và row_offset trong 2 shard nguồn train-000.parquet và train-055.parquet). Điều này tạo nguy cơ lộ mẫu nếu người gán nhãn hoặc bên thứ ba truy ngược lại dòng raw parquet. Để bảo vệ tính toàn vẹn của giao thức mù đôi (double-blind annotation), toàn bộ 32 mẫu này bị đình chỉ phát hành ngay lập tức.",
        },
        "remediation_actions": [
            {
                "step": 1,
                "action": "halt_blind_view_release",
                "detail": "Đình chỉ hoàn toàn việc xuất và bàn giao Blind View của 32 ứng viên đợt A. Đánh dấu đợt chọn này là không dùng cho Pass 1 sạch.",
            },
            {
                "step": 2,
                "action": "preserve_git_history",
                "detail": "Không thực hiện git push --force hay rewrite history; giữ nguyên 2 commit 226d422 và fefb89e làm bằng chứng kiểm toán độc lập.",
            },
            {
                "step": 3,
                "action": "register_in_exclusion_registry",
                "detail": "Đăng ký toàn bộ 32 mẫu bị lộ vào data/exclusion_registry.json với mã lô EXCL-CALIB-CLEAN-32-EXPOSED-ON-GIT. Loại trừ vĩnh viễn khỏi toàn bộ tập huấn luyện, xác thực và kiểm thử (M0-M3).",
            },
            {
                "step": 4,
                "action": "untrack_from_git_and_ignore",
                "detail": "Thực hiện 'git rm --cached' để gỡ tệp khỏi theo dõi của Git và cập nhật .gitignore nhằm ngăn chặn mọi tệp locator/ứng viên chi tiết bị commit lên Git trong tương lai.",
            },
            {
                "step": 5,
                "action": "rerun_selection_with_locked_seeds",
                "detail": "Thực hiện tuyển chọn lại đợt mới (Đợt B: 24 chính + 8 dự phòng) với seed 20261027, loại trừ toàn bộ 180 mẫu (148 mẫu cũ + 32 mẫu lộ). Lưu trữ tệp locator trong khu vực hạn chế ngoài Git.",
            },
        ],
        "affected_samples": audit_samples,
    }
    leak_audit_file.write_text(json.dumps(leak_audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"-> Đã ghi nhận báo cáo chi tiết: {leak_audit_file}")


if __name__ == "__main__":
    update_exclusion_registry()
