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
    compute_sample_content_hash,
    create_blind_sample,
    export_blind_view,
    extract_safe_view_content,
    filter_research_annotations,
    validate_annotation_record,
)
import hashlib
import importlib.util


@pytest.fixture
def cli_module():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("annotate_cli", root / "scripts/annotate_cli.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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

        kappa_res = compute_cohens_kappa(labels_a, labels_b, is_difficult=is_difficult, random_subset=[r.random_subset for r in records_a])
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
            assert "is_synthetic" in r
            assert "dataset_id" in r
            assert "dataset_hash" in r
            assert "codebook_hash" in r
            assert "sampling_plan_version" in r
            validated = validate_annotation_record(r)
            assert validated.is_dry_run is True

    def test_load_already_annotated_sample_ids_rejects_dataset_hash_mismatch(self, tmp_path, cli_module):
        """CLI từ chối resume khi dataset_hash của tệp output không khớp gói input hiện tại."""
        out_file = tmp_path / "resume_hash_mismatch.jsonl"
        rec = {
            "annotator_id": "A",
            "sample_id": "PILOT-001",
            "pass_id": 1,
            "is_dry_run": False,
            "dataset_hash": "hash_package_v1",
        }
        out_file.write_text(json.dumps(rec) + "\n", encoding="utf-8")

        with pytest.raises(ValueError, match="MÂU THUẪN GÓI DỮ LIỆU ĐẦU VÀO"):
            cli_module.load_already_annotated_sample_ids(
                out_file,
                expected_annotator_id="A",
                expected_pass_id=1,
                expected_dataset_hash="hash_package_v2",
            )

    def test_load_already_annotated_sample_ids_rejects_dataset_id_mismatch(self, tmp_path, cli_module):
        """CLI từ chối resume khi dataset_id của tệp output không khớp dataset_id hiện tại."""
        out_file = tmp_path / "resume_ds_mismatch.jsonl"
        rec = {
            "annotator_id": "A",
            "sample_id": "PILOT-001",
            "pass_id": 1,
            "is_dry_run": False,
            "dataset_id": "REAL-PILOT-32-V1",
        }
        out_file.write_text(json.dumps(rec) + "\n", encoding="utf-8")

        with pytest.raises(ValueError, match="MÂU THUẪN GÓI DỮ LIỆU ĐẦU VÀO"):
            cli_module.load_already_annotated_sample_ids(
                out_file,
                expected_annotator_id="A",
                expected_pass_id=1,
                expected_dataset_id="SYNTHETIC-20-V1",
            )

    def test_cli_blocks_random_subset_override_in_human_session(self, tmp_path, cli_module):
        """CLI khóa cờ --random-subset khi gán nhãn người thật."""
        input_blind = tmp_path / "test_blind.json"
        export_blind_view(
            [{"sample_id": "SMP-001", "url": "https://test.invalid/", "html": "<p>Hello</p>"}],
            input_blind,
            dataset_id="TEST-OVERRIDE",
        )
        out_file = tmp_path / "A_override.jsonl"
        with pytest.raises(ValueError, match="CỜ BỊ KHÓA"):
            cli_module.annotate_interactive_session(
                annotator_id="A",
                input_path=input_blind,
                output_path=out_file,
                pass_id=1,
                dry_run=False,
                cli_random_subset=True,
            )

    def test_resume_rejects_codebook_hash_mismatch(self, tmp_path, cli_module):
        """CLI từ chối resume khi codebook_hash trong file kết quả khác codebook hiện tại."""
        out_file = tmp_path / "resume_cb_mismatch.jsonl"
        rec = {
            "annotator_id": "A",
            "sample_id": "PILOT-001",
            "pass_id": 1,
            "is_dry_run": False,
            "codebook_hash": "cb_old_hash",
        }
        out_file.write_text(json.dumps(rec) + "\n", encoding="utf-8")

        with pytest.raises(ValueError, match="MÂU THUẪN CODEBOOK HASH"):
            cli_module.load_already_annotated_sample_ids(
                out_file,
                expected_annotator_id="A",
                expected_pass_id=1,
                expected_codebook_hash="cb_new_hash",
            )

    def test_resume_rejects_content_change_for_same_sample_id(self, tmp_path, cli_module):
        """CLI từ chối resume khi mẫu cùng ID bị đổi nội dung (URL hoặc page_text)."""
        import hashlib
        out_file = tmp_path / "resume_content_changed.jsonl"
        old_url = "https://login.example.com/"
        old_text = "Original login prompt text"
        old_hash = hashlib.sha256((old_url + "\0" + old_text).encode("utf-8")).hexdigest()

        rec = {
            "annotator_id": "A",
            "sample_id": "PILOT-001",
            "pass_id": 1,
            "is_dry_run": False,
            "sample_content_hash": old_hash,
        }
        out_file.write_text(json.dumps(rec) + "\n", encoding="utf-8")

        # Gói đầu vào hiện tại chứa PILOT-001 nhưng nội dung đã bị sửa đổi
        new_samples = {
            "PILOT-001": {
                "sample_id": "PILOT-001",
                "url": "https://tampered-login.example.com/",
                "page_text": "Different content under same ID",
            }
        }

        with pytest.raises(ValueError, match="MÂU THUẪN NỘI DUNG MẪU"):
            cli_module.load_already_annotated_sample_ids(
                out_file,
                expected_annotator_id="A",
                expected_pass_id=1,
                current_samples_by_id=new_samples,
            )



class TestProvenanceAndKappaPairing:
    """Kiểm thử các trường provenance và thuật toán ghép cặp sample_id trong Cohen's Kappa."""

    def test_annotation_record_provenance_roundtrip(self):
        """AnnotationRecord lưu trữ và khôi phục đầy đủ các trường provenance."""
        data = {
            "annotator_id": "B",
            "sample_id": "PILOT-005",
            "pass_id": 1,
            "class_label": "phishing",
            "primary_org_status": "identified",
            "catalog_status": "in_catalog",
            "observed_service": "Office 365",
            "org_targets": ["microsoft"],
            "primary_org": "microsoft",
            "identity_role": "identity_claim",
            "domain_role": "unverified",
            "evidence_note": "Fake login form",
            "seconds_spent": 42.5,
            "random_subset": True,
            "difficult_case": False,
            "codebook_version": "1.0.0",
            "is_dry_run": False,
            "is_synthetic": False,
            "dataset_id": "REAL-PILOT-32-V1",
            "dataset_hash": "abc123hash",
            "codebook_hash": "def456hash",
            "sampling_plan_version": "PLAN-01",
        }
        rec = validate_annotation_record(data)
        d = rec.to_dict()
        assert d["is_synthetic"] is False
        assert d["dataset_id"] == "REAL-PILOT-32-V1"
        assert d["dataset_hash"] == "abc123hash"
        assert d["codebook_hash"] == "def456hash"
        assert d["sampling_plan_version"] == "PLAN-01"

    def test_kappa_pairs_by_sample_id_regardless_of_order(self):
        """compute_cohens_kappa tự sắp xếp ghép cặp theo sample_id khi thứ tự dòng khác nhau."""
        r1 = [
            {"sample_id": "S01", "class_label": "phishing", "random_subset": True},
            {"sample_id": "S02", "class_label": "benign", "random_subset": True},
            {"sample_id": "S03", "class_label": "phishing", "random_subset": True},
        ]
        # r2 bị xáo trộn thứ tự dòng: S03, S01, S02
        r2 = [
            {"sample_id": "S03", "class_label": "phishing", "random_subset": True},
            {"sample_id": "S01", "class_label": "phishing", "random_subset": True},
            {"sample_id": "S02", "class_label": "benign", "random_subset": True},
        ]
        res = compute_cohens_kappa(r1, r2, label_field="class_label")
        assert res.sample_count == 3
        assert res.observed_agreement == 1.0
        assert res.kappa == 1.0

    def test_kappa_rejects_sample_id_mismatch(self):
        """compute_cohens_kappa ném lỗi khi tập hợp sample_id giữa hai người gán không trùng khớp."""
        r1 = [{"sample_id": "S01", "class_label": "phishing"}, {"sample_id": "S02", "class_label": "benign"}]
        r2 = [{"sample_id": "S01", "class_label": "phishing"}, {"sample_id": "S99", "class_label": "benign"}]
        with pytest.raises(ValueError, match="không khớp nhau"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_rejects_package_hash_mismatch(self):
        """compute_cohens_kappa ném lỗi khi rater1 và rater2 gán trên hai gói dữ liệu khác nhau."""
        r1 = [{"sample_id": "S01", "class_label": "phishing", "dataset_hash": "hash_A"}]
        r2 = [{"sample_id": "S01", "class_label": "phishing", "dataset_hash": "hash_B"}]
        with pytest.raises(ValueError, match="mâu thuẫn provenance"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_rejects_codebook_and_plan_provenance_mismatch(self):
        """compute_cohens_kappa phát hiện mâu thuẫn codebook_hash hoặc sampling_plan_version."""
        r1 = [{"sample_id": "S01", "class_label": "phishing", "codebook_hash": "cb_v1"}]
        r2 = [{"sample_id": "S01", "class_label": "phishing", "codebook_hash": "cb_v2"}]
        with pytest.raises(ValueError, match="mâu thuẫn provenance 'codebook_hash'"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_excludes_synthetic_records_from_research_statistics(self):
        """Dữ liệu mô phỏng (is_synthetic=True) bị loại bỏ khỏi thống kê Cohen's Kappa theo quy tắc Lead D."""
        r1 = [
            {"sample_id": "S01", "class_label": "phishing", "is_synthetic": True, "random_subset": True},
            {"sample_id": "S02", "class_label": "benign", "is_synthetic": True, "random_subset": True},
        ]
        r2 = [
            {"sample_id": "S01", "class_label": "phishing", "is_synthetic": True, "random_subset": True},
            {"sample_id": "S02", "class_label": "benign", "is_synthetic": True, "random_subset": True},
        ]
        # Mặc định allow_synthetic=False: ném lỗi vì toàn bộ mẫu bị loại bỏ
        with pytest.raises(ValueError, match="dữ liệu mô phỏng"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

        # Cho phép rõ ràng qua tham số allow_synthetic=True
        res = compute_cohens_kappa(r1, r2, label_field="class_label", allow_synthetic=True)
        assert res.sample_count == 2
        assert res.observed_agreement == 1.0

    def test_filter_research_annotations_excludes_simulation_and_dry_run(self):
        """filter_research_annotations loại bỏ hoàn toàn các bản ghi mô phỏng và dry-run khỏi tập thống kê."""
        records = [
            {"sample_id": "REAL-1", "is_synthetic": False, "is_dry_run": False},
            {"sample_id": "SYNTH-1", "is_synthetic": True, "is_dry_run": False},
            {"sample_id": "DRY-1", "is_synthetic": False, "is_dry_run": True},
            {"sample_id": "REAL-2", "is_synthetic": False, "is_dry_run": False},
        ]
        filtered = filter_research_annotations(records)
        assert len(filtered) == 2
        assert [r["sample_id"] for r in filtered] == ["REAL-1", "REAL-2"]

    def test_kappa_rejects_mixed_batch_multiple_packages(self):
        """compute_cohens_kappa cấm tính toán trên tập dữ liệu lẫn lộn nhiều gói/codebook/sampling-plan."""
        r1 = [
            {"sample_id": "S01", "class_label": "phishing", "dataset_hash": "pkg_A", "codebook_hash": "cb1"},
            {"sample_id": "S02", "class_label": "benign", "dataset_hash": "pkg_B", "codebook_hash": "cb1"},
        ]
        r2 = [
            {"sample_id": "S01", "class_label": "phishing", "dataset_hash": "pkg_A", "codebook_hash": "cb1"},
            {"sample_id": "S02", "class_label": "benign", "dataset_hash": "pkg_B", "codebook_hash": "cb1"},
        ]
        with pytest.raises(ValueError, match="LỖI ĐA GÓI"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_rejects_pairwise_content_hash_mismatch(self):
        """compute_cohens_kappa phát hiện và báo lỗi khi sample_content_hash của cùng sample_id bị lệch giữa A và B."""
        r1 = [
            {"sample_id": "S01", "class_label": "phishing", "dataset_hash": "pkg1", "sample_content_hash": "hash_v1"},
            {"sample_id": "S02", "class_label": "benign", "dataset_hash": "pkg1", "sample_content_hash": "hash_v2"},
        ]
        r2 = [
            {"sample_id": "S01", "class_label": "phishing", "dataset_hash": "pkg1", "sample_content_hash": "hash_tampered"},
            {"sample_id": "S02", "class_label": "benign", "dataset_hash": "pkg1", "sample_content_hash": "hash_v2"},
        ]
        with pytest.raises(ValueError, match="MÂU THUẪN NỘI DUNG MẪU"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_stable_deterministic_sort_matches_different_order(self):
        """compute_cohens_kappa tự động sắp xếp theo sample_id bảo đảm kết quả độc lập với thứ tự nhập liệu."""
        r1 = [
            {"sample_id": "S03", "class_label": "phishing", "random_subset": True},
            {"sample_id": "S01", "class_label": "benign", "random_subset": True},
            {"sample_id": "S02", "class_label": "phishing", "random_subset": True},
        ]
        r2 = [
            {"sample_id": "S02", "class_label": "phishing", "random_subset": True},
            {"sample_id": "S03", "class_label": "phishing", "random_subset": True},
            {"sample_id": "S01", "class_label": "benign", "random_subset": True},
        ]
        res = compute_cohens_kappa(r1, r2, label_field="class_label")
        assert res.sample_count == 3
        assert res.observed_agreement == 1.0
        assert res.kappa == 1.0

    def test_kappa_keeps_difficult_cases_in_random_subset(self):
        """compute_cohens_kappa giữ nguyên các ca khó (difficult_case=True) nếu thuộc random_subset."""
        r1 = [
            {"sample_id": "S01", "class_label": "phishing", "difficult_case": True, "random_subset": True},
            {"sample_id": "S02", "class_label": "benign", "difficult_case": False, "random_subset": True},
        ]
        r2 = [
            {"sample_id": "S01", "class_label": "phishing", "difficult_case": True, "random_subset": True},
            {"sample_id": "S02", "class_label": "benign", "difficult_case": False, "random_subset": True},
        ]
        res = compute_cohens_kappa(r1, r2, label_field="class_label")
        assert res.sample_count == 2
        assert res.observed_agreement == 1.0


class TestResumeStrictProvenanceAndManifestChecks:
    """Kiểm thử cơ chế kiểm tra Resume nghiêm ngặt và rào chắn Manifest kiểm định."""

    def test_resume_rejects_missing_provenance_field_in_real_session(self, tmp_path, cli_module):
        """Phiên gán nhãn thật từ chối bản ghi resume nếu thiếu bất kỳ trường nào trong 6 trường provenance."""
        base_record = {
            "annotator_id": "A",
            "sample_id": "SMP-01",
            "pass_id": 1,
            "is_dry_run": False,
            "dataset_id": "REAL-PILOT-32-V1",
            "dataset_hash": "pkg_hash_123",
            "codebook_version": "1.0.0",
            "codebook_hash": "cb_hash_456",
            "sampling_plan_version": "PILOT-PLAN-V1-FULL-OVERLAP",
            "sample_content_hash": "content_hash_789",
        }
        provenance_keys = [
            "dataset_id",
            "dataset_hash",
            "codebook_version",
            "codebook_hash",
            "sampling_plan_version",
            "sample_content_hash",
        ]
        for missing_key in provenance_keys:
            out_file = tmp_path / f"resume_missing_{missing_key}.jsonl"
            tampered = dict(base_record)
            tampered[missing_key] = ""
            out_file.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
            with pytest.raises(ValueError, match="THIẾU PROVENANCE"):
                cli_module.load_already_annotated_sample_ids(
                    out_file,
                    expected_annotator_id="A",
                    expected_pass_id=1,
                    is_real_session=True,
                )

    def test_resume_rejects_empty_or_mismatched_when_expected_is_set(self, tmp_path, cli_module):
        """Khi giá trị kỳ vọng đã được xác định, bản ghi thiếu, rỗng hoặc khác giá trị đều phải báo lỗi cho cả 6 trường."""
        cases = [
            ("dataset_hash", "expected_dataset_hash", "hash_actual_v1", "hash_wrong_v2", "MÂU THUẪN GÓI DỮ LIỆU ĐẦU VÀO"),
            ("dataset_id", "expected_dataset_id", "REAL-PILOT-32-V1", "WRONG-ID", "MÂU THUẪN GÓI DỮ LIỆU ĐẦU VÀO"),
            ("codebook_hash", "expected_codebook_hash", "cb_hash_1", "cb_hash_wrong", "MÂU THUẪN CODEBOOK HASH"),
            ("codebook_version", "expected_codebook_version", "1.0.0", "9.9.9", "MÂU THUẪN PHIÊN BẢN CODEBOOK"),
            ("sampling_plan_version", "expected_sampling_plan_version", "PILOT-PLAN-V1-FULL-OVERLAP", "WRONG-PLAN", "MÂU THUẪN SAMPLING PLAN"),
        ]
        for field, kwarg, expected_val, wrong_val, err_pattern in cases:
            # 1. Trường hợp rỗng
            out_empty = tmp_path / f"resume_empty_{field}.jsonl"
            rec_empty = {
                "annotator_id": "A",
                "sample_id": "SMP-01",
                "pass_id": 1,
                "is_dry_run": False,
                field: "",
            }
            out_empty.write_text(json.dumps(rec_empty) + "\n", encoding="utf-8")
            with pytest.raises(ValueError, match=err_pattern):
                kwargs = {kwarg: expected_val}
                cli_module.load_already_annotated_sample_ids(
                    out_empty,
                    expected_annotator_id="A",
                    expected_pass_id=1,
                    **kwargs,
                )

            # 2. Trường hợp sai khác giá trị
            out_wrong = tmp_path / f"resume_wrong_{field}.jsonl"
            rec_wrong = {
                "annotator_id": "A",
                "sample_id": "SMP-01",
                "pass_id": 1,
                "is_dry_run": False,
                field: wrong_val,
            }
            out_wrong.write_text(json.dumps(rec_wrong) + "\n", encoding="utf-8")
            with pytest.raises(ValueError, match=err_pattern):
                kwargs = {kwarg: expected_val}
                cli_module.load_already_annotated_sample_ids(
                    out_wrong,
                    expected_annotator_id="A",
                    expected_pass_id=1,
                    **kwargs,
                )

    def test_resume_rejects_unknown_sample_id_not_in_current_package(self, tmp_path, cli_module):
        """CLI từ chối file resume chứa sample_id không thuộc gói dữ liệu đầu vào hiện tại."""
        out_file = tmp_path / "resume_unknown_id.jsonl"
        rec = {
            "annotator_id": "A",
            "sample_id": "UNKNOWN-SAMPLE-999",
            "pass_id": 1,
            "is_dry_run": False,
        }
        out_file.write_text(json.dumps(rec) + "\n", encoding="utf-8")
        current_samples = {
            "PILOT-001": {"sample_id": "PILOT-001", "url": "https://a.test", "page_text": "text"}
        }
        with pytest.raises(ValueError, match="SAMPLE_ID LẠ"):
            cli_module.load_already_annotated_sample_ids(
                out_file,
                expected_annotator_id="A",
                expected_pass_id=1,
                current_samples_by_id=current_samples,
            )

    def test_resume_does_not_mutate_or_backfill_old_records(self, tmp_path, cli_module):
        """CLI tuyệt đối không tự ý bổ sung provenance hay sửa đổi tệp kết quả cũ khi phát hiện thiếu; bắt buộc ném lỗi và giữ nguyên tệp."""
        out_file = tmp_path / "old_unmodified_probe.jsonl"
        old_content = json.dumps({
            "annotator_id": "A",
            "sample_id": "PILOT-001",
            "pass_id": 1,
            "is_dry_run": False,
            # Thiếu toàn bộ provenance
        }) + "\n"
        out_file.write_text(old_content, encoding="utf-8")
        current_samples = {
            "PILOT-001": {"sample_id": "PILOT-001", "url": "https://a.test", "page_text": "text"}
        }

        with pytest.raises(ValueError, match="THIẾU PROVENANCE"):
            cli_module.load_already_annotated_sample_ids(
                out_file,
                expected_annotator_id="A",
                expected_pass_id=1,
                current_samples_by_id=current_samples,
                is_real_session=True,
            )

        # Bảo đảm tệp cũ hoàn toàn không bị can thiệp, không bị ghi đè hay bổ sung dữ liệu giả
        assert out_file.read_text(encoding="utf-8") == old_content

    def test_resume_content_hash_includes_structure_summary(self, tmp_path, cli_module):
        """Thay đổi structure_summary (DOM) dù URL và page_text giữ nguyên cũng bị phát hiện và từ chối."""
        out_file = tmp_path / "resume_dom_changed.jsonl"
        sample_orig = {
            "sample_id": "SMP-01",
            "url": "https://login.example.com/",
            "page_text": "Please sign in to continue",
            "structure_summary": {"forms": 1, "inputs": 1, "password_inputs": 0},
        }
        orig_hash = compute_sample_content_hash(sample_orig)
        rec = {
            "annotator_id": "A",
            "sample_id": "SMP-01",
            "pass_id": 1,
            "is_dry_run": False,
            "sample_content_hash": orig_hash,
        }
        out_file.write_text(json.dumps(rec) + "\n", encoding="utf-8")

        # Gói đầu vào hiện tại có cấu trúc DOM bị sửa đổi (thêm password input)
        sample_tampered = {
            "sample_id": "SMP-01",
            "url": "https://login.example.com/",
            "page_text": "Please sign in to continue",
            "structure_summary": {"forms": 1, "inputs": 2, "password_inputs": 1},
        }
        current_samples = {"SMP-01": sample_tampered}
        with pytest.raises(ValueError, match="MÂU THUẪN NỘI DUNG MẪU"):
            cli_module.load_already_annotated_sample_ids(
                out_file,
                expected_annotator_id="A",
                expected_pass_id=1,
                current_samples_by_id=current_samples,
            )

    def test_cli_blocks_codebook_version_override_in_human_session(self, tmp_path, cli_module):
        """CLI khóa cờ --codebook-version khi gán nhãn người thật."""
        input_blind = tmp_path / "test_blind.json"
        export_blind_view(
            [{"sample_id": "SMP-001", "url": "https://test.invalid/", "html": "<p>Hello</p>"}],
            input_blind,
            dataset_id="TEST-OVERRIDE",
        )
        out_file = tmp_path / "A_override_cb.jsonl"
        with pytest.raises(ValueError, match="CỜ BỊ KHÓA"):
            cli_module.annotate_interactive_session(
                annotator_id="A",
                input_path=input_blind,
                output_path=out_file,
                pass_id=1,
                dry_run=False,
                cli_codebook_version="custom-v2",
            )

    def test_cli_manifest_preflight_blocks_unapproved_or_pending(self, tmp_path, cli_module):
        """CLI kiểm tra toàn bộ điều kiện manifest trước khi cho phép phiên người thật hoạt động."""
        input_blind = tmp_path / "real_view.json"
        export_blind_view(
            [{"sample_id": "SMP-001", "url": "https://test.invalid/", "html": "<p>Content</p>"}],
            input_blind,
            dataset_id="TEST-REAL",
            dataset_type="real_pilot_ready",
        )
        out_file = tmp_path / "A_real.jsonl"
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()

        # 1. B và D chưa nghiệm thu đầy đủ
        m1 = tmp_path / "m1.json"
        m1.write_text(json.dumps({
            "acceptance": {"B": "approved", "D": "pending"},
            "ready_for_annotation": True,
            "codebook_status": "locked",
            "sample_count": 1,
            "blind_view_sha256": view_hash,
        }), encoding="utf-8")
        with pytest.raises(ValueError, match="CHƯA NGHIỆM THU"):
            cli_module.annotate_interactive_session("A", input_blind, out_file, manifest_path=m1)

        # 2. ready_for_annotation=False
        m2 = tmp_path / "m2.json"
        m2.write_text(json.dumps({
            "acceptance": {"B": "approved", "D": "approved"},
            "ready_for_annotation": False,
            "codebook_status": "locked",
            "sample_count": 1,
            "blind_view_sha256": view_hash,
        }), encoding="utf-8")
        with pytest.raises(ValueError, match="CHƯA SẴN SÀNG"):
            cli_module.annotate_interactive_session("A", input_blind, out_file, manifest_path=m2)

        # 3. codebook_status chưa locked
        m3 = tmp_path / "m3.json"
        m3.write_text(json.dumps({
            "acceptance": {"B": "approved", "D": "approved"},
            "ready_for_annotation": True,
            "codebook_status": "pending_review",
            "sample_count": 1,
            "blind_view_sha256": view_hash,
        }), encoding="utf-8")
        with pytest.raises(ValueError, match="CODEBOOK CHƯA KHÓA"):
            cli_module.annotate_interactive_session("A", input_blind, out_file, manifest_path=m3)

        # 4. Hash view không khớp
        m4 = tmp_path / "m4.json"
        m4.write_text(json.dumps({
            "acceptance": {"B": "approved", "D": "approved"},
            "ready_for_annotation": True,
            "codebook_status": "locked",
            "sample_count": 1,
            "blind_view_sha256": "wrong_hash_12345",
        }), encoding="utf-8")
        with pytest.raises(ValueError, match="SAI KHÁC MÃ BĂM VIEW"):
            cli_module.annotate_interactive_session("A", input_blind, out_file, manifest_path=m4)

        # 5. Số mẫu không khớp
        m5 = tmp_path / "m5.json"
        m5.write_text(json.dumps({
            "acceptance": {"B": "approved", "D": "approved"},
            "ready_for_annotation": True,
            "codebook_status": "locked",
            "sample_count": 99,  # Gói view chỉ có 1 mẫu
            "blind_view_sha256": view_hash,
        }), encoding="utf-8")
        with pytest.raises(ValueError, match="SAI KHÁC SỐ MẪU"):
            cli_module.annotate_interactive_session("A", input_blind, out_file, manifest_path=m5)





