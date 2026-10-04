"""Bộ kiểm thử cho Blind View, cơ chế chống rò rỉ nhãn và AnnotationRecord (Task LABEL-01).

Kiểm tra:
1. assert_no_label_leak phát hiện và ném lỗi khi xuất hiện bất kỳ trường nhãn hoặc metadata cấm.
2. extract_safe_view_content loại bỏ 100% script, iframe, inline events và bóc tách text an toàn.
3. create_blind_sample tạo mẫu BlindSample hợp lệ, không rò rỉ nhãn.
4. validate_annotation_record xác thực chặt chẽ theo đúng chuẩn docs/CODEBOOK_V1.md.
5. export_blind_view xuất gói JSON Blind View hoàn chỉnh cho A và B.
6. Luồng tích hợp giữa lượt gán nhãn AnnotationRecord và tính toán Cohen's Kappa.
7. Cơ chế allowlist, ID trung tính, cách ly dry-run và kiểm tra tính toàn vẹn khi resume CLI.
"""

import json
from pathlib import Path
import pytest

from phishing.annotation import (
    AnnotationRecord,
    BlindSample,
    assert_neutral_sample_id,
    assert_no_label_leak,
    compute_cohens_kappa,
    create_blind_sample,
    export_blind_view,
    extract_safe_view_content,
    validate_annotation_record,
)


