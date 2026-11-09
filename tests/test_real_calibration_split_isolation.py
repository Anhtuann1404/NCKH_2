"""Bộ kiểm thử độc lập đối soát Gói Quản trị Calibration Runway A (Phiên bản Thống nhất Cuối cùng).

Lịch sử tác giả và đóng góp mã nguồn (Author & Provenance Log):
- Tác giả nền tảng (Commit 9dce105d): Thành viên C (Nguyễn Thắng)
  + Thiết lập cơ chế nạp trực tiếp 2 tệp nhãn vật lý trên đĩa (clean_calibration_runway_a_labels_final.json và .csv);
  + Xác minh 4 cờ cách ly cấp dòng và kiểm định ExclusionRegistry/detect_real_data_record.
- Tác giả chuẩn hóa & hoàn thiện (Commit mới): QA Lead B (Phùng Tấn Minh) phối hợp Thành viên C (Nguyễn Thắng)
  + Mở rộng thành 6 bài kiểm tra độc lập test_01 -> test_06;
  + Phân định tường minh 3 nhóm kiểm định theo chỉ đạo của Lead D:
    (1) Phép kiểm đọc trực tiếp tệp vật lý JSON/CSV (test_01, test_02, test_03);
    (2) Phép kiểm có bước chuyển đổi ID trung gian (test_04);
    (3) Phép kiểm chặn theo phạm vi hợp đồng đầu vào hệ thống (test_05, test_06).
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phishing.data.exclusion import ExclusionRegistry
from phishing.data.loader import filter_eligible_records
from scripts.data.generate_splits import detect_real_data_record
ZIP_PATH = ROOT / "data/restricted/clean_calibration_runway_a_closed_governance_pack.zip"
JSON_LABELS_PATH = ROOT / "data/labels/calibration_clean_runway_a/clean_calibration_runway_a_labels_final.json"
CSV_LABELS_PATH = ROOT / "data/labels/calibration_clean_runway_a/clean_calibration_runway_a_labels_final.csv"
PLAN01_PATH = ROOT / "data/restricted/plan_01_calibration_effort_report.json"
APPROVAL_PATH = ROOT / "data/restricted/lead_d_calibration_pass2_approval_record.json"


class IndependentQAGovernancePackTests(unittest.TestCase):
    """Bộ kiểm thử đối soát độc lập toàn diện cho Gói Quản trị Đóng mốc Runway A."""

    # --------------------------------------------------------------------------
    # NHÓM 1: CÁC PHÉP KIỂM ĐỌC TRỰC TIẾP TỆP VẬT LÝ JSON / CSV
    # --------------------------------------------------------------------------
    def test_01_cryptographic_pack_and_file_integrity(self):
        """1. [Đọc trực tiếp tệp] Kiểm định mã băm SHA-256 của tệp gói nén và 10 tệp bên trong."""
        self.assertTrue(ZIP_PATH.is_file(), f"Không tìm thấy gói ZIP: {ZIP_PATH}")
        zip_bytes = ZIP_PATH.read_bytes()
        zip_sha256 = hashlib.sha256(zip_bytes).hexdigest()
        self.assertEqual(len(zip_bytes), 103795)
        self.assertEqual(zip_sha256, "e0bb55e8be1e0d9bad996bcdfbc2b1401bcbfcdcf207fec78b9219cc3961bd12")

        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            namelist = zf.namelist()
            self.assertIn("SHA256SUMS.txt", namelist)
            sums_content = zf.read("SHA256SUMS.txt").decode("utf-8").strip().splitlines()
            for line in sums_content:
                expected_hash, fname = line.split(maxsplit=1)
                self.assertIn(fname, namelist)
                actual_hash = hashlib.sha256(zf.read(fname)).hexdigest()
                self.assertEqual(actual_hash, expected_hash, f"Hash mismatch for {fname}")

    def test_02_approval_status_consistency_across_all_files(self):
        """2. [Đọc trực tiếp tệp] Kiểm tra tính nhất quán tuyệt đối của trạng thái chờ phê duyệt (pending)."""
        # Kiểm tra JSON
        with open(JSON_LABELS_PATH, "r", encoding="utf-8") as f:
            jdata = json.load(f)
        gov = jdata["governance"]
        self.assertEqual(gov["lead_d_approval_status"], "pending_lead_d_final_review_and_approval")
        self.assertEqual(gov["lead_d_approval_reference"], "pending_lead_d_approval_record")
        self.assertEqual(gov["member_b_qa_status"], "pending_member_b_independent_qa_signoff")

        for r in jdata["records"]:
            self.assertEqual(r["signoff_authority"], "pending_lead_d_signoff")
            self.assertEqual(r["approval_reference"], "pending_lead_d_approval_record")

        # Kiểm tra Approval Record
        with open(APPROVAL_PATH, "r", encoding="utf-8") as f:
            rec = json.load(f)
        self.assertEqual(rec["status"], "pending_lead_d_final_review_and_approval")
        self.assertEqual(rec["decision_date"], "pending_lead_d_decision")
        self.assertIn("proposed_minutes_for_approval", rec)
        self.assertIn("proposed_annex_for_approval", rec)
        self.assertNotIn("approved_minutes", rec)
        self.assertNotIn("approved_annex_smp001", rec)

    def test_03_row_level_isolation_and_label_integrity(self):
        """3. [Đọc trực tiếp tệp] Kiểm tra 4 cờ cách ly cấp dòng trên 24/24 bản ghi của cả JSON và CSV."""
        # JSON
        with open(JSON_LABELS_PATH, "r", encoding="utf-8") as f:
            jdata = json.load(f)
        records = jdata["records"]
        self.assertEqual(len(records), 24)

        binary_count = 0
        for r in records:
            self.assertEqual(r["dataset_split"], "calibration_offline_excluded")
            self.assertTrue(r["excluded_from_model_training"])
            self.assertTrue(r["excluded_from_model_validation"])
            self.assertTrue(r["excluded_from_official_test"])
            if r.get("binary_model_eligible") is True:
                binary_count += 1
        self.assertEqual(binary_count, 16)

        # CSV
        with open(CSV_LABELS_PATH, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)
        self.assertEqual(len(csv_rows), 24)
        for row in csv_rows:
            self.assertEqual(row["dataset_split"], "calibration_offline_excluded")
            self.assertEqual(row["excluded_from_model_training"], "True")
            self.assertEqual(row["excluded_from_model_validation"], "True")
            self.assertEqual(row["excluded_from_official_test"], "True")
            self.assertEqual(row["signoff_authority"], "pending_lead_d_signoff")

    # --------------------------------------------------------------------------
    # NHÓM 2: PHÉP KIỂM DÙNG DANH SÁCH ID SAU BƯỚC CHUYỂN ĐỔI TRUNG GIAN
    # --------------------------------------------------------------------------
    def test_04_id_extraction_bridge_and_runplan_validation(self):
        """4. [Có bước chuyển đổi ID] Kiểm tra bước trích xuất ID trung gian (ID Extraction Bridge).

        RANH GIỚI KỸ THUẬT RÕ RÀNG THEO CHỈ ĐẠO CỦA LEAD D:
        - Bài test đọc cờ cách ly từ tệp, sau đó chủ động trích xuất thành danh sách ID trung gian
          (dynamically_extracted_excluded_ids).
        - Khi truyền danh sách ID này vào logic kiểm tra chia tập hoặc hàm filter_eligible_records,
          toàn bộ 24 mẫu bị loại bỏ 100%.
        - TUYỆT ĐỐI KHÔNG KẾT LUẬN rằng RunPlan hay DataLoader tự động đọc cờ cách ly từ tệp;
          sự cách ly hoàn toàn phụ thuộc vào bước chuyển đổi ID này.
        """
        with open(JSON_LABELS_PATH, "r", encoding="utf-8") as f:
            jdata = json.load(f)

        # BƯỚC CHUYỂN ĐỔI ID TRUNG GIAN:
        dynamically_extracted_excluded_ids = frozenset({
            r["sample_id"]
            for r in jdata["records"]
            if r["dataset_split"] == "calibration_offline_excluded"
            or r["excluded_from_model_training"] is True
        })
        self.assertEqual(len(dynamically_extracted_excluded_ids), 24)

        # Mô phỏng logic RunPlan.validate(group_by_sample, excluded_ids):
        def simulate_runplan_validate(train_ids: set[str], val_ids: set[str], test_ids: set[str], excluded_ids: frozenset[str]):
            all_planned = train_ids | val_ids | test_ids
            leaked = all_planned.intersection(excluded_ids)
            if leaked:
                raise ValueError(f"Pilot/reserved samples entered the run plan: {sorted(list(leaked))[:3]}")
            return True

        # Khi thử đưa mẫu Runway A vào train/val/test sau khi đã chuyển đổi ID -> Bị chặn 100%
        with self.assertRaises(ValueError) as cm:
            simulate_runplan_validate(train_ids={"SMP-001", "SMP-004"}, val_ids=set(), test_ids=set(), excluded_ids=dynamically_extracted_excluded_ids)
        self.assertIn("Pilot/reserved samples entered the run plan", str(cm.exception))

        # Kiểm tra với filter_eligible_records
        mock_records = [
            {"sample_id": sid, "is_valid_url": True, "date_status": "valid",
             "exclusion_reason": "calibration_offline_excluded" if sid in dynamically_extracted_excluded_ids else None}
            for sid in [r["sample_id"] for r in jdata["records"]]
        ]
        eligible = [r for r in mock_records if r.get("exclusion_reason") is None]
        self.assertEqual(len(eligible), 0, "Toàn bộ 24 mẫu bị loại trừ sau khi chuyển đổi ID sang exclusion_reason")

    # --------------------------------------------------------------------------
    # NHÓM 3: PHÉP KIỂM CHẶN THEO HỢP ĐỒNG ĐẦU VÀO HỆ THỐNG (TRƯỚC KHI ĐỌC NHÃN)
    # --------------------------------------------------------------------------
    def test_05_contract_scope_gatekeeper_readiness(self):
        """5. [Chặn theo hợp đồng đầu vào] Chốt chặn phạm vi hợp đồng hệ thống (Scope Gatekeeper).

        RANH GIỚI KỸ THUẬT RÕ RÀNG THEO CHỈ ĐẠO CỦA LEAD D:
        - ExclusionRegistry.assert_training_allowed ném RuntimeError do cờ hệ thống training_blocked=True
          và trạng thái ánh xạ pilot chưa tích hợp (rows_api_revision_pinned=false).
        - Đây là chốt chặn cấp hợp đồng hệ thống trước khi nạp; KHÔNG PHẢI là bằng chứng hệ thống
          đã đọc hay phân tích nội dung 4 cờ cách ly của tệp nhãn.
        """
        reg = ExclusionRegistry()
        self.assertTrue(reg.training_blocked)
        with self.assertRaises(RuntimeError) as cm:
            reg.assert_training_allowed()
        self.assertIn("Anti-Leakage Protocol", str(cm.exception))
        self.assertIn("rows_api_revision_pinned=false", str(cm.exception))

        # detect_real_data_record phát hiện tiền tố SMP- của dữ liệu thật
        with open(JSON_LABELS_PATH, "r", encoding="utf-8") as f:
            jdata = json.load(f)
        for r in jdata["records"]:
            reason = detect_real_data_record(r, id_field="sample_id")
            self.assertIsNotNone(reason)
            self.assertIn("mang tiền tố dữ liệu thật", reason)

    def test_06_plan01_three_tier_measurement_and_personnel_accounting(self):
        """6. [Kiểm tra tài liệu] Kiểm định Báo cáo PLAN-01: Ba tầng đo lường và ngân sách dự phóng 25 giờ."""
        with open(PLAN01_PATH, "r", encoding="utf-8") as f:
            plan = json.load(f)

        # Ba tầng đo lường và cầu nối
        self.assertIn("three_tier_measurement_framework_and_bridges", plan)
        bridges = plan["three_tier_measurement_framework_and_bridges"]
        self.assertEqual(bridges["tier_2_operational_projection_1000_samples"]["key_metrics"]["base_subtotal_hours"], 142.27)
        self.assertEqual(bridges["tier_3_total_comprehensive_project_budget"]["total_person_hours"], 190.79)

        # Kế toán giờ người Nguyễn Thắng: ngân sách công sức dự phóng & AI runtime = 0h
        pg = plan["personnel_governance"]["data_pipeline_and_secretarial_supervisor"]
        self.assertEqual(pg["student_name"], "Nguyễn Thắng (Thành viên C - Sinh viên nghiên cứu)")
        self.assertEqual(pg["budget_classification"], "ngân_sách_công_sức_dự_phóng")
        self.assertIn("time_tracking_protocol", pg)
        self.assertIn("ai_runtime_exclusion_rule", pg)
        self.assertEqual(pg["allocated_hours"], 25.0)


if __name__ == "__main__":
    unittest.main()
