"""
Independent QA Verification Test Suite for Calibration Runway A Closed Governance Package.
Author: Phùng Tấn Minh (Member B - QA Lead & Nhóm trưởng)
Target Package: clean_calibration_runway_a_closed_governance_pack.zip (103.635 bytes)
Target Hash: cedade7e2ab090b6ec4e20fcedb4038f4c79684a360905ca96aa9732049ee0e3

This test suite rigorously verifies:
1. Cryptographic integrity of the zip and all 10 internal member files against SHA256SUMS.txt.
2. Complete consistency of approval statuses (strictly pending Lead D's review across all files).
3. Exact row-level isolation on all 24 records across both exported JSON and CSV physical files.
4. Two-step ID extraction bridge to RunPlan.validate (explicitly acknowledging the intermediate extraction step).
5. Input readiness contract gatekeeper (explicitly separating contract scope rejection from label flag inspection).
6. Plan-01 three-tier measurement framework, student human hours accounting, and SMP-001 sensitivity analysis.
"""

import csv
import hashlib
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

# Đưa thư mục src vào sys.path để gọi trực tiếp các module mã nguồn THẬT của dự án
sys.path.insert(0, os.path.abspath('src'))

from phishing.training.plan import RunPlan
from phishing.training.readiness import check_training_inputs


class IndependentQAGovernancePackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack_path = Path('data/restricted/clean_calibration_runway_a_closed_governance_pack.zip')
        cls.json_labels_path = Path('data/restricted/clean_calibration_runway_a_labels_final.json')
        cls.csv_labels_path = Path('data/restricted/clean_calibration_runway_a_labels_final.csv')
        cls.approval_record_path = Path('data/restricted/lead_d_calibration_pass2_approval_record.json')
        cls.plan01_path = Path('data/restricted/plan_01_calibration_effort_report.json')

        # Đọc dữ liệu trực tiếp từ 2 tệp xuất trên đĩa
        with open(cls.json_labels_path, 'r', encoding='utf-8') as f:
            cls.labels_json_data = json.load(f)
        cls.records_json = cls.labels_json_data['records']

        with open(cls.csv_labels_path, 'r', encoding='utf-8-sig') as f:
            cls.records_csv = list(csv.DictReader(f))

        with open(cls.approval_record_path, 'r', encoding='utf-8') as f:
            cls.approval_record = json.load(f)

        with open(cls.plan01_path, 'r', encoding='utf-8') as f:
            cls.plan01 = json.load(f)

    def test_01_cryptographic_pack_and_file_integrity(self):
        """1. Kiểm định mã băm SHA-256 của tệp gói nén và toàn bộ 10 tệp bên trong."""
        # Kiểm tra gói nén
        pack_bytes = self.pack_path.read_bytes()
        pack_hash = hashlib.sha256(pack_bytes).hexdigest()
        self.assertEqual(len(pack_bytes), 103635, "Dung lượng gói ZIP phải đúng 103.635 bytes")
        self.assertEqual(pack_hash, "cedade7e2ab090b6ec4e20fcedb4038f4c79684a360905ca96aa9732049ee0e3")

        # Kiểm tra nội dung bên trong ZIP và đối soát SHA256SUMS.txt
        with zipfile.ZipFile(self.pack_path, 'r') as z:
            sha_sums_text = z.read('SHA256SUMS.txt').decode('utf-8')
            expected_hashes = {}
            for line in sha_sums_text.strip().splitlines():
                if line.strip():
                    h, name = line.split(maxsplit=1)
                    expected_hashes[name.strip()] = h.strip()

            for info in z.infolist():
                if info.filename == 'SHA256SUMS.txt':
                    continue
                file_data = z.read(info.filename)
                file_hash = hashlib.sha256(file_data).hexdigest()
                self.assertIn(info.filename, expected_hashes, f"Tệp {info.filename} không có trong SHA256SUMS.txt")
                self.assertEqual(file_hash, expected_hashes[info.filename], f"Mã băm tệp {info.filename} không khớp")

        # Khẳng định 4 tệp bất biến đã ký giữ nguyên 100%
        self.assertEqual(expected_hashes['clean_calibration_adjudication_minutes_draft.json'],
                         '73e29a20cca394c2e145008c74f0172ac69292ecc81b52844642dc331dc6e04b')
        self.assertEqual(expected_hashes['clean_calibration_annex_smp001_audit.json'],
                         'b46bc2ada53e5f6d3cb03b1a57f6dce7feeade0de7f696ff95fc7082033e6577')
        self.assertEqual(expected_hashes['intake_pass1_A_1c60d10a.jsonl'],
                         '1c60d10ac4056679d8aafe2b13dcf4f00ffc0f332d34f5413f4b922164eac7f1')
        self.assertEqual(expected_hashes['intake_pass1_B_6069f61c.jsonl'],
                         '6069f61c5550f39e2aa39158ec0d3f183c01198b5b0d6e0479ab792bd15cc3f0')

    def test_02_approval_status_consistency_across_all_files(self):
        """2. Kiểm tra tính nhất quán tuyệt đối của trạng thái chờ phê duyệt (pending) trên toàn bộ gói."""
        # Hồ sơ phê duyệt
        self.assertEqual(self.approval_record['status'], 'pending_lead_d_final_review_and_approval')
        self.assertEqual(self.approval_record['decision_date'], 'pending_lead_d_decision')
        self.assertNotIn('approved_minutes', self.approval_record)
        self.assertNotIn('approved_annex_smp001', self.approval_record)
        self.assertIn('proposed_minutes_for_approval', self.approval_record)
        self.assertIn('proposed_annex_for_approval', self.approval_record)

        # Metadata tệp nhãn JSON
        gov = self.labels_json_data['governance']
        self.assertEqual(gov['lead_d_approval_status'], 'pending_lead_d_final_review_and_approval')
        self.assertEqual(gov['lead_d_approval_reference'], 'pending_lead_d_approval_record')
        self.assertEqual(gov['lead_d_approval_sha256'], 'pending_lead_d_decision')
        self.assertEqual(gov['member_b_qa_status'], 'pending_member_b_independent_qa_signoff')

        # Cấp bản ghi trên toàn bộ 24 dòng JSON và CSV
        for r_json, r_csv in zip(self.records_json, self.records_csv):
            self.assertEqual(r_json['sample_id'], r_csv['sample_id'])
            self.assertEqual(r_json['signoff_authority'], 'pending_lead_d_signoff')
            self.assertEqual(r_json['approval_reference'], 'pending_lead_d_approval_record')
            self.assertEqual(r_csv['signoff_authority'], 'pending_lead_d_signoff')
            self.assertEqual(r_csv['approval_reference'], 'pending_lead_d_approval_record')

    def test_03_row_level_isolation_and_label_integrity(self):
        """3. Kiểm tra 4 cờ cách ly cấp dòng và tính chính xác của 24 bản ghi nhãn."""
        self.assertEqual(len(self.records_json), 24)
        self.assertEqual(len(self.records_csv), 24)

        final_labels = [r['final_class_label'] for r in self.records_json]
        self.assertEqual(final_labels.count('benign'), 11)
        self.assertEqual(final_labels.count('phishing'), 5)
        self.assertEqual(final_labels.count('insufficient_evidence'), 2)
        self.assertEqual(final_labels.count(None), 6)  # 6 ca pending evidence

        eligible_records = [r for r in self.records_json if r.get('binary_model_eligible') is True]
        self.assertEqual(len(eligible_records), 16, "Chính xác 16 mẫu có binary_model_eligible=True")

        for r in self.records_json:
            self.assertEqual(r['dataset_split'], 'calibration_offline_excluded')
            self.assertTrue(r['excluded_from_model_training'])
            self.assertTrue(r['excluded_from_model_validation'])
            self.assertTrue(r['excluded_from_official_test'])

        for r in self.records_csv:
            self.assertEqual(r['dataset_split'], 'calibration_offline_excluded')
            self.assertIn(r['excluded_from_model_training'], ['True', 'true', True])
            self.assertIn(r['excluded_from_model_validation'], ['True', 'true', True])
            self.assertIn(r['excluded_from_official_test'], ['True', 'true', True])

    def test_04_id_extraction_bridge_and_runplan_validation(self):
        """4. Kiểm tra có bước chuyển đổi ID trung gian (ID Extraction Bridge):
        Đọc 2 tệp xuất vật lý (clean_calibration_runway_a_labels_final.json và .csv),
        trích xuất danh sách sample_id mang cờ excluded_from_model_training=True,
        rồi truyền tập ID này vào RunPlan.validate(..., excluded_ids=...).

        LƯU Ý PHẠM VI KỸ THUẬT RÕ RÀNG:
        RunPlan.validate chỉ nhận đối số chuỗi ID (excluded_ids: frozenset[str]),
        nó KHÔNG tự động đọc tệp hoặc tự nhận biết 4 trường cờ cách ly. Việc bảo vệ
        dựa vào bước chuyển đổi ID của bộ nạp / adapter khi tích hợp."""
        # 1. Bước trích xuất ID từ tệp JSON và CSV thật trên đĩa
        json_sample_ids = [r['sample_id'] for r in self.records_json]
        csv_sample_ids = [r['sample_id'] for r in self.records_csv]
        self.assertEqual(json_sample_ids, csv_sample_ids)

        # Trích xuất tập ID mang cờ loại trừ
        dynamically_extracted_excluded_ids = frozenset(
            r['sample_id'] for r in self.records_json if r.get('excluded_from_model_training') is True
        )
        self.assertEqual(len(dynamically_extracted_excluded_ids), 24, "Đủ 24 ID được trích xuất từ cờ loại trừ")

        dummy_groups = {sid: f"grp_{sid}" for sid in dynamically_extracted_excluded_ids}
        dummy_groups['VALID-01'] = 'grp_v1'
        dummy_groups['VALID-02'] = 'grp_v2'

        # 2. Kiểm tra RunPlan.validate khi nhận tập ID đã trích xuất:
        # Nếu bất kỳ ID nào trong số 24 mẫu hiệu chuẩn bị đưa vào train, validation, hoặc test:
        for sid in dynamically_extracted_excluded_ids:
            # Thử đưa vào train_ids
            plan_train = RunPlan('M0', 17, (sid,), ('VALID-01',), ('VALID-02',))
            with self.assertRaises(ValueError) as ctx:
                plan_train.validate(dummy_groups, excluded_ids=dynamically_extracted_excluded_ids)
            self.assertIn("Pilot/reserved samples entered the run plan", str(ctx.exception))

            # Thử đưa vào validation_ids
            plan_val = RunPlan('M0', 17, ('VALID-01',), (sid,), ('VALID-02',))
            with self.assertRaises(ValueError) as ctx:
                plan_val.validate(dummy_groups, excluded_ids=dynamically_extracted_excluded_ids)
            self.assertIn("Pilot/reserved samples entered the run plan", str(ctx.exception))

            # Thử đưa vào test_ids
            plan_test = RunPlan('M0', 17, ('VALID-01',), ('VALID-02',), (sid,))
            with self.assertRaises(ValueError) as ctx:
                plan_test.validate(dummy_groups, excluded_ids=dynamically_extracted_excluded_ids)
            self.assertIn("Pilot/reserved samples entered the run plan", str(ctx.exception))

        # 3. Kiểm tra riêng 16 mẫu có binary_model_eligible=True:
        eligible_16_ids = [r['sample_id'] for r in self.records_json if r.get('binary_model_eligible') is True]
        self.assertEqual(len(eligible_16_ids), 16)
        for sid in eligible_16_ids:
            plan = RunPlan('M3', 42, (sid,), ('VALID-01',), ('VALID-02',))
            with self.assertRaises(ValueError) as ctx:
                plan.validate(dummy_groups, excluded_ids=dynamically_extracted_excluded_ids)
            self.assertIn("Pilot/reserved samples entered the run plan", str(ctx.exception))

    def test_05_contract_scope_gatekeeper_readiness(self):
        """5. Kiểm tra chốt chặn phạm vi hợp đồng đầu vào (Scope Gatekeeper):
        Xác nhận check_training_inputs từ chối nạp manifest nghiên cứu Runway A.

        LƯU Ý PHẠM VI KỸ THUẬT RÕ RÀNG:
        check_training_inputs ném lỗi vì scope != 'synthetic_fixture_only' (hợp đồng nghiên cứu
        và adapter của C chưa tích hợp, training_blocked=True). Đây là chốt chặn ở tầng hợp đồng
        phạm vi hệ thống, KHÔNG PHẢI là bằng chứng rằng check_training_inputs đã phân tích nội dung
        hoặc tự đọc 4 cờ cách ly bên trong tệp nhãn."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_manifest_path = Path(temp_dir) / "calibration_research_manifest.json"
            research_manifest = {
                "contract_version": "training-input-fixture-v0",
                "scope": "research_calibration_runway_a",  # Scope nghiên cứu chưa được kích hoạt
                "artifacts": {
                    "labels": {"path": str(self.json_labels_path.resolve())}
                }
            }
            temp_manifest_path.write_text(json.dumps(research_manifest), encoding='utf-8')
            with self.assertRaises(ValueError) as ctx:
                check_training_inputs(str(temp_manifest_path))
            self.assertIn("Research inputs blocked", str(ctx.exception))

    def test_06_plan01_three_tier_measurement_and_personnel_accounting(self):
        """6. Kiểm định Báo cáo PLAN-01: Ba tầng đo lường, kế toán giờ người Nguyễn Thắng và ca SMP-001."""
        self.assertEqual(self.plan01['status'], 'submitted_for_lead_d_review')

        # Ba tầng đo lường
        framework = self.plan01.get('three_tier_measurement_framework_and_bridges', {})
        self.assertIn('tier_1_raw_empirical_baseline', framework)
        self.assertIn('tier_2_operational_projection_1000_samples', framework)
        self.assertIn('tier_3_total_comprehensive_project_budget', framework)
        self.assertEqual(framework['tier_3_total_comprehensive_project_budget']['total_person_hours'], 190.79)

        # Cầu nối giải trình chênh lệch
        reconciliation = framework.get('reconciliation_bridges_tier_2_to_tier_3', {})
        self.assertEqual(reconciliation.get('sum_delta_hours'), 48.52)

        # Kế toán giờ người Thành viên C
        pg = self.plan01.get('personnel_governance', {})
        sup = pg.get('data_pipeline_and_secretarial_supervisor', {})
        self.assertIn('Nguyễn Thắng', sup.get('student_name'))
        self.assertEqual(sup.get('allocated_hours'), 25.0)
        self.assertIn('0,00 giờ công người', sup.get('ai_runtime_exclusion_rule'))

        # Phân tích ca sửa thao tác SMP-001
        smp = self.plan01.get('item_2_smp001_operational_rectification_and_sensitivity', {})
        self.assertIn('Sự cố thao tác / giao diện được báo cáo', smp.get('incident_summary'))
        self.assertNotIn('lỗi công cụ CLI', smp.get('incident_summary'))
        self.assertIn('sensitivity_analysis_table', smp)
        models = smp['sensitivity_analysis_table']
        self.assertIn('model_1_baseline_locked', models)
        self.assertIn('model_2_excluding_smp001', models)
        self.assertIn('model_3_substituting_draft_time', models)
        self.assertIn('model_4_conservative_active_interaction_sum', models)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    unittest.main(verbosity=2)