class TestBlindViewSecurityAndAntiLeakage:
    """Kiểm tra cơ chế bảo mật và chống rò rỉ dữ liệu (Anti-Leakage Protocols)."""

    def test_assert_no_label_leak_detects_forbidden_keys(self):
        """Phát hiện các khóa nhãn nguồn ở mọi cấp độ (cấp 1 hoặc lồng nhau)."""
        forbidden_samples = [
            {"sample_id": "S1", "label": "phish"},
            {"sample_id": "S2", "source_label": "benign"},
            {"sample_id": "S3", "target": "microsoft"},
            {"sample_id": "S4", "org_targets": ["google"]},
            {"sample_id": "S5", "score": 0.95},
            {"sample_id": "S6", "metadata": {"primary_org": "apple"}},
            {"sample_id": "S7", "model_score": 0.8},
            {"sample_id": "S8", "pilot_row_idx": 5},
        ]

        for s in forbidden_samples:
            with pytest.raises(ValueError, match="RÒ RỈ DỮ LIỆU PHÁT HIỆN"):
                assert_no_label_leak(s)

    def test_assert_no_label_leak_passes_clean_data(self):
        """Dữ liệu an toàn không chứa khóa cấm phải vượt qua bình thường."""
        clean_data = {
            "sample_id": "S001",
            "url": "https://login.example.com/",
            "page_text": "Please enter your username and password",
            "structure_summary": {
                "title": "Login Page",
                "forms": 1,
                "inputs": 2,
                "password_inputs": 1,
                "has_login_form": True,
            },
        }
        assert_no_label_leak(clean_data)

    def test_extract_safe_view_content_strips_scripts_and_events(self):
        """Bóc tách text an toàn, loại bỏ thẻ script, iframe, inline event handlers và style."""
        malicious_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Suspicious Portal</title>
            <script>alert('malicious_js_executed');</script>
            <style>body { color: red; }</style>
        </head>
        <body onload="doEvil()">
            <iframe src="https://evil-site.com/exploit"></iframe>
            <h1>Sign in to your account</h1>
            <p>Enter credentials below:</p>
            <form action="/login" method="POST">
                <input type="text" name="user" placeholder="Email" value="victim@domain.com" />
                <input type="password" name="pass" />
                <button type="submit" onclick="stealData()">Submit</button>
            </form>
            <a href="https://other-domain.org/help">External Help</a>
        </body>
        </html>
        """
        text, summary = extract_safe_view_content(malicious_html, "https://example.com/login")

        # 1. Không còn mã độc trong văn bản
        assert "malicious_js_executed" not in text
        assert "alert" not in text
        assert "evil-site" not in text
        assert "color: red" not in text

        # 2. Giữ nguyên văn bản cần thiết cho người gán nhãn
        assert "Sign in to your account" in text
        assert "Enter credentials below:" in text

        # 3. Thống kê cấu trúc chính xác
        assert summary["title"] == "Suspicious Portal"
        assert summary["forms"] == 1
        assert summary["inputs"] == 2
        assert summary["password_inputs"] == 1
        assert summary["has_login_form"] is True
        assert summary["buttons"] == 1
        assert summary["external_links"] == 1

    def test_create_blind_sample_drops_labels_completely(self):
        """Hàm create_blind_sample phải loại bỏ nhãn và các metadata nhạy cảm khỏi đầu ra."""
        raw_sample = {
            "row_idx": 42,
            "label": "phish",
            "source_label": "phishing",
            "target": "microsoft",
            "url": "https://secure-login.update-office.com/",
            "html": "<html><title>Microsoft Login</title><body><h1>Sign In</h1><form><input type='password'></form></body></html>",
            "matcher_score": 0.99,
        }

        blind = create_blind_sample(raw_sample, sample_id="BLIND-042")
        out = blind.to_dict()

        # Kiểm tra không còn bất kỳ nhãn nào
        assert "label" not in out
        assert "source_label" not in out
        assert "target" not in out
        assert "matcher_score" not in out
        assert "row_idx" not in out

        # Kiểm tra thông tin mù hợp lệ
        assert out["sample_id"] == "BLIND-042"
        assert out["url"] == "https://secure-login.update-office.com/"
        assert "Sign In" in out["page_text"]
        assert out["structure_summary"]["has_login_form"] is True

    def test_assert_neutral_sample_id(self):
        """Kiểm tra assert_neutral_sample_id chặn mọi ID chứa nhãn hoặc tên thương hiệu."""
        for valid_id in ["PILOT-001", "SMP-100", "BLIND-042", "CASE-9999", "M001"]:
            assert_neutral_sample_id(valid_id)

        with pytest.raises(ValueError, match="không được để rỗng"):
            assert_neutral_sample_id("")

        leaky_ids = [
            "phish-001",
            "benign-101",
            "malicious-url",
            "sample-microsoft",
            "target-google",
            "smp-booking",
            "paypal-portal",
            "amazon-prime",
            "apple-id",
        ]
        for bad_id in leaky_ids:
            with pytest.raises(ValueError, match="RÒ RỈ DỮ LIỆU PHÁT HIỆN"):
                assert_neutral_sample_id(bad_id)

    def test_assert_no_label_leak_enforces_allowlist_on_blind_samples(self):
        """Kiểm tra cơ chế allowlist ở cấp mẫu: từ chối các trường ngoài allowlist."""
        bad_sample = {
            "sample_id": "PILOT-001",
            "url": "https://example.com/login",
            "page_text": "Sample text",
            "structure_summary": {
                "title": "Login",
                "forms": 1,
                "inputs": 2,
                "password_inputs": 1,
                "has_login_form": True,
                "buttons": 1,
                "external_links": 0,
            },
            "annotation_a": {"class_label": "phishing"},
        }
        with pytest.raises(ValueError, match="chứa các khóa ngoài allowlist"):
            assert_no_label_leak(bad_sample)

    def test_assert_no_label_leak_enforces_allowlist_on_structure_summary(self):
        """Kiểm tra cơ chế allowlist ở structure_summary: từ chối trường lạ."""
        bad_summary_sample = {
            "sample_id": "PILOT-002",
            "url": "https://example.com/test",
            "page_text": "Text",
            "structure_summary": {
                "title": "Test",
                "forms": 0,
                "inputs": 0,
                "password_inputs": 0,
                "has_login_form": False,
                "buttons": 0,
                "external_links": 0,
                "model_prediction": "phish",
            },
        }
        with pytest.raises(ValueError, match="structure_summary .* chứa khóa ngoài allowlist"):
            assert_no_label_leak(bad_summary_sample)

    def test_assert_no_label_leak_rejects_forbidden_prefixes_and_suffixes(self):
        """Kiểm tra cấm các tiền tố (annotation_, rater_, model_) và hậu tố (_label, _score)."""
        test_cases = [
            {"sample_id": "SMP-01", "url": "https://test.com", "rater_a_result": "phishing"},
            {"sample_id": "SMP-02", "url": "https://test.com", "model_prob": 0.88},
            {"sample_id": "SMP-03", "url": "https://test.com", "final_verdict": "phish"},
            {"sample_id": "SMP-04", "url": "https://test.com", "eval_score": 0.9},
        ]
        for tc in test_cases:
            with pytest.raises(ValueError, match="RÒ RỈ DỮ LIỆU PHÁT HIỆN"):
                assert_no_label_leak(tc)


class TestAnnotationRecordValidation:
    """Kiểm tra tính tuân thủ của bản ghi gán nhãn đối với docs/CODEBOOK_V1.md."""

    def test_valid_annotation_record_passes(self):
        valid_dict = {
            "annotator_id": "A",
            "sample_id": "BLIND-001",
            "pass_id": 1,
            "class_label": "phishing",
            "primary_org_status": "identified",
            "catalog_status": "in_catalog",
            "observed_service": "Microsoft 365",
            "org_targets": ["microsoft"],
            "primary_org": "microsoft",
            "identity_role": "identity_claim",
            "domain_role": "unverified",
            "evidence_note": "Trang chứa logo Microsoft và form đăng nhập trên tên miền lạ",
            "seconds_spent": 142.5,
            "random_subset": True,
            "difficult_case": False,
            "codebook_version": "1.0.0",
        }
        record = validate_annotation_record(valid_dict)
        assert record.annotator_id == "A"
        assert record.seconds_spent == 142.5
        assert record.class_label == "phishing"
        assert record.is_dry_run is False

        d = record.to_dict()
        assert d["seconds_spent"] == 142.5
        assert d["random_subset"] is True
        assert d["is_dry_run"] is False

    def test_annotation_record_is_dry_run_flag(self):
        """Kiểm tra cờ is_dry_run được hỗ trợ và chuẩn hóa đúng kiểu boolean."""
        dry_dict = {
            "annotator_id": "simulated_A",
            "sample_id": "PILOT-001",
            "pass_id": 1,
            "class_label": "benign",
            "primary_org_status": "unknown",
            "catalog_status": "unresolved",
            "observed_service": "None",
            "org_targets": [],
            "primary_org": "unknown",
            "identity_role": "unclear",
            "domain_role": "unverified",
            "evidence_note": "Dry-run record",
            "seconds_spent": 0.5,
            "random_subset": True,
            "difficult_case": False,
            "codebook_version": "1.0.0",
            "is_dry_run": True,
        }
        record = validate_annotation_record(dry_dict)
        assert record.is_dry_run is True
        assert record.to_dict()["is_dry_run"] is True

    def test_invalid_class_label_rejected(self):
        invalid_dict = {
            "annotator_id": "A",
            "sample_id": "BLIND-001",
            "pass_id": 1,
            "class_label": "malicious",
            "primary_org_status": "identified",
            "catalog_status": "in_catalog",
            "observed_service": "Google",
            "org_targets": ["google"],
            "primary_org": "google",
            "identity_role": "identity_claim",
            "domain_role": "unverified",
            "evidence_note": "test",
            "seconds_spent": 60.0,
            "random_subset": True,
            "difficult_case": False,
        }
        with pytest.raises(ValueError, match="class_label 'malicious' không hợp lệ"):
            validate_annotation_record(invalid_dict)

    def test_invalid_identity_role_rejected(self):
        invalid_dict = {
            "annotator_id": "B",
            "sample_id": "BLIND-002",
            "pass_id": 1,
            "class_label": "benign",
            "primary_org_status": "unknown",
            "catalog_status": "unresolved",
            "observed_service": "None",
            "org_targets": [],
            "primary_org": "unknown",
            "identity_role": "first_party_login",
            "domain_role": "first_party_identity",
            "evidence_note": "valid site",
            "seconds_spent": 30.0,
            "random_subset": True,
            "difficult_case": False,
        }
        with pytest.raises(ValueError, match="identity_role 'first_party_login' không hợp lệ"):
            validate_annotation_record(invalid_dict)

    def test_negative_seconds_spent_rejected(self):
        invalid_dict = {
            "annotator_id": "A",
            "sample_id": "BLIND-003",
            "pass_id": 1,
            "class_label": "benign",
            "primary_org_status": "identified",
            "catalog_status": "in_catalog",
            "observed_service": "Adobe",
            "org_targets": ["adobe"],
            "primary_org": "adobe",
            "identity_role": "identity_claim",
            "domain_role": "first_party_identity",
            "evidence_note": "Adobe official site",
            "seconds_spent": -15.0,
            "random_subset": True,
            "difficult_case": False,
        }
        with pytest.raises(ValueError, match="seconds_spent=-15.0 không được âm"):
            validate_annotation_record(invalid_dict)


class TestBlindViewExportAndKappaFlow:
    """Kiểm tra xuất file gói mù và tích hợp đo đạc Cohen's Kappa giữa A và B."""

    def test_export_blind_view_writes_json_and_preserves_metadata(self, tmp_path):
        out_file = tmp_path / "blind_view_test.json"
        raw_samples = [
            {
                "sample_id": "S101",
                "url": "https://example.com/one",
                "html": "<p>Content one</p>",
            },
            {
                "sample_id": "S102",
                "url": "https://example.com/two",
                "html": "<p>Content two</p>",
            },
        ]
        payload = export_blind_view(
            raw_samples,
            out_file,
            dataset_id="TEST-PILOT-01",
            dataset_type="synthetic_practice_pilot",
            is_synthetic=True,
            purpose="Mô phỏng luyện tập",
        )
        assert out_file.exists()
        assert payload["total_samples"] == 2
        assert payload["dataset_id"] == "TEST-PILOT-01"
        assert payload["dataset_type"] == "synthetic_practice_pilot"
        assert payload["is_synthetic"] is True

        saved_data = json.loads(out_file.read_text(encoding="utf-8"))
        assert saved_data["total_samples"] == 2
        assert saved_data["samples"][0]["sample_id"] == "S101"
        assert saved_data["is_synthetic"] is True
        assert_no_label_leak(saved_data)

    def test_pilot_practice_package_file_integrity(self):
        """Kiểm tra tệp blind_view_pilot.json thực tế trong dự án."""
        project_root = Path(__file__).resolve().parent.parent
        pilot_file = project_root / "data" / "annotations" / "blind_view_pilot.json"
        assert pilot_file.exists(), f"Không tìm thấy {pilot_file}"

        data = json.loads(pilot_file.read_text(encoding="utf-8"))
        assert data["dataset_type"] == "synthetic_practice_pilot"
        assert data["is_synthetic"] is True
        assert data["total_samples"] == 20
        assert len(data["samples"]) == 20

        for idx, sample in enumerate(data["samples"], 1):
            sid = sample["sample_id"]
            assert sid == f"PILOT-{idx:03d}"
            assert "random_subset" in sample
            assert "codebook_version" in sample
            assert "structure_summary" in sample

        assert_no_label_leak(data)

    def test_kappa_integration_from_annotation_records(self):
        """Giả lập lượt gán nhãn độc lập của A và B trên 5 mẫu ngẫu nhiên và tính Kappa."""
        records_a = [
            validate_annotation_record({
                "annotator_id": "A", "sample_id": f"S{i}", "pass_id": 1,
                "class_label": label, "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Service", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "note",
                "seconds_spent": 120.0, "random_subset": True, "difficult_case": False,
            })
            for i, label in enumerate(["phishing", "phishing", "benign", "benign", "phishing"])
        ]

        records_b = [
            validate_annotation_record({
                "annotator_id": "B", "sample_id": f"S{i}", "pass_id": 1,
                "class_label": label, "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Service", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "note",
                "seconds_spent": 115.0, "random_subset": True, "difficult_case": False,
            })
            for i, label in enumerate(["phishing", "benign", "benign", "benign", "phishing"])
        ]

        labels_a = [r.class_label for r in records_a]
        labels_b = [r.class_label for r in records_b]
        is_difficult = [r.difficult_case for r in records_a]

        kappa_res = compute_cohens_kappa(labels_a, labels_b, is_difficult=is_difficult)
        assert kappa_res.status == "valid"
        assert kappa_res.observed_agreement == 0.8
        assert kappa_res.sample_count == 5
        assert 0.0 < kappa_res.kappa <= 1.0

    def test_cohens_kappa_filters_dry_run_records(self):
        """Hàm compute_cohens_kappa phải tự động loại bỏ bản ghi dry-run mô phỏng."""
        records_a = [
            validate_annotation_record({
                "annotator_id": "A", "sample_id": "S1", "pass_id": 1,
                "class_label": "phishing", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "note",
                "seconds_spent": 100.0, "random_subset": True, "difficult_case": False, "is_dry_run": False,
            }),
            validate_annotation_record({
                "annotator_id": "A", "sample_id": "S2", "pass_id": 1,
                "class_label": "benign", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "note",
                "seconds_spent": 80.0, "random_subset": True, "difficult_case": False, "is_dry_run": False,
            }),
            validate_annotation_record({
                "annotator_id": "A", "sample_id": "S3", "pass_id": 1,
                "class_label": "phishing", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "note",
                "seconds_spent": 90.0, "random_subset": True, "difficult_case": False, "is_dry_run": False,
            }),
            validate_annotation_record({
                "annotator_id": "simulated_A", "sample_id": "S4", "pass_id": 1,
                "class_label": "benign", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "dry",
                "seconds_spent": 0.5, "random_subset": True, "difficult_case": False, "is_dry_run": True,
            }),
            validate_annotation_record({
                "annotator_id": "simulated_A", "sample_id": "S5", "pass_id": 1,
                "class_label": "phishing", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "dry",
                "seconds_spent": 0.5, "random_subset": True, "difficult_case": False, "is_dry_run": True,
            }),
        ]

        records_b = [
            validate_annotation_record({
                "annotator_id": "B", "sample_id": "S1", "pass_id": 1,
                "class_label": "phishing", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "note",
                "seconds_spent": 110.0, "random_subset": True, "difficult_case": False, "is_dry_run": False,
            }),
            validate_annotation_record({
                "annotator_id": "B", "sample_id": "S2", "pass_id": 1,
                "class_label": "benign", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "note",
                "seconds_spent": 75.0, "random_subset": True, "difficult_case": False, "is_dry_run": False,
            }),
            validate_annotation_record({
                "annotator_id": "B", "sample_id": "S3", "pass_id": 1,
                "class_label": "benign", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "note",
                "seconds_spent": 85.0, "random_subset": True, "difficult_case": False, "is_dry_run": False,
            }),
            validate_annotation_record({
                "annotator_id": "simulated_B", "sample_id": "S4", "pass_id": 1,
                "class_label": "benign", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "dry",
                "seconds_spent": 0.5, "random_subset": True, "difficult_case": False, "is_dry_run": True,
            }),
            validate_annotation_record({
                "annotator_id": "simulated_B", "sample_id": "S5", "pass_id": 1,
                "class_label": "phishing", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "dry",
                "seconds_spent": 0.5, "random_subset": True, "difficult_case": False, "is_dry_run": True,
            }),
        ]

        res = compute_cohens_kappa(records_a, records_b)
        assert res.sample_count == 3

        with pytest.raises(ValueError, match="Không còn mẫu ngẫu nhiên hợp lệ"):
            compute_cohens_kappa(records_a[3:], records_b[3:])


