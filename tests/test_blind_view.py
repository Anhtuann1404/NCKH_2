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
    compute_cohens_kappa_from_labels,
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

        kappa_res = compute_cohens_kappa_from_labels(labels_a, labels_b, is_difficult=is_difficult, random_subset=[r.random_subset for r in records_a])
        assert kappa_res.status == "valid"
        assert kappa_res.observed_agreement == 0.8
        assert kappa_res.sample_count == 5
        assert 0.0 < kappa_res.kappa <= 1.0

    def test_cohens_kappa_filters_dry_run_records(self):
        """Hàm compute_cohens_kappa phải tự động loại bỏ bản ghi dry-run mô phỏng."""
        prov = {
            "dataset_id": "TEST-PILOT-01",
            "dataset_hash": "hash_pkg_v1",
            "codebook_hash": "cb_hash_v1",
            "codebook_version": "1.0.0",
            "sampling_plan_version": "PLAN-V1",
            "sample_content_hash": "content_hash_s",
        }
        records_a = [
            validate_annotation_record({
                "annotator_id": "A", "sample_id": "S1", "pass_id": 1,
                "class_label": "phishing", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "note",
                "seconds_spent": 100.0, "random_subset": True, "difficult_case": False, "is_dry_run": False,
                **prov,
            }),
            validate_annotation_record({
                "annotator_id": "A", "sample_id": "S2", "pass_id": 1,
                "class_label": "benign", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "note",
                "seconds_spent": 80.0, "random_subset": True, "difficult_case": False, "is_dry_run": False,
                **prov,
            }),
            validate_annotation_record({
                "annotator_id": "A", "sample_id": "S3", "pass_id": 1,
                "class_label": "phishing", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "note",
                "seconds_spent": 90.0, "random_subset": True, "difficult_case": False, "is_dry_run": False,
                **prov,
            }),
            validate_annotation_record({
                "annotator_id": "simulated_A", "sample_id": "S4", "pass_id": 1,
                "class_label": "benign", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "dry",
                "seconds_spent": 0.5, "random_subset": True, "difficult_case": False, "is_dry_run": True,
                **prov,
            }),
            validate_annotation_record({
                "annotator_id": "simulated_A", "sample_id": "S5", "pass_id": 1,
                "class_label": "phishing", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "dry",
                "seconds_spent": 0.5, "random_subset": True, "difficult_case": False, "is_dry_run": True,
                **prov,
            }),
        ]

        records_b = [
            validate_annotation_record({
                "annotator_id": "B", "sample_id": "S1", "pass_id": 1,
                "class_label": "phishing", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "note",
                "seconds_spent": 110.0, "random_subset": True, "difficult_case": False, "is_dry_run": False,
                **prov,
            }),
            validate_annotation_record({
                "annotator_id": "B", "sample_id": "S2", "pass_id": 1,
                "class_label": "benign", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "note",
                "seconds_spent": 75.0, "random_subset": True, "difficult_case": False, "is_dry_run": False,
                **prov,
            }),
            validate_annotation_record({
                "annotator_id": "B", "sample_id": "S3", "pass_id": 1,
                "class_label": "benign", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "note",
                "seconds_spent": 85.0, "random_subset": True, "difficult_case": False, "is_dry_run": False,
                **prov,
            }),
            validate_annotation_record({
                "annotator_id": "simulated_B", "sample_id": "S4", "pass_id": 1,
                "class_label": "benign", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "dry",
                "seconds_spent": 0.5, "random_subset": True, "difficult_case": False, "is_dry_run": True,
                **prov,
            }),
            validate_annotation_record({
                "annotator_id": "simulated_B", "sample_id": "S5", "pass_id": 1,
                "class_label": "phishing", "primary_org_status": "identified", "catalog_status": "in_catalog",
                "observed_service": "Office", "org_targets": ["target"], "primary_org": "target",
                "identity_role": "identity_claim", "domain_role": "unverified", "evidence_note": "dry",
                "seconds_spent": 0.5, "random_subset": True, "difficult_case": False, "is_dry_run": True,
                **prov,
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

    @staticmethod
    def _full_prov(**kwargs):
        prov = {
            "dataset_id": "REAL-PILOT-32-V1",
            "dataset_hash": "hash_pkg_v1",
            "codebook_hash": "hash_cb_v1",
            "codebook_version": "1.0.0",
            "sampling_plan_version": "PILOT-PLAN-V1-FULL-OVERLAP",
            "sample_content_hash": "content_hash_default",
            "random_subset": True,
        }
        prov.update(kwargs)
        return prov

    def test_kappa_pairs_by_sample_id_regardless_of_order(self):
        """compute_cohens_kappa tự sắp xếp ghép cặp theo sample_id khi thứ tự dòng khác nhau."""
        p = self._full_prov
        r1 = [
            p(sample_id="S01", class_label="phishing", sample_content_hash="c1"),
            p(sample_id="S02", class_label="benign", sample_content_hash="c2"),
            p(sample_id="S03", class_label="phishing", sample_content_hash="c3"),
        ]
        # r2 bị xáo trộn thứ tự dòng: S03, S01, S02
        r2 = [
            p(sample_id="S03", class_label="phishing", sample_content_hash="c3"),
            p(sample_id="S01", class_label="phishing", sample_content_hash="c1"),
            p(sample_id="S02", class_label="benign", sample_content_hash="c2"),
        ]
        res = compute_cohens_kappa(r1, r2, label_field="class_label")
        assert res.sample_count == 3
        assert res.observed_agreement == 1.0
        assert res.kappa == 1.0

    def test_kappa_rejects_sample_id_mismatch(self):
        """compute_cohens_kappa ném lỗi khi tập hợp sample_id giữa hai người gán không trùng khớp."""
        p = self._full_prov
        r1 = [p(sample_id="S01", class_label="phishing"), p(sample_id="S02", class_label="benign")]
        r2 = [p(sample_id="S01", class_label="phishing"), p(sample_id="S99", class_label="benign")]
        with pytest.raises(ValueError, match="không khớp nhau"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_rejects_package_hash_mismatch(self):
        """compute_cohens_kappa ném lỗi khi rater1 và rater2 gán trên hai gói dữ liệu khác nhau."""
        p = self._full_prov
        r1 = [p(sample_id="S01", class_label="phishing", dataset_hash="hash_A")]
        r2 = [p(sample_id="S01", class_label="phishing", dataset_hash="hash_B")]
        with pytest.raises(ValueError, match="mâu thuẫn provenance 'dataset_hash'"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_rejects_codebook_and_plan_provenance_mismatch(self):
        """compute_cohens_kappa phát hiện mâu thuẫn codebook_hash hoặc sampling_plan_version."""
        p = self._full_prov
        r1 = [p(sample_id="S01", class_label="phishing", codebook_hash="cb_v1")]
        r2 = [p(sample_id="S01", class_label="phishing", codebook_hash="cb_v2")]
        with pytest.raises(ValueError, match="mâu thuẫn provenance 'codebook_hash'"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_excludes_synthetic_records_from_research_statistics(self):
        """Dữ liệu mô phỏng (is_synthetic=True) bị loại bỏ khỏi thống kê Cohen's Kappa theo quy tắc Lead D."""
        p = self._full_prov
        r1 = [
            p(sample_id="S01", class_label="phishing", is_synthetic=True),
            p(sample_id="S02", class_label="benign", is_synthetic=True),
        ]
        r2 = [
            p(sample_id="S01", class_label="phishing", is_synthetic=True),
            p(sample_id="S02", class_label="benign", is_synthetic=True),
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
        p = self._full_prov
        r1 = [
            p(sample_id="S01", class_label="phishing", dataset_hash="pkg_A"),
            p(sample_id="S02", class_label="benign", dataset_hash="pkg_B"),
        ]
        r2 = [
            p(sample_id="S01", class_label="phishing", dataset_hash="pkg_A"),
            p(sample_id="S02", class_label="benign", dataset_hash="pkg_B"),
        ]
        with pytest.raises(ValueError, match="LỖI ĐA GÓI"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_rejects_pairwise_content_hash_mismatch(self):
        """compute_cohens_kappa phát hiện và báo lỗi khi sample_content_hash của cùng sample_id bị lệch giữa A và B."""
        p = self._full_prov
        r1 = [
            p(sample_id="S01", class_label="phishing", sample_content_hash="hash_v1"),
            p(sample_id="S02", class_label="benign", sample_content_hash="hash_v2"),
        ]
        r2 = [
            p(sample_id="S01", class_label="phishing", sample_content_hash="hash_tampered"),
            p(sample_id="S02", class_label="benign", sample_content_hash="hash_v2"),
        ]
        with pytest.raises(ValueError, match="MÂU THUẪN NỘI DUNG MẪU"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_rejects_missing_sample_id_when_provenance_present(self):
        """compute_cohens_kappa từ chối khi bản ghi có provenance nhưng không có sample_id."""
        p = self._full_prov
        r1 = [dict(p(class_label="phishing"), sample_id=None)]
        r2 = [dict(p(class_label="phishing"), sample_id=None)]
        with pytest.raises(ValueError, match="THIẾU PROVENANCE"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_rejects_partial_missing_or_empty_sample_id(self):
        """compute_cohens_kappa từ chối khi có bản ghi thiếu hoặc rỗng sample_id."""
        p = self._full_prov
        r1 = [
            p(sample_id="S01", class_label="phishing"),
            p(sample_id="", class_label="benign"),
        ]
        r2 = [
            p(sample_id="S01", class_label="phishing"),
            p(sample_id="S02", class_label="benign"),
        ]
        with pytest.raises(ValueError, match="THIẾU PROVENANCE"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_rejects_intra_batch_missing_provenance_field(self):
        """compute_cohens_kappa yêu cầu mọi bản ghi trong tập phải có đầy đủ trường provenance."""
        p = self._full_prov
        r1 = [
            p(sample_id="S01", class_label="phishing"),
            p(sample_id="S02", class_label="benign", codebook_version=""),
        ]
        r2 = [
            p(sample_id="S01", class_label="phishing"),
            p(sample_id="S02", class_label="benign"),
        ]
        with pytest.raises(ValueError, match="THIẾU PROVENANCE.*codebook_version"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_rejects_when_one_rater_completely_lacks_provenance_field(self):
        """compute_cohens_kappa từ chối khi rater1 có provenance nhưng rater2 thiếu."""
        p = self._full_prov
        r1 = [
            p(sample_id="S01", class_label="phishing"),
            p(sample_id="S02", class_label="benign"),
        ]
        r2 = [
            p(sample_id="S01", class_label="phishing", dataset_id=""),
            p(sample_id="S02", class_label="benign", dataset_id=""),
        ]
        with pytest.raises(ValueError, match="THIẾU PROVENANCE.*dataset_id"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_rejects_missing_content_hash_on_one_record(self):
        """compute_cohens_kappa yêu cầu sample_content_hash đầy đủ trên toàn bộ bản ghi."""
        p = self._full_prov
        r1 = [
            p(sample_id="S01", class_label="phishing", sample_content_hash="h1"),
            p(sample_id="S02", class_label="benign", sample_content_hash=""),
        ]
        r2 = [
            p(sample_id="S01", class_label="phishing", sample_content_hash="h1"),
            p(sample_id="S02", class_label="benign", sample_content_hash="h2"),
        ]
        with pytest.raises(ValueError, match="THIẾU PROVENANCE.*sample_content_hash"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_rejects_pairwise_provenance_mismatch(self):
        """compute_cohens_kappa đối chiếu từng cặp phát hiện mâu thuẫn codebook_version."""
        r1 = [
            {"sample_id": "S01", "class_label": "phishing", "dataset_id": "ds_A", "dataset_hash": "h_pkg", "codebook_hash": "cb_h", "codebook_version": "1.0.0", "sampling_plan_version": "1.0.0", "sample_content_hash": "c1"},
            {"sample_id": "S02", "class_label": "benign", "dataset_id": "ds_A", "dataset_hash": "h_pkg", "codebook_hash": "cb_h", "codebook_version": "1.0.0", "sampling_plan_version": "1.0.0", "sample_content_hash": "c2"},
        ]
        r2 = [
            {"sample_id": "S01", "class_label": "phishing", "dataset_id": "ds_B", "dataset_hash": "h_pkg", "codebook_hash": "cb_h", "codebook_version": "1.0.0", "sampling_plan_version": "1.0.0", "sample_content_hash": "c1"},
            {"sample_id": "S02", "class_label": "benign", "dataset_id": "ds_B", "dataset_hash": "h_pkg", "codebook_hash": "cb_h", "codebook_version": "1.0.0", "sampling_plan_version": "1.0.0", "sample_content_hash": "c2"},
        ]
        with pytest.raises(ValueError, match="mâu thuẫn provenance 'dataset_id'"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_passes_when_all_provenance_and_content_hashes_match_strictly(self):
        """compute_cohens_kappa tính toán thành công khi provenance đồng nhất và nội dung khớp hoàn toàn."""
        r1 = [
            {"sample_id": "S01", "class_label": "phishing", "dataset_id": "ds_A", "dataset_hash": "h_pkg", "codebook_hash": "cb_h", "codebook_version": "1.0.0", "sampling_plan_version": "1.0.0", "sample_content_hash": "c1"},
            {"sample_id": "S02", "class_label": "benign", "dataset_id": "ds_A", "dataset_hash": "h_pkg", "codebook_hash": "cb_h", "codebook_version": "1.0.0", "sampling_plan_version": "1.0.0", "sample_content_hash": "c2"},
        ]
        r2 = [
            {"sample_id": "S02", "class_label": "benign", "dataset_id": "ds_A", "dataset_hash": "h_pkg", "codebook_hash": "cb_h", "codebook_version": "1.0.0", "sampling_plan_version": "1.0.0", "sample_content_hash": "c2"},
            {"sample_id": "S01", "class_label": "phishing", "dataset_id": "ds_A", "dataset_hash": "h_pkg", "codebook_hash": "cb_h", "codebook_version": "1.0.0", "sampling_plan_version": "1.0.0", "sample_content_hash": "c1"},
        ]
        res = compute_cohens_kappa(r1, r2, label_field="class_label")
        assert res.sample_count == 2
        assert res.kappa == 1.0

    def test_kappa_stable_deterministic_sort_matches_different_order(self):
        """compute_cohens_kappa tự động sắp xếp theo sample_id bảo đảm kết quả độc lập với thứ tự nhập liệu."""
        p = self._full_prov
        r1 = [
            p(sample_id="S03", class_label="phishing", sample_content_hash="c3"),
            p(sample_id="S01", class_label="benign", sample_content_hash="c1"),
            p(sample_id="S02", class_label="phishing", sample_content_hash="c2"),
        ]
        r2 = [
            p(sample_id="S02", class_label="phishing", sample_content_hash="c2"),
            p(sample_id="S03", class_label="phishing", sample_content_hash="c3"),
            p(sample_id="S01", class_label="benign", sample_content_hash="c1"),
        ]
        res = compute_cohens_kappa(r1, r2, label_field="class_label")
        assert res.sample_count == 3
        assert res.observed_agreement == 1.0
        assert res.kappa == 1.0

    def test_kappa_keeps_difficult_cases_in_random_subset(self):
        """compute_cohens_kappa giữ nguyên các ca khó (difficult_case=True) nếu thuộc random_subset."""
        p = self._full_prov
        r1 = [
            p(sample_id="S01", class_label="phishing", difficult_case=True, random_subset=True, sample_content_hash="c1"),
            p(sample_id="S02", class_label="benign", difficult_case=False, random_subset=True, sample_content_hash="c2"),
        ]
        r2 = [
            p(sample_id="S01", class_label="phishing", difficult_case=True, random_subset=True, sample_content_hash="c1"),
            p(sample_id="S02", class_label="benign", difficult_case=False, random_subset=True, sample_content_hash="c2"),
        ]
        res = compute_cohens_kappa(r1, r2, label_field="class_label")
        assert res.sample_count == 2
        assert res.observed_agreement == 1.0

    def test_lead_d_probe_manifest_missing_mandatory_fields_rejected(self, tmp_path):
        """Tái hiện Probe 1 của Lead D: Manifest chỉ có acceptance, ready và codebook_status bị từ chối triệt để."""
        import scripts.annotate_cli as cli
        input_path = tmp_path / "view.json"
        export_blind_view([], input_path)
        manifest_path = tmp_path / "probe_manifest.json"
        # Manifest thiếu dataset_id, sample_count, sampling_plan_version, các hashes...
        manifest_path.write_text(json.dumps({
            "acceptance": {"B": "approved", "D": "approved"},
            "ready_for_annotation": True,
            "codebook_status": "locked",
        }), encoding="utf-8")
        with pytest.raises(ValueError, match="THIẾU TRƯỜNG MANIFEST BẮT BUỘC"):
            cli.validate_manifest_preflight(manifest_path, input_path, {"samples": []})

    def test_lead_d_probe_kappa_missing_provenance_rejected_in_research_mode(self):
        """Tái hiện Probe 2 của Lead D: Hai bản ghi có ID/nhãn nhưng thiếu provenance bị từ chối trong luồng nghiên cứu."""
        r1 = [{"sample_id": "S01", "class_label": "phishing"}, {"sample_id": "S02", "class_label": "benign"}]
        r2 = [{"sample_id": "S01", "class_label": "phishing"}, {"sample_id": "S02", "class_label": "benign"}]
        # Luồng nghiên cứu chính thức: bắt buộc provenance
        with pytest.raises(ValueError, match="THIẾU PROVENANCE"):
            compute_cohens_kappa(r1, r2)

        # Chế độ test/toán học tách biệt (require_provenance=False): tính được
        res = compute_cohens_kappa(r1, r2, require_provenance=False)
        assert res.sample_count == 2
        assert res.observed_agreement == 1.0

    def test_tamper_dataset_type_fails_preflight(self, tmp_path):
        """Thay đổi riêng dataset_type làm sai lệch hash view -> bị chặn tại preflight."""
        import scripts.annotate_cli as cli
        input_path = tmp_path / "view.json"
        dataset_id = "TEST-TAMPER"
        sp_ver = "PILOT-PLAN-V1-FULL-OVERLAP"
        export_blind_view(
            [{"sample_id": "S1", "url": "https://test.invalid/", "html": "<p>Content</p>"}],
            input_path,
            dataset_id=dataset_id,
            dataset_type="blind_view",
            sampling_plan_version=sp_ver,
        )
        original_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()

        dummy_cb = tmp_path / "CODEBOOK.md"
        dummy_cb.write_text("# Codebook\n**Phiên bản:** `v1.0.0`\n**Trạng thái:** `locked`\n" + "Rules content " * 20, encoding="utf-8")
        cb_hash = hashlib.sha256(dummy_cb.read_bytes()).hexdigest()

        dummy_dict = tmp_path / "dictionary.json"
        dummy_dict.write_text(json.dumps({
            "dictionary_id": "org_dictionary_v1",
            "version": "1.0.0",
            "status": "locked",
            "organizations": [{"id": f"org_{i}"} for i in range(14)],
        }), encoding="utf-8")
        dict_hash = hashlib.sha256(dummy_dict.read_bytes()).hexdigest()

        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps({
            "dataset_id": dataset_id,
            "sample_count": 1,
            "sampling_plan_version": sp_ver,
            "codebook_version": "1.0.0",
            "codebook_status": "locked",
            "dictionary_version": "1.0.0",
            "dictionary_status": "locked",
            "acceptance": {"B": "approved", "D": "approved"},
            "ready_for_annotation": True,
            "blind_view_sha256": original_hash,
            "codebook_sha256": cb_hash,
            "dictionary_sha256": dict_hash,
        }), encoding="utf-8")

        # Kẻ gian sửa riêng dataset_type trong file view thành "real_pilot_ready"
        view_content = json.loads(input_path.read_text(encoding="utf-8"))
        view_content["dataset_type"] = "real_pilot_ready"
        input_path.write_text(json.dumps(view_content), encoding="utf-8")

        with pytest.raises(ValueError, match="SAI KHÁC MÃ BĂM VIEW"):
            cli.validate_manifest_preflight(
                manifest_path, input_path, view_content,
                codebook_path=dummy_cb, dictionary_path=dummy_dict
            )

    def test_tamper_file_after_locking_fails_preflight(self, tmp_path):
        """Sửa tệp sau khóa (codebook hoặc dictionary) bị chặn tại preflight."""
        import scripts.annotate_cli as cli
        input_path = tmp_path / "view.json"
        dataset_id = "TEST-TAMPER"
        sp_ver = "PILOT-PLAN-V1-FULL-OVERLAP"
        export_blind_view(
            [{"sample_id": "S1", "url": "https://test.invalid/", "html": "<p>Content</p>"}],
            input_path,
            dataset_id=dataset_id,
            dataset_type="real_pilot_ready",
            sampling_plan_version=sp_ver,
        )
        view_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()

        dummy_cb = tmp_path / "CODEBOOK.md"
        dummy_cb.write_text("# Codebook\n**Phiên bản:** `v1.0.0`\n**Trạng thái:** `locked`\n" + "Rules content " * 20, encoding="utf-8")
        cb_hash = hashlib.sha256(dummy_cb.read_bytes()).hexdigest()

        dummy_dict = tmp_path / "dictionary.json"
        dummy_dict.write_text(json.dumps({
            "dictionary_id": "org_dictionary_v1",
            "version": "1.0.0",
            "status": "locked",
            "organizations": [{"id": f"org_{i}"} for i in range(14)],
        }), encoding="utf-8")
        dict_hash = hashlib.sha256(dummy_dict.read_bytes()).hexdigest()

        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps({
            "dataset_id": dataset_id,
            "sample_count": 1,
            "sampling_plan_version": sp_ver,
            "codebook_version": "1.0.0",
            "codebook_status": "locked",
            "dictionary_version": "1.0.0",
            "dictionary_status": "locked",
            "acceptance": {"B": "approved", "D": "approved"},
            "ready_for_annotation": True,
            "blind_view_sha256": view_hash,
            "codebook_sha256": cb_hash,
            "dictionary_sha256": dict_hash,
        }), encoding="utf-8")

        # Sửa codebook sau khi khóa
        dummy_cb.write_text("# Tampered Codebook", encoding="utf-8")
        with pytest.raises(ValueError, match="SAI KHÁC MÃ BĂM CODEBOOK"):
            cli.validate_manifest_preflight(
                manifest_path,
                input_path,
                {"samples": [{"sample_id": "S1"}], "dataset_id": dataset_id, "sampling_plan_version": sp_ver},
                codebook_path=dummy_cb,
                dictionary_path=dummy_dict,
            )

    def test_cli_blocks_codebook_override_in_real_session(self, tmp_path):
        """Chặn ghi đè codebook bằng CLI trong lượt thật."""
        import scripts.annotate_cli as cli
        input_path = tmp_path / "view.json"
        export_blind_view([], input_path, dataset_id="REAL-PILOT-32-V1", dataset_type="real_pilot_ready")
        output = tmp_path / "A.jsonl"
        with pytest.raises(ValueError, match="CỜ BỊ KHÓA"):
            cli.annotate_interactive_session("A", input_path, output, cli_codebook_version="hack_v2", dry_run=False)

    def test_kappa_rejects_mixed_packages_even_when_both_raters_have_same_hash_set(self):
        """Cùng tập hash {hash_A, hash_B} nhưng trộn hai gói trong cùng batch phải ném lỗi LỖI ĐA GÓI."""
        # Cả rater1 và rater2 cùng chứa các mẫu từ 2 gói dữ liệu hash_pkg_A và hash_pkg_B
        # Tập hợp hash của rater1: {hash_pkg_A, hash_pkg_B}
        # Tập hợp hash của rater2: {hash_pkg_A, hash_pkg_B}
        # Thuật toán cũ: clean_v1 != clean_v2 -> False (bỏ lọt lỗi trộn gói)
        # Thuật toán mới: len(clean_v1) > 1 -> ném ValueError("LỖI ĐA GÓI...")
        r1 = [
            {"sample_id": "S01", "class_label": "phishing", "dataset_id": "ds_A", "dataset_hash": "hash_pkg_A", "codebook_version": "1.0.0", "codebook_hash": "cb_1", "sampling_plan_version": "v1", "sample_content_hash": "c1"},
            {"sample_id": "S02", "class_label": "benign", "dataset_id": "ds_B", "dataset_hash": "hash_pkg_B", "codebook_version": "1.0.0", "codebook_hash": "cb_1", "sampling_plan_version": "v1", "sample_content_hash": "c2"},
            {"sample_id": "S03", "class_label": "phishing", "dataset_id": "ds_A", "dataset_hash": "hash_pkg_A", "codebook_version": "1.0.0", "codebook_hash": "cb_1", "sampling_plan_version": "v1", "sample_content_hash": "c3"},
        ]
        r2 = [
            {"sample_id": "S01", "class_label": "phishing", "dataset_id": "ds_A", "dataset_hash": "hash_pkg_A", "codebook_version": "1.0.0", "codebook_hash": "cb_1", "sampling_plan_version": "v1", "sample_content_hash": "c1"},
            {"sample_id": "S02", "class_label": "benign", "dataset_id": "ds_B", "dataset_hash": "hash_pkg_B", "codebook_version": "1.0.0", "codebook_hash": "cb_1", "sampling_plan_version": "v1", "sample_content_hash": "c2"},
            {"sample_id": "S03", "class_label": "phishing", "dataset_id": "ds_A", "dataset_hash": "hash_pkg_A", "codebook_version": "1.0.0", "codebook_hash": "cb_1", "sampling_plan_version": "v1", "sample_content_hash": "c3"},
        ]
        with pytest.raises(ValueError, match="LỖI ĐA GÓI"):
            compute_cohens_kappa(r1, r2, label_field="class_label")

    def test_kappa_shuffled_row_order_same_package_produces_identical_correct_result(self):
        """Đảo thứ tự dòng của cùng gói dữ liệu phải đối chiếu đúng theo sample_id và cho kết quả chuẩn xác."""
        common_prov = {
            "dataset_id": "REAL-PILOT-32-V1",
            "dataset_hash": "pilot_pkg_sha256_abcdef",
            "codebook_version": "1.0.0",
            "codebook_hash": "codebook_sha256_123456",
            "sampling_plan_version": "PILOT-PLAN-V1-FULL-OVERLAP",
            "random_subset": True,
        }
        # Thứ tự chuẩn gốc theo sample_id (4 khớp, 1 lệch)
        r1_ordered = [
            {**common_prov, "sample_id": "S01", "class_label": "phishing", "sample_content_hash": "cnt_01"},
            {**common_prov, "sample_id": "S02", "class_label": "benign", "sample_content_hash": "cnt_02"},
            {**common_prov, "sample_id": "S03", "class_label": "phishing", "sample_content_hash": "cnt_03"},
            {**common_prov, "sample_id": "S04", "class_label": "benign", "sample_content_hash": "cnt_04"},
            {**common_prov, "sample_id": "S05", "class_label": "phishing", "sample_content_hash": "cnt_05"},
        ]
        r2_ordered = [
            {**common_prov, "sample_id": "S01", "class_label": "phishing", "sample_content_hash": "cnt_01"},  # Agree (phish)
            {**common_prov, "sample_id": "S02", "class_label": "benign", "sample_content_hash": "cnt_02"},    # Agree (benign)
            {**common_prov, "sample_id": "S03", "class_label": "benign", "sample_content_hash": "cnt_03"},    # Disagree
            {**common_prov, "sample_id": "S04", "class_label": "benign", "sample_content_hash": "cnt_04"},    # Agree (benign)
            {**common_prov, "sample_id": "S05", "class_label": "phishing", "sample_content_hash": "cnt_05"},  # Agree (phish)
        ]
        res_baseline = compute_cohens_kappa(r1_ordered, r2_ordered, label_field="class_label")
        assert res_baseline.sample_count == 5
        assert res_baseline.observed_agreement == 0.8  # 4/5

        # Đảo thứ tự dòng ở rater1 và xáo trộn hoàn toàn ở rater2
        r1_shuffled = [r1_ordered[4], r1_ordered[0], r1_ordered[2], r1_ordered[1], r1_ordered[3]]
        r2_shuffled = [r2_ordered[1], r2_ordered[3], r2_ordered[4], r2_ordered[0], r2_ordered[2]]

        res_shuffled = compute_cohens_kappa(r1_shuffled, r2_shuffled, label_field="class_label")

        # Kết quả tính toán phải độc lập thứ tự dòng và chuẩn xác 100% với baseline
        assert res_shuffled.status == res_baseline.status == "valid"
        assert res_shuffled.sample_count == res_baseline.sample_count == 5
        assert res_shuffled.observed_agreement == res_baseline.observed_agreement == 0.8
        assert res_shuffled.expected_agreement == res_baseline.expected_agreement
        assert res_shuffled.kappa == res_baseline.kappa



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

    def test_resume_with_correct_provenance_skips_annotated_and_never_duplicates(self, tmp_path, cli_module):
        """File cũ thiếu provenance phải lỗi; khi đúng provenance thì resume bỏ qua mẫu đã làm và không ghi trùng."""
        from unittest.mock import patch

        samples = [
            {"sample_id": "SMP-001", "url": "https://a.test/login", "html": "<p>Login A</p>"},
            {"sample_id": "SMP-002", "url": "https://b.test/login", "html": "<p>Login B</p>"},
        ]
        blind_file = tmp_path / "real_view.json"
        export_blind_view(
            samples, blind_file,
            dataset_id="TEST-PKG",
            dataset_type="real_pilot_ready",
            sampling_plan_version="PILOT-PLAN-V1-FULL-OVERLAP",
        )
        view_hash = hashlib.sha256(blind_file.read_bytes()).hexdigest()
        dummy_cb = tmp_path / "LOCKED_CB.md"
        dummy_cb.write_text("# Codebook\n**Phiên bản:** `v1.0.0`\n**Trạng thái:** `locked`\n" + "Rules content " * 20, encoding="utf-8")
        cb_hash = hashlib.sha256(dummy_cb.read_bytes()).hexdigest()

        dummy_dict = tmp_path / "locked_dict.json"
        dummy_dict.write_text(json.dumps({
            "dictionary_id": "org_dictionary_v1",
            "version": "1.0.0",
            "status": "locked",
            "organizations": [{"id": f"org_{i}"} for i in range(14)],
        }), encoding="utf-8")
        dict_hash = hashlib.sha256(dummy_dict.read_bytes()).hexdigest()

        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps({
            "acceptance": {"B": "approved", "D": "approved"},
            "ready_for_annotation": True,
            "codebook_status": "locked",
            "codebook_version": "1.0.0",
            "dictionary_status": "locked",
            "dictionary_version": "1.0.0",
            "sample_count": 2,
            "blind_view_sha256": view_hash,
            "codebook_sha256": cb_hash,
            "dictionary_sha256": dict_hash,
            "dataset_id": "TEST-PKG",
            "sampling_plan_version": "PILOT-PLAN-V1-FULL-OVERLAP",
        }), encoding="utf-8")

        blind_data = json.loads(blind_file.read_text(encoding="utf-8"))
        s1_hash = compute_sample_content_hash(blind_data["samples"][0])

        out_file = tmp_path / "A_out.jsonl"

        # 1. Kiểm tra: file cũ thiếu provenance phải bị từ chối
        bad_rec = {
            "annotator_id": "A",
            "sample_id": "SMP-001",
            "pass_id": 1,
            "class_label": "phishing",
            "is_dry_run": False,
            # Thiếu provenance
        }
        out_file.write_text(json.dumps(bad_rec) + "\n", encoding="utf-8")
        with pytest.raises(ValueError, match="THIẾU PROVENANCE"):
            cli_module.annotate_interactive_session(
                "A", blind_file, out_file, manifest_path=manifest_file,
                codebook_path=dummy_cb, dictionary_path=dummy_dict
            )

        # 2. Chuẩn bị file cũ với ĐÚNG ĐẦY ĐỦ 6 TRƯỜNG PROVENANCE cho SMP-001
        valid_rec_1 = validate_annotation_record({
            "annotator_id": "A",
            "sample_id": "SMP-001",
            "pass_id": 1,
            "class_label": "phishing",
            "primary_org_status": "identified",
            "catalog_status": "in_catalog",
            "observed_service": "Office",
            "org_targets": ["microsoft"],
            "primary_org": "microsoft",
            "identity_role": "identity_claim",
            "domain_role": "first_party_identity",
            "evidence_note": "valid s1",
            "seconds_spent": 10.0,
            "random_subset": True,
            "difficult_case": False,
            "is_dry_run": False,
            "is_synthetic": False,
            "dataset_id": "TEST-PKG",
            "dataset_hash": view_hash,
            "codebook_version": "1.0.0",
            "codebook_hash": cb_hash,
            "sampling_plan_version": "PILOT-PLAN-V1-FULL-OVERLAP",
            "sample_content_hash": s1_hash,
            "timestamp_utc": "2026-10-05T00:00:00Z",
        })
        out_file.write_text(json.dumps(valid_rec_1.to_dict()) + "\n", encoding="utf-8")

        # 3. Tiếp tục phiên: CLI chỉ nhập SMP-002, bỏ qua SMP-001 và không ghi trùng
        mock_inputs_s2 = ["2", "1", "1", "Office", "google", "google", "1", "1", "valid s2", "n"]
        with patch("builtins.input", side_effect=mock_inputs_s2):
            cli_module.annotate_interactive_session(
                "A", blind_file, out_file, manifest_path=manifest_file,
                codebook_path=dummy_cb, dictionary_path=dummy_dict
            )

        records_after = [json.loads(line) for line in out_file.read_text(encoding="utf-8").strip().split("\n")]
        assert len(records_after) == 2, f"Kỳ vọng đúng 2 bản ghi, thực tế có {len(records_after)}"
        assert records_after[0]["sample_id"] == "SMP-001"
        assert records_after[1]["sample_id"] == "SMP-002"

        # 4. Khi chạy lại gói đã hoàn thành: không ghi thêm bất kỳ dòng trùng nào
        with patch("builtins.input", side_effect=[]):
            cli_module.annotate_interactive_session(
                "A", blind_file, out_file, manifest_path=manifest_file,
                codebook_path=dummy_cb, dictionary_path=dummy_dict
            )

        records_final = [json.loads(line) for line in out_file.read_text(encoding="utf-8").strip().split("\n")]
        assert len(records_final) == 2, "Chạy lại gói đã hoàn thành không được sinh thêm bản ghi trùng!"

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

    @staticmethod
    def _make_locked_artifacts(tmp_path):
        cb_file = tmp_path / "MOCK_CODEBOOK_LOCKED.md"
        dict_file = tmp_path / "mock_dictionary_locked.json"
        cb_content = (
            "# SỔ TAY QUY TẮC GÁN NHÃN\n\n"
            "**Phiên bản:** `v1.0.0`\n"
            "**Trạng thái:** `locked`\n"
            + "Quy tắc gán nhãn chuẩn hóa cho dự án NCKH_2. " * 10
        )
        cb_file.write_text(cb_content, encoding="utf-8")
        dict_data = {
            "dictionary_id": "org_dictionary_v1",
            "version": "1.0.0",
            "status": "locked",
            "organizations": [{"name": f"Org_{i}"} for i in range(14)],
        }
        dict_file.write_text(json.dumps(dict_data), encoding="utf-8")
        cb_hash = hashlib.sha256(cb_file.read_bytes()).hexdigest()
        dict_hash = hashlib.sha256(dict_file.read_bytes()).hexdigest()
        return cb_file, dict_file, cb_hash, dict_hash

    @staticmethod
    def _make_m(view_hash, cb_hash=None, dict_hash=None, **kwargs):
        root = Path(__file__).resolve().parent.parent
        cb_h = cb_hash or hashlib.sha256((root / "docs" / "CODEBOOK_V1.md").read_bytes()).hexdigest()
        dict_h = dict_hash or hashlib.sha256((root / "configs" / "dictionary_v1.json").read_bytes()).hexdigest()
        base = {
            "dataset_id": "TEST-REAL",
            "sample_count": 1,
            "sampling_plan_version": "PLAN-V1",
            "codebook_version": "1.0.0",
            "codebook_status": "locked",
            "dictionary_version": "1.0.0",
            "dictionary_status": "locked",
            "acceptance": {"B": "approved", "D": "approved"},
            "ready_for_annotation": True,
            "blind_view_sha256": view_hash,
            "codebook_sha256": cb_h,
            "dictionary_sha256": dict_h,
        }
        base.update(kwargs)
        return base

    def test_cli_manifest_preflight_blocks_unapproved_or_pending(self, tmp_path, cli_module):
        """CLI kiểm tra toàn bộ điều kiện manifest trước khi cho phép phiên người thật hoạt động."""
        input_blind = tmp_path / "real_view.json"
        export_blind_view(
            [{"sample_id": "SMP-001", "url": "https://test.invalid/", "html": "<p>Content</p>"}],
            input_blind,
            dataset_id="TEST-REAL",
            dataset_type="real_pilot_ready",
            sampling_plan_version="PLAN-V1",
        )
        out_file = tmp_path / "A_real.jsonl"
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()

        # 1. B và D chưa nghiệm thu đầy đủ
        m1 = tmp_path / "m1.json"
        m1.write_text(json.dumps(self._make_m(view_hash, acceptance={"B": "approved", "D": "pending"})), encoding="utf-8")
        with pytest.raises(ValueError, match="CHƯA NGHIỆM THU"):
            cli_module.annotate_interactive_session("A", input_blind, out_file, manifest_path=m1)

        # 2. ready_for_annotation=False
        m2 = tmp_path / "m2.json"
        m2.write_text(json.dumps(self._make_m(view_hash, ready_for_annotation=False)), encoding="utf-8")
        with pytest.raises(ValueError, match="CHƯA SẴN SÀNG"):
            cli_module.annotate_interactive_session("A", input_blind, out_file, manifest_path=m2)

        # 3. codebook_status chưa locked
        m3 = tmp_path / "m3.json"
        m3.write_text(json.dumps(self._make_m(view_hash, codebook_status="pending_review")), encoding="utf-8")
        with pytest.raises(ValueError, match="CODEBOOK CHƯA KHÓA"):
            cli_module.annotate_interactive_session("A", input_blind, out_file, manifest_path=m3)

        # 4. Hash view không khớp
        m4 = tmp_path / "m4.json"
        m4.write_text(json.dumps(self._make_m("wrong_hash_12345")), encoding="utf-8")
        with pytest.raises(ValueError, match="SAI KHÁC MÃ BĂM VIEW"):
            cli_module.annotate_interactive_session("A", input_blind, out_file, manifest_path=m4)

        # 5. Số mẫu không khớp
        cb_file, dict_file, cb_hash, dict_hash = self._make_locked_artifacts(tmp_path)
        m5 = tmp_path / "m5.json"
        m5.write_text(json.dumps(self._make_m(view_hash, cb_hash=cb_hash, dict_hash=dict_hash, sample_count=99)), encoding="utf-8")
        with pytest.raises(ValueError, match="SAI KHÁC SỐ MẪU"):
            cli_module.annotate_interactive_session(
                "A", input_blind, out_file, manifest_path=m5,
                codebook_path=cb_file, dictionary_path=dict_file
            )

    def test_cli_manifest_checked_before_displaying_any_sample(self, tmp_path, cli_module):
        """CLI bắt buộc kiểm tra manifest trước khi hiển thị bất kỳ mẫu nào; không được lộ mẫu khi manifest chưa duyệt."""
        from unittest.mock import patch

        input_blind = tmp_path / "real_view_display_check.json"
        export_blind_view(
            [
                {"sample_id": "SMP-001", "url": "https://secret-phish-domain.test/login", "html": "<p>Secret Phish Content</p>"},
                {"sample_id": "SMP-002", "url": "https://secret-bank-domain.test/auth", "html": "<p>Secret Bank Content</p>"},
            ],
            input_blind,
            dataset_id="REAL-PILOT-32-V1",
            dataset_type="real_pilot_ready",
            sampling_plan_version="PILOT-PLAN-V1-FULL-OVERLAP",
        )
        out_file = tmp_path / "A_display_check.jsonl"
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()

        # Manifest chưa được Lead D nghiệm thu
        unapproved_manifest = tmp_path / "unapproved_manifest.json"
        unapproved_manifest.write_text(json.dumps(self._make_m(
            view_hash,
            dataset_id="REAL-PILOT-32-V1",
            sample_count=2,
            sampling_plan_version="PILOT-PLAN-V1-FULL-OVERLAP",
            acceptance={"B": "approved", "D": "pending"},
            ready_for_annotation=False,
            codebook_status="pending_review",
        )), encoding="utf-8")

        with patch.object(cli_module, "display_sample_and_allow_reading") as mock_display:
            with pytest.raises(ValueError, match="CHƯA NGHIỆM THU"):
                cli_module.annotate_interactive_session("A", input_blind, out_file, manifest_path=unapproved_manifest)
            # Khẳng định tuyệt đối: hàm hiển thị mẫu KHÔNG BAO GIỜ được gọi
            assert mock_display.call_count == 0

    def test_cli_manifest_checked_even_in_dry_run_for_real_pilot(self, tmp_path, cli_module):
        """CLI vẫn kiểm tra manifest ngay cả khi có cờ --dry-run nếu là gói pilot thật; tuyệt đối không bỏ qua manifest."""
        from unittest.mock import patch

        input_blind = tmp_path / "real_view_dryrun_check.json"
        export_blind_view(
            [{"sample_id": "SMP-001", "url": "https://confidential.test/", "html": "<p>Confidential</p>"}],
            input_blind,
            dataset_id="REAL-PILOT-32-V1",
            dataset_type="real_pilot_pending_review",
            sampling_plan_version="PILOT-PLAN-V1-FULL-OVERLAP",
        )
        out_file = tmp_path / "A_dryrun_check.jsonl"
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()

        # Manifest có ready_for_annotation=false
        unready_manifest = tmp_path / "unready_manifest.json"
        unready_manifest.write_text(json.dumps(self._make_m(
            view_hash,
            dataset_id="REAL-PILOT-32-V1",
            sample_count=1,
            sampling_plan_version="PILOT-PLAN-V1-FULL-OVERLAP",
            acceptance={"B": "approved", "D": "approved"},
            ready_for_annotation=False,
            codebook_status="locked",
        )), encoding="utf-8")

        with patch.object(cli_module, "display_sample_and_allow_reading") as mock_display:
            with pytest.raises(ValueError, match="CHƯA SẴN SÀNG"):
                cli_module.annotate_interactive_session(
                    "A", input_blind, out_file, manifest_path=unready_manifest, dry_run=True
                )
            assert mock_display.call_count == 0

    def test_manifest_preflight_rejects_missing_blind_view_sha256(self, tmp_path, cli_module):
        """Preflight từ chối nếu manifest thiếu trường bắt buộc blind_view_sha256."""
        input_blind = tmp_path / "view.json"
        export_blind_view(
            [{"sample_id": "S1", "url": "https://test.invalid/", "html": "<p>Hi</p>"}],
            input_blind,
            dataset_id="TEST-DS",
            sampling_plan_version="PLAN-V1",
        )
        data = json.loads(input_blind.read_text(encoding="utf-8"))
        m_file = tmp_path / "m_no_hash.json"
        m = self._make_m("dummy", dataset_id="TEST-DS", sampling_plan_version="PLAN-V1", sample_count=1)
        del m["blind_view_sha256"]
        m_file.write_text(json.dumps(m), encoding="utf-8")

        with pytest.raises(ValueError, match="THIẾU TRƯỜNG MANIFEST BẮT BUỘC.*blind_view_sha256|THIẾU MÃ BĂM MANIFEST"):
            cli_module.validate_manifest_preflight(m_file, input_blind, data)

    def test_manifest_preflight_rejects_pending_codebook_version(self, tmp_path, cli_module):
        """Preflight từ chối nếu codebook_version trong manifest vẫn ở trạng thái pending."""
        input_blind = tmp_path / "view.json"
        export_blind_view(
            [{"sample_id": "S1", "url": "https://test.invalid/", "html": "<p>Hi</p>"}],
            input_blind,
            dataset_id="TEST-DS",
            sampling_plan_version="PLAN-V1",
        )
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()
        data = json.loads(input_blind.read_text(encoding="utf-8"))
        m_file = tmp_path / "m_cb_pending.json"
        m_file.write_text(json.dumps(self._make_m(
            view_hash,
            dataset_id="TEST-DS",
            sampling_plan_version="PLAN-V1",
            sample_count=1,
            codebook_version="v1.0.0-pending-review",
        )), encoding="utf-8")

        with pytest.raises(ValueError, match="CODEBOOK CHƯA KHÓA"):
            cli_module.validate_manifest_preflight(m_file, input_blind, data)

    def test_manifest_preflight_rejects_unlocked_dictionary_status(self, tmp_path, cli_module):
        """Preflight từ chối nếu dictionary_status trong manifest không phải locked."""
        input_blind = tmp_path / "view.json"
        export_blind_view(
            [{"sample_id": "S1", "url": "https://test.invalid/", "html": "<p>Hi</p>"}],
            input_blind,
            dataset_id="TEST-DS",
            sampling_plan_version="PLAN-V1",
        )
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()
        data = json.loads(input_blind.read_text(encoding="utf-8"))
        m_file = tmp_path / "m_dict_pending.json"
        m_file.write_text(json.dumps(self._make_m(
            view_hash,
            dataset_id="TEST-DS",
            sampling_plan_version="PLAN-V1",
            sample_count=1,
            dictionary_status="draft",
        )), encoding="utf-8")

        with pytest.raises(ValueError, match="DICTIONARY CHƯA KHÓA"):
            cli_module.validate_manifest_preflight(m_file, input_blind, data)

    def test_manifest_preflight_rejects_pending_dictionary_version(self, tmp_path, cli_module):
        """Preflight từ chối nếu dictionary_version trong manifest khai báo trạng thái pending."""
        input_blind = tmp_path / "view.json"
        export_blind_view(
            [{"sample_id": "S1", "url": "https://test.invalid/", "html": "<p>Hi</p>"}],
            input_blind,
            dataset_id="TEST-DS",
            sampling_plan_version="PLAN-V1",
        )
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()
        data = json.loads(input_blind.read_text(encoding="utf-8"))
        m_file = tmp_path / "m_dict_ver_pending.json"
        m_file.write_text(json.dumps(self._make_m(
            view_hash,
            dataset_id="TEST-DS",
            sampling_plan_version="PLAN-V1",
            sample_count=1,
            dictionary_status="locked",
            dictionary_version="1.0.0-pending_review",
        )), encoding="utf-8")

        with pytest.raises(ValueError, match="DICTIONARY CHƯA KHÓA"):
            cli_module.validate_manifest_preflight(m_file, input_blind, data)

    def test_manifest_preflight_rejects_codebook_disk_hash_mismatch(self, tmp_path, cli_module):
        """Preflight từ chối nếu codebook_sha256 trong manifest không khớp mã băm docs/CODEBOOK_V1.md trên đĩa."""
        input_blind = tmp_path / "view.json"
        export_blind_view(
            [{"sample_id": "S1", "url": "https://test.invalid/", "html": "<p>Hi</p>"}],
            input_blind,
            dataset_id="TEST-DS",
            sampling_plan_version="PLAN-V1",
        )
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()
        data = json.loads(input_blind.read_text(encoding="utf-8"))
        m_file = tmp_path / "m_cb_mismatch.json"
        m_file.write_text(json.dumps(self._make_m(
            view_hash,
            dataset_id="TEST-DS",
            sampling_plan_version="PLAN-V1",
            sample_count=1,
            codebook_sha256="fake_cb_hash_mismatch_12345",
        )), encoding="utf-8")

        with pytest.raises(ValueError, match="SAI KHÁC MÃ BĂM CODEBOOK"):
            cli_module.validate_manifest_preflight(m_file, input_blind, data)

    def test_manifest_preflight_rejects_dictionary_disk_hash_mismatch(self, tmp_path, cli_module):
        """Preflight từ chối nếu dictionary_sha256 trong manifest không khớp configs/dictionary_v1.json trên đĩa."""
        cb_file, dict_file, cb_hash, dict_hash = self._make_locked_artifacts(tmp_path)
        input_blind = tmp_path / "view.json"
        export_blind_view(
            [{"sample_id": "S1", "url": "https://test.invalid/", "html": "<p>Hi</p>"}],
            input_blind,
            dataset_id="TEST-DS",
            sampling_plan_version="PLAN-V1",
        )
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()
        data = json.loads(input_blind.read_text(encoding="utf-8"))
        m_file = tmp_path / "m_dict_mismatch.json"
        m_file.write_text(json.dumps(self._make_m(
            view_hash,
            cb_hash=cb_hash,
            dict_hash="fake_dict_hash_mismatch_12345",
            dataset_id="TEST-DS",
            sampling_plan_version="PLAN-V1",
            sample_count=1,
            dictionary_sha256="fake_dict_hash_mismatch_12345",
        )), encoding="utf-8")

        with pytest.raises(ValueError, match="SAI KHÁC MÃ BĂM DICTIONARY"):
            cli_module.validate_manifest_preflight(
                m_file, input_blind, data,
                codebook_path=cb_file, dictionary_path=dict_file
            )

    def test_manifest_preflight_rejects_view_metadata_hash_mismatch(self, tmp_path, cli_module):
        """Preflight từ chối nếu metadata gói view khai báo hash codebook/dictionary không khớp manifest."""
        cb_file, dict_file, cb_hash, dict_hash = self._make_locked_artifacts(tmp_path)

        input_blind = tmp_path / "view.json"
        export_blind_view(
            [{"sample_id": "S1", "url": "https://test.invalid/", "html": "<p>Hi</p>"}],
            input_blind,
            dataset_id="TEST-DS",
            sampling_plan_version="PLAN-V1",
        )
        data = json.loads(input_blind.read_text(encoding="utf-8"))
        # Giả lập metadata gói view khai báo sai khác hash codebook
        data["codebook_sha256"] = "mismatched_view_cb_hash"
        input_blind.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()

        m_file = tmp_path / "m_valid.json"
        m_file.write_text(json.dumps(self._make_m(
            view_hash,
            cb_hash=cb_hash,
            dict_hash=dict_hash,
            dataset_id="TEST-DS",
            sampling_plan_version="PLAN-V1",
            sample_count=1,
            codebook_sha256=cb_hash,
            dictionary_sha256=dict_hash,
        )), encoding="utf-8")

        with pytest.raises(ValueError, match="SAI KHÁC MÃ BĂM CODEBOOK TRONG GÓI"):
            cli_module.validate_manifest_preflight(
                m_file, input_blind, data,
                codebook_path=cb_file, dictionary_path=dict_file
            )

        # Giả lập metadata gói view khai báo sai khác hash dictionary
        data["codebook_sha256"] = cb_hash
        data["dictionary_sha256"] = "mismatched_view_dict_hash"
        input_blind.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        view_hash2 = hashlib.sha256(input_blind.read_bytes()).hexdigest()
        m_file.write_text(json.dumps(self._make_m(
            view_hash2,
            cb_hash=cb_hash,
            dict_hash=dict_hash,
            dataset_id="TEST-DS",
            sampling_plan_version="PLAN-V1",
            sample_count=1,
            codebook_sha256=cb_hash,
            dictionary_sha256=dict_hash,
        )), encoding="utf-8")

        with pytest.raises(ValueError, match="SAI KHÁC MÃ BĂM DICTIONARY TRONG GÓI"):
            cli_module.validate_manifest_preflight(
                m_file, input_blind, data,
                codebook_path=cb_file, dictionary_path=dict_file
            )

    def test_manifest_preflight_rejects_dataset_id_and_sampling_plan_mismatch(self, tmp_path, cli_module):
        """Preflight từ chối nếu dataset_id hoặc sampling_plan_version không khớp manifest."""
        cb_file, dict_file, cb_hash, dict_hash = self._make_locked_artifacts(tmp_path)
        input_blind = tmp_path / "view.json"
        export_blind_view(
            [{"sample_id": "S1", "url": "https://test.invalid/", "html": "<p>Hi</p>"}],
            input_blind,
            dataset_id="PACKAGE-ID-1",
            sampling_plan_version="PLAN-V1",
        )
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()
        data = json.loads(input_blind.read_text(encoding="utf-8"))

        m_file = tmp_path / "m.json"
        # 1. Mismatch dataset_id
        m_file.write_text(json.dumps(self._make_m(
            view_hash,
            cb_hash=cb_hash,
            dict_hash=dict_hash,
            dataset_id="DIFFERENT-ID",
            sampling_plan_version="PLAN-V1",
            sample_count=1,
        )), encoding="utf-8")
        with pytest.raises(ValueError, match="SAI KHÁC DATASET_ID"):
            cli_module.validate_manifest_preflight(
                m_file, input_blind, data,
                codebook_path=cb_file, dictionary_path=dict_file
            )

        # 2. Mismatch sampling_plan_version
        m_file.write_text(json.dumps(self._make_m(
            view_hash,
            cb_hash=cb_hash,
            dict_hash=dict_hash,
            dataset_id="PACKAGE-ID-1",
            sampling_plan_version="PLAN-V2",
            sample_count=1,
        )), encoding="utf-8")
        with pytest.raises(ValueError, match="SAI KHÁC SAMPLING_PLAN"):
            cli_module.validate_manifest_preflight(
                m_file, input_blind, data,
                codebook_path=cb_file, dictionary_path=dict_file
            )

    def test_manifest_preflight_passes_when_all_conditions_and_hashes_valid(self, tmp_path, cli_module):
        """Preflight thành công mỹ mãn khi tất cả trạng thái nghiệm thu và mã băm đĩa đều khớp hoàn hảo."""
        cb_file, dict_file, cb_hash, dict_hash = self._make_locked_artifacts(tmp_path)

        input_blind = tmp_path / "view.json"
        export_blind_view(
            [
                {"sample_id": "S1", "url": "https://test.invalid/1", "html": "<p>Page 1</p>"},
                {"sample_id": "S2", "url": "https://test.invalid/2", "html": "<p>Page 2</p>"},
            ],
            input_blind,
            dataset_id="VALID-PILOT-V1",
            sampling_plan_version="PLAN-V1",
        )
        data = json.loads(input_blind.read_text(encoding="utf-8"))
        data["codebook_sha256"] = cb_hash
        data["dictionary_sha256"] = dict_hash
        input_blind.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()

        m_file = tmp_path / "m_good.json"
        manifest_payload = self._make_m(
            view_hash,
            cb_hash=cb_hash,
            dict_hash=dict_hash,
            dataset_id="VALID-PILOT-V1",
            sampling_plan_version="PLAN-V1",
            sample_count=2,
            codebook_version="v1.0.0",
            dictionary_version="1.0.0",
            codebook_sha256=cb_hash,
            dictionary_sha256=dict_hash,
        )
        m_file.write_text(json.dumps(manifest_payload), encoding="utf-8")

        res = cli_module.validate_manifest_preflight(
            m_file, input_blind, data,
            codebook_path=cb_file, dictionary_path=dict_file
        )
        assert res["ready_for_annotation"] is True
        assert res["blind_view_sha256"] == view_hash

    def test_lead_d_probe_artifact_pending_when_manifest_locked_fails(self, tmp_path, cli_module):
        """Lead D probe: Codebook/Dictionary còn pending_review trên đĩa; nếu manifest ghi locked và hash khớp thì preflight bắt buộc phải ném lỗi."""
        input_blind = tmp_path / "view.json"
        export_blind_view(
            [{"sample_id": "SMP-001", "url": "https://test.invalid/", "html": "<p>Test</p>"}],
            input_blind,
            dataset_id="TEST-REAL",
            sampling_plan_version="PLAN-V1",
        )
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()
        data = json.loads(input_blind.read_text(encoding="utf-8"))

        # 1. Codebook pending fixture
        pending_cb = tmp_path / "PENDING_CODEBOOK.md"
        pending_cb.write_text(
            "# SỔ TAY QUY TẮC GÁN NHÃN\n\n"
            "**Phiên bản:** `v1.0.0-pending_review`\n"
            "**Trạng thái:** `pending_review`\n"
            + "Nội dung quy tắc... " * 10,
            encoding="utf-8",
        )
        locked_dict = tmp_path / "LOCKED_DICT.json"
        locked_dict.write_text(
            json.dumps({
                "dictionary_id": "org_dictionary_v1",
                "version": "1.0.0",
                "status": "locked",
                "organizations": [{"name": f"Org_{i}"} for i in range(14)],
            }),
            encoding="utf-8",
        )
        cb_hash = hashlib.sha256(pending_cb.read_bytes()).hexdigest()
        dict_hash = hashlib.sha256(locked_dict.read_bytes()).hexdigest()

        m_file = tmp_path / "fake_locked_manifest.json"
        m_file.write_text(json.dumps(self._make_m(
            view_hash,
            cb_hash=cb_hash,
            dict_hash=dict_hash,
            codebook_status="locked",
            dictionary_status="locked",
            codebook_version="v1.0.0",
            dictionary_version="1.0.0",
        )), encoding="utf-8")

        with pytest.raises(ValueError, match="ARTIFACT CODEBOOK CHƯA KHÓA"):
            cli_module.validate_manifest_preflight(
                m_file, input_blind, data,
                codebook_path=pending_cb, dictionary_path=locked_dict
            )

        # 2. Dictionary pending fixture
        locked_cb = tmp_path / "LOCKED_CODEBOOK.md"
        locked_cb.write_text(
            "# SỔ TAY QUY TẮC GÁN NHÃN\n\n"
            "**Phiên bản:** `v1.0.0`\n"
            "**Trạng thái:** `locked`\n"
            + "Nội dung quy tắc... " * 10,
            encoding="utf-8",
        )
        pending_dict = tmp_path / "PENDING_DICT.json"
        pending_dict.write_text(
            json.dumps({
                "dictionary_id": "org_dictionary_v1",
                "version": "1.0.0-pending_review",
                "status": "pending_review",
                "organizations": [{"name": f"Org_{i}"} for i in range(14)],
            }),
            encoding="utf-8",
        )
        locked_cb_hash = hashlib.sha256(locked_cb.read_bytes()).hexdigest()
        pending_dict_hash = hashlib.sha256(pending_dict.read_bytes()).hexdigest()

        m_file2 = tmp_path / "fake_locked_manifest2.json"
        m_file2.write_text(json.dumps(self._make_m(
            view_hash,
            cb_hash=locked_cb_hash,
            dict_hash=pending_dict_hash,
            codebook_status="locked",
            dictionary_status="locked",
            codebook_version="v1.0.0",
            dictionary_version="1.0.0",
        )), encoding="utf-8")

        with pytest.raises(ValueError, match="ARTIFACT DICTIONARY CHƯA KHÓA"):
            cli_module.validate_manifest_preflight(
                m_file2, input_blind, data,
                codebook_path=locked_cb, dictionary_path=pending_dict
            )

    def test_lead_d_probe_sample_with_mismatched_codebook_version_fails(self, tmp_path, cli_module):
        """Lead D probe: Mẫu có codebook_version='WRONG-VERSION' bị từ chối ngay trước khi hiển thị; không ghi annotation theo version chưa kiểm."""
        cb_file, dict_file, cb_hash, dict_hash = self._make_locked_artifacts(tmp_path)
        input_blind = tmp_path / "view_wrong_sample_cb.json"
        samples = [
            {"sample_id": "SMP-001", "url": "https://test.invalid/1", "html": "<p>P1</p>", "codebook_version": "v1.0.0"},
            {"sample_id": "SMP-002", "url": "https://test.invalid/2", "html": "<p>P2</p>", "codebook_version": "WRONG-VERSION"},
        ]
        export_blind_view(
            samples,
            input_blind,
            dataset_id="TEST-REAL",
            sampling_plan_version="PLAN-V1",
        )
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()
        data = json.loads(input_blind.read_text(encoding="utf-8"))

        m_file = tmp_path / "m.json"
        m_file.write_text(json.dumps(self._make_m(
            view_hash,
            cb_hash=cb_hash,
            dict_hash=dict_hash,
            codebook_version="v1.0.0",
            sample_count=2,
        )), encoding="utf-8")

        with pytest.raises(ValueError, match="SAI KHÁC PHIÊN BẢN CODEBOOK TRÊN MẪU"):
            cli_module.validate_manifest_preflight(
                m_file, input_blind, data,
                codebook_path=cb_file, dictionary_path=dict_file
            )

        from unittest.mock import patch
        out_file = tmp_path / "A_wrong_sample.jsonl"
        with patch.object(cli_module, "display_sample_and_allow_reading") as mock_display:
            with pytest.raises(ValueError, match="SAI KHÁC PHIÊN BẢN CODEBOOK TRÊN MẪU"):
                cli_module.annotate_interactive_session(
                    "A", input_blind, out_file, manifest_path=m_file,
                    codebook_path=cb_file, dictionary_path=dict_file, dry_run=True
                )
            assert mock_display.call_count == 0

    def test_lead_d_probe_sample_count_zero_boolean_empty_fails(self, tmp_path, cli_module):
        """Lead D probe: sample_count=0, boolean (True/False), hoặc samples=[] bị từ chối triệt để."""
        cb_file, dict_file, cb_hash, dict_hash = self._make_locked_artifacts(tmp_path)
        input_blind = tmp_path / "view.json"
        export_blind_view(
            [{"sample_id": "SMP-001", "url": "https://test.invalid/", "html": "<p>Hi</p>"}],
            input_blind,
            dataset_id="TEST-REAL",
            sampling_plan_version="PLAN-V1",
        )
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()
        data = json.loads(input_blind.read_text(encoding="utf-8"))

        m_file = tmp_path / "m.json"

        # a) sample_count = 0
        m_file.write_text(json.dumps(self._make_m(
            view_hash, cb_hash=cb_hash, dict_hash=dict_hash, sample_count=0
        )), encoding="utf-8")
        with pytest.raises(ValueError, match="sample_count trong manifest phải là số nguyên dương"):
            cli_module.validate_manifest_preflight(m_file, input_blind, data, codebook_path=cb_file, dictionary_path=dict_file)

        # b) sample_count = True (boolean)
        m_file.write_text(json.dumps(self._make_m(
            view_hash, cb_hash=cb_hash, dict_hash=dict_hash, sample_count=True
        )), encoding="utf-8")
        with pytest.raises(ValueError, match="không nhận boolean"):
            cli_module.validate_manifest_preflight(m_file, input_blind, data, codebook_path=cb_file, dictionary_path=dict_file)

        # c) samples = [] (gói rỗng)
        empty_blind = tmp_path / "empty_view.json"
        empty_data = {
            "dataset_id": "TEST-REAL",
            "sampling_plan_version": "PLAN-V1",
            "samples": [],
        }
        empty_blind.write_text(json.dumps(empty_data), encoding="utf-8")
        empty_hash = hashlib.sha256(empty_blind.read_bytes()).hexdigest()
        m_file.write_text(json.dumps(self._make_m(
            empty_hash, cb_hash=cb_hash, dict_hash=dict_hash, sample_count=1
        )), encoding="utf-8")
        with pytest.raises(ValueError, match="danh sách các mẫu không rỗng"):
            cli_module.validate_manifest_preflight(m_file, empty_blind, empty_data, codebook_path=cb_file, dictionary_path=dict_file)

    def test_lead_d_probe_real_pilot_32_wrong_count_fails(self, tmp_path, cli_module):
        """Lead D probe: Gói REAL-PILOT-32-V1 yêu cầu đúng 32 mẫu theo kế hoạch đã chốt; sai số lượng phải lỗi."""
        cb_file, dict_file, cb_hash, dict_hash = self._make_locked_artifacts(tmp_path)
        input_blind = tmp_path / "pilot_view_wrong_count.json"
        # Tạo 31 mẫu thay vì 32
        samples_31 = [{"sample_id": f"PILOT-{i:03d}", "url": f"https://test.invalid/{i}", "html": "<p>P</p>"} for i in range(1, 32)]
        export_blind_view(
            samples_31,
            input_blind,
            dataset_id="REAL-PILOT-32-V1",
            sampling_plan_version="PILOT-PLAN-V1-FULL-OVERLAP",
        )
        view_hash = hashlib.sha256(input_blind.read_bytes()).hexdigest()
        data = json.loads(input_blind.read_text(encoding="utf-8"))

        m_file = tmp_path / "m_real32.json"

        # Manifest khai báo 31 mẫu cho REAL-PILOT-32-V1 -> lỗi
        m_file.write_text(json.dumps(self._make_m(
            view_hash, cb_hash=cb_hash, dict_hash=dict_hash,
            dataset_id="REAL-PILOT-32-V1",
            sampling_plan_version="PILOT-PLAN-V1-FULL-OVERLAP",
            sample_count=31,
        )), encoding="utf-8")
        with pytest.raises(ValueError, match="Gói REAL-PILOT-32-V1 yêu cầu manifest sample_count đúng 32 mẫu"):
            cli_module.validate_manifest_preflight(m_file, input_blind, data, codebook_path=cb_file, dictionary_path=dict_file)

        # Manifest khai báo 32 mẫu nhưng gói view chỉ có 31 mẫu -> lỗi
        m_file.write_text(json.dumps(self._make_m(
            view_hash, cb_hash=cb_hash, dict_hash=dict_hash,
            dataset_id="REAL-PILOT-32-V1",
            sampling_plan_version="PILOT-PLAN-V1-FULL-OVERLAP",
            sample_count=32,
        )), encoding="utf-8")
        with pytest.raises(ValueError, match="Gói view có 31 mẫu, nhưng manifest khai báo 32 mẫu"):
            cli_module.validate_manifest_preflight(m_file, input_blind, data, codebook_path=cb_file, dictionary_path=dict_file)






