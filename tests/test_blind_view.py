"""Bộ kiểm thử cho Blind View, cơ chế chống rò rỉ nhãn và AnnotationRecord (Task LABEL-01).

Kiểm tra:
1. assert_no_label_leak phát hiện và ném lỗi khi xuất hiện bất kỳ trường nhãn hoặc metadata cấm.
2. extract_safe_view_content loại bỏ 100% script, iframe, inline events và bóc tách text an toàn.
3. create_blind_sample tạo mẫu BlindSample hợp lệ, không rò rỉ nhãn.
4. validate_annotation_record xác thực chặt chẽ theo đúng chuẩn docs/CODEBOOK_V1.md.
5. export_blind_view xuất gói JSON Blind View hoàn chỉnh cho A và B.
6. Luồng tích hợp giữa lượt gán nhãn AnnotationRecord và tính toán Cohen's Kappa.
"""

import json
from pathlib import Path
import pytest

from phishing.annotation import (
    AnnotationRecord,
    BlindSample,
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
        # Không được ném ngoại lệ
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

        d = record.to_dict()
        assert d["seconds_spent"] == 142.5
        assert d["random_subset"] is True

    def test_invalid_class_label_rejected(self):
        invalid_dict = {
            "annotator_id": "A",
            "sample_id": "BLIND-001",
            "pass_id": 1,
            "class_label": "malicious",  # Sai enum (chỉ cho phép: phishing, benign, insufficient_evidence)
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
            "identity_role": "first_party_login",  # Sai enum (đây là domain_role hoặc enum cũ)
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
            "seconds_spent": -15.0,  # Thời gian âm không hợp lệ
            "random_subset": True,
            "difficult_case": False,
        }
        with pytest.raises(ValueError, match="seconds_spent=-15.0 không được âm"):
            validate_annotation_record(invalid_dict)


class TestBlindViewExportAndKappaFlow:
    """Kiểm tra xuất file gói mù và tích hợp đo đạc Cohen's Kappa giữa A và B."""

    def test_export_blind_view_writes_json(self, tmp_path):
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
        payload = export_blind_view(raw_samples, out_file)
        assert out_file.exists()
        assert payload["total_samples"] == 2
        assert len(payload["samples"]) == 2

        # Đọc lại từ file và kiểm tra tính toàn vẹn
        saved_data = json.loads(out_file.read_text(encoding="utf-8"))
        assert saved_data["total_samples"] == 2
        assert saved_data["samples"][0]["sample_id"] == "S101"
        assert_no_label_leak(saved_data)

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

        # Trích xuất nhãn lớp và tính Cohen's Kappa
        labels_a = [r.class_label for r in records_a]
        labels_b = [r.class_label for r in records_b]
        is_difficult = [r.difficult_case for r in records_a]

        kappa_res = compute_cohens_kappa(labels_a, labels_b, is_difficult=is_difficult)
        assert kappa_res.status == "valid"
        assert kappa_res.observed_agreement == 0.8
        assert kappa_res.sample_count == 5
        assert 0.0 < kappa_res.kappa <= 1.0