class TestCLIResumeAndIsolation:
    """Kiểm tra cơ chế resume an toàn và cách ly dry-run trong CLI gán nhãn."""

    @pytest.fixture
    def cli_module(self):
        """Nạp động module scripts/annotate_cli.py."""
        import importlib.util
        cli_path = Path(__file__).resolve().parent.parent / "scripts" / "annotate_cli.py"
        spec = importlib.util.spec_from_file_location("annotate_cli", cli_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_load_already_annotated_sample_ids_rejects_rater_mismatch(self, tmp_path, cli_module):
        """Từ chối tiếp tục nếu tệp chứa kết quả của đánh giá viên khác."""
        out_file = tmp_path / "rater_test.jsonl"
        record = {
            "annotator_id": "A",
            "sample_id": "PILOT-001",
            "pass_id": 1,
            "class_label": "phishing",
            "is_dry_run": False,
        }
        out_file.write_text(json.dumps(record) + "\n", encoding="utf-8")

        with pytest.raises(ValueError, match="MÂU THUẪN ĐÁNH GIÁ VIÊN"):
            cli_module.load_already_annotated_sample_ids(
                out_file,
                expected_annotator_id="B",
                expected_pass_id=1,
            )

    def test_load_already_annotated_sample_ids_rejects_pass_mismatch(self, tmp_path, cli_module):
        """Từ chối tiếp tục nếu tệp chứa kết quả của pass_id khác."""
        out_file = tmp_path / "pass_test.jsonl"
        record = {
            "annotator_id": "A",
            "sample_id": "PILOT-001",
            "pass_id": 1,
            "class_label": "phishing",
            "is_dry_run": False,
        }
        out_file.write_text(json.dumps(record) + "\n", encoding="utf-8")

        with pytest.raises(ValueError, match="MÂU THUẪN LƯỢT GÁN"):
            cli_module.load_already_annotated_sample_ids(
                out_file,
                expected_annotator_id="A",
                expected_pass_id=2,
            )

    def test_load_already_annotated_sample_ids_rejects_malformed_json(self, tmp_path, cli_module):
        """Không âm thầm bỏ qua dòng JSON lỗi, ném lỗi toàn vẹn."""
        out_file = tmp_path / "corrupt_test.jsonl"
        out_file.write_text('{"annotator_id": "A", "sample_id": "PILOT-001", "pass_id": 1}\n{CORRUPT_JSON\n', encoding="utf-8")

        with pytest.raises(ValueError, match="LỖI TOÀN VẸN TỆP"):
            cli_module.load_already_annotated_sample_ids(
                out_file,
                expected_annotator_id="A",
                expected_pass_id=1,
            )

    def test_load_already_annotated_sample_ids_rejects_dry_run_contamination(self, tmp_path, cli_module):
        """Từ chối nếu tệp gán nhãn của người thật bị lẫn bản ghi dry-run."""
        out_file = tmp_path / "dry_mix_test.jsonl"
        record = {
            "annotator_id": "A",
            "sample_id": "PILOT-001",
            "pass_id": 1,
            "class_label": "phishing",
            "is_dry_run": True,
        }
        out_file.write_text(json.dumps(record) + "\n", encoding="utf-8")

        with pytest.raises(ValueError, match="LỖI TẠP NHIỄM DỮ LIỆU"):
            cli_module.load_already_annotated_sample_ids(
                out_file,
                expected_annotator_id="A",
                expected_pass_id=1,
                is_dry_run_session=False,
            )

    def test_load_already_annotated_sample_ids_happy_path(self, tmp_path, cli_module):
        """Nạp thành công danh sách sample_id đã hoàn thành khi thông tin hoàn toàn hợp lệ."""
        out_file = tmp_path / "valid_resume.jsonl"
        records = [
            {"annotator_id": "A", "sample_id": "PILOT-001", "pass_id": 1, "is_dry_run": False},
            {"annotator_id": "A", "sample_id": "PILOT-002", "pass_id": 1, "is_dry_run": False},
        ]
        out_file.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")

        done = cli_module.load_already_annotated_sample_ids(
            out_file,
            expected_annotator_id="A",
            expected_pass_id=1,
        )
        assert done == {"PILOT-001", "PILOT-002"}

    def test_cli_dry_run_executes_isolated_session(self, tmp_path, cli_module):
        """Chế độ dry-run tự động cách ly vào tệp .dryrun.jsonl và ghi nhãn hợp lệ."""
        input_blind = tmp_path / "mini_blind.json"
        export_blind_view(
            [
                {"sample_id": "SMP-001", "url": "https://secure-login.test/", "html": "<form><input type='password'></form>"},
                {"sample_id": "SMP-002", "url": "https://normal-blog.test/", "html": "<p>Hello world blog</p>"},
            ],
            input_blind,
            dataset_id="MINI-TEST",
        )

        target_output = tmp_path / "A_pilot.jsonl"
        cli_module.annotate_interactive_session(
            annotator_id="A",
            input_path=input_blind,
            output_path=target_output,
            pass_id=1,
            dry_run=True,
        )

        # File người dùng chỉ định ban đầu không bị tạo
        assert not target_output.exists()

        # File cách ly dry-run phải được tạo
        isolated_file = tmp_path / "A_pilot.dryrun.jsonl"
        assert isolated_file.exists()

        lines = [json.loads(line) for line in isolated_file.read_text(encoding="utf-8").strip().split("\n")]
        assert len(lines) == 2
        for r in lines:
            assert r["annotator_id"] == "simulated_A"
            assert r["is_dry_run"] is True
            assert r["seconds_spent"] == 0.5
            validated = validate_annotation_record(r)
            assert validated.is_dry_run is True
