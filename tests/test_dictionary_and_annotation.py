"""Bộ kiểm thử đơn vị cho Dictionary V1, Matcher dùng chung và Cohen's Kappa (Task DATA-02).

Tuân thủ nghiêm ngặt chỉ đạo của Lead D:
1. Dùng trực tiếp module matcher dùng chung (src/phishing/features/domains.py), không dùng helper riêng.
2. Kiểm tra forms.office.com và các endpoint lưu trữ (S3, Azure Blob/Web, GCS, SharePoint).
3. Kiểm tra tính độc lập thứ tự quy tắc (UGC luôn thắng bất kể thứ tự khai báo).
4. Kiểm tra DNS boundary chống tấn công tiền tố/hậu tố/substring.
5. Kiểm tra compute_cohens_kappa: khi Pe=1.0 trả về None và status='undefined_single_class'.
"""

import json
from pathlib import Path
import re
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DICT_PATH = PROJECT_ROOT / "configs" / "dictionary_v1.json"
MANIFEST_PATH = PROJECT_ROOT / "configs" / "source_manifest.json"
EXCLUSION_PATH = PROJECT_ROOT / "data" / "exclusion_registry.json"

from phishing.data import verify_sha256
from phishing.features.domains import DomainRule, domain_relation, load_rules_from_org_dict
from phishing.annotation import compute_cohens_kappa, compute_cohens_kappa_from_labels, KappaResult


class TestConfigIntegrity:
    """Kiểm tra cấu trúc và tính toàn vẹn của các file JSON cấu hình."""

    def test_dictionary_v1_json_valid(self):
        assert DICT_PATH.exists(), f"Không tìm thấy file {DICT_PATH}"
        data = json.loads(DICT_PATH.read_text(encoding="utf-8"))
        assert data["dictionary_id"] == "org_dictionary_v1"
        assert data["status"] in ("pending_review", "locked", "approved")
        assert len(data["organizations"]) == 14
        assert "roles_definition" in data
        assert "review_status" in data
        assert "temporal_protocol_note" in data

    def test_source_manifest_json_valid(self):
        assert MANIFEST_PATH.exists()
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        assert manifest["revision"] == "eabec4b7a66324b79cc8a0ad856d1731dc26fe1a"
        assert manifest["total_records"] == 498255
        assert manifest["total_shards"] == 56
        assert len(manifest["files"]) == 56

    def test_exclusion_registry_valid(self):
        assert EXCLUSION_PATH.exists()
        excl = json.loads(EXCLUSION_PATH.read_text(encoding="utf-8"))
        assert excl["total_excluded_samples"] == sum(len(e.get("samples", [])) for e in excl["exclusions"])
        assert excl["total_excluded_samples"] >= 32
        assert excl["exclusions"][0]["mapping_status"] == "unresolved_source_mapping"


class TestDomainRulesAndSharedMatcher:
    """Kiểm tra matcher dùng chung với quy tắc từ dictionary_v1.json."""

    @pytest.fixture
    def dict_data(self):
        return json.loads(DICT_PATH.read_text(encoding="utf-8"))

    @pytest.fixture
    def rules_by_org(self, dict_data):
        return {org["org_id"]: load_rules_from_org_dict(org) for org in dict_data["organizations"]}

    def test_all_regex_patterns_compile(self, dict_data):
        for org in dict_data["organizations"]:
            for rule in org["domain_rules"]:
                pattern = rule["pattern"]
                compiled = re.compile(pattern, re.IGNORECASE)
                assert compiled is not None, f"Regex lỗi ở org {org['org_id']}: {pattern}"

    def test_forms_office_com_classified_as_user_content_hosting(self, rules_by_org):
        """forms.office.com và forms.microsoft.com phải là user_content_hosting, không tự nhận first_party."""
        rules_ms = rules_by_org["microsoft"]
        assert domain_relation("https://forms.office.com/r/xyz123", rules_ms) == "unverified_shared_hosting"
        assert domain_relation("https://forms.microsoft.com/Pages/ResponsePage", rules_ms) == "unverified_shared_hosting"
        assert domain_relation("https://tenant.forms.office.com/form", rules_ms) == "unverified_shared_hosting"

    def test_amazon_s3_storage_endpoints_classified_as_user_content_hosting(self, rules_by_org):
        """Amazon S3 mọi dạng endpoint phải là user_content_hosting, không bị nuốt bởi amazonaws.com."""
        rules_amz = rules_by_org["amazon"]
        # Virtual hosted-style
        assert domain_relation("https://mybucket.s3.amazonaws.com/login.html", rules_amz) == "unverified_shared_hosting"
        # Path-style
        assert domain_relation("https://s3.amazonaws.com/mybucket/login.html", rules_amz) == "unverified_shared_hosting"
        # Regional virtual-hosted style
        assert domain_relation("https://mybucket.s3.us-east-1.amazonaws.com/login", rules_amz) == "unverified_shared_hosting"
        assert domain_relation("https://mybucket.s3-us-west-2.amazonaws.com/login", rules_amz) == "unverified_shared_hosting"

    def test_azure_and_google_storage_endpoints(self, rules_by_org):
        rules_ms = rules_by_org["microsoft"]
        assert domain_relation("https://evilaccount.blob.core.windows.net/web/login.html", rules_ms) == "unverified_shared_hosting"
        assert domain_relation("https://staticpage.web.core.windows.net/auth", rules_ms) == "unverified_shared_hosting"

        rules_gg = rules_by_org["google"]
        assert domain_relation("https://sites.google.com/view/evilphish", rules_gg) == "unverified_shared_hosting"
        assert domain_relation("https://docs.google.com/forms/d/e/1FAIpQLSc", rules_gg) == "unverified_shared_hosting"
        assert domain_relation("https://forms.google.com/", rules_gg) == "unverified_shared_hosting"
        assert domain_relation("https://storage.googleapis.com/phish-bucket/index.html", rules_gg) == "unverified_shared_hosting"
        assert domain_relation("https://myapp.firebaseapp.com/login", rules_gg) == "unverified_shared_hosting"
        assert domain_relation("https://myapp.web.app/login", rules_gg) == "unverified_shared_hosting"

    def test_rule_order_independence(self, rules_by_org):
        """Chứng minh đảo thứ tự quy tắc trong tuple/list không làm thay đổi kết quả (UGC luôn thắng)."""
        rules_amz = rules_by_org["amazon"]
        reversed_rules_amz = tuple(reversed(rules_amz))

        url_s3 = "https://bucket.s3.amazonaws.com/index.html"
        assert domain_relation(url_s3, rules_amz) == "unverified_shared_hosting"
        assert domain_relation(url_s3, reversed_rules_amz) == "unverified_shared_hosting"

        rules_ms = rules_by_org["microsoft"]
        reversed_rules_ms = tuple(reversed(rules_ms))
        url_forms = "https://forms.office.com/pages/view"
        assert domain_relation(url_forms, rules_ms) == "unverified_shared_hosting"
        assert domain_relation(url_forms, reversed_rules_ms) == "unverified_shared_hosting"

    def test_dns_boundary_and_spoofing_attempts(self, rules_by_org):
        """Đảm bảo các tên miền tấn công dạng substring, prefix, suffix đều trả về 'unverified'."""
        rules_ms = rules_by_org["microsoft"]
        assert domain_relation("https://attacker-microsoft.com/login", rules_ms) == "unverified"
        assert domain_relation("https://microsoft.com.attacker.net/login", rules_ms) == "unverified"
        assert domain_relation("https://portal-azure-security.com/", rules_ms) == "unverified"

        rules_gg = rules_by_org["google"]
        assert domain_relation("https://mygoogle.com/login", rules_gg) == "unverified"
        assert domain_relation("https://google.com.phishingsite.com/", rules_gg) == "unverified"
        assert domain_relation("https://fake-google-login.xyz/", rules_gg) == "unverified"

        rules_meta = rules_by_org["meta"]
        assert domain_relation("https://notfacebook.com/signin", rules_meta) == "unverified"
        assert domain_relation("https://instagram-verify.net/", rules_meta) == "unverified"

        rules_paypal = rules_by_org["paypal"]
        assert domain_relation("https://verify-paypal.com/account", rules_paypal) == "unverified"
        assert domain_relation("https://paypal.com.account-update.info/", rules_paypal) == "unverified"

    def test_legitimate_first_party_verification(self, rules_by_org):
        rules_ms = rules_by_org["microsoft"]
        assert domain_relation("https://login.microsoft.com/common/oauth2", rules_ms) == "verified_first_party"
        assert domain_relation("https://portal.azure.com/#home", rules_ms) == "verified_first_party"
        assert domain_relation("https://outlook.live.com/mail/", rules_ms) == "verified_first_party"

        rules_gg = rules_by_org["google"]
        assert domain_relation("https://accounts.google.com/signin", rules_gg) == "verified_first_party"
        assert domain_relation("https://mail.google.com/mail/u/0/", rules_gg) == "verified_first_party"

        rules_paypal = rules_by_org["paypal"]
        assert domain_relation("https://www.paypal.com/signin", rules_paypal) == "verified_first_party"


class TestHelperFunctionsAndKappa:
    """Kiểm tra hàm verify_sha256 và thuật toán Cohen's Kappa."""

    def test_verify_sha256_correct(self):
        import hashlib
        expected_hash = hashlib.sha256(DICT_PATH.read_bytes()).hexdigest()
        assert verify_sha256(str(DICT_PATH), expected_hash) is True

    def test_verify_sha256_wrong(self):
        wrong_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        assert verify_sha256(str(DICT_PATH), wrong_hash) is False

    def test_cohens_kappa_single_class_undefined(self):
        """Khi toàn bộ mẫu chỉ thuộc 1 category duy nhất, Pe=1.0 -> Kappa không xác định (0/0), không trả 1.0."""
        rater1 = ["phish"] * 20
        rater2 = ["phish"] * 20
        result = compute_cohens_kappa_from_labels(rater1, rater2)
        assert result.kappa is None
        assert result.status == "undefined_single_class"
        assert result.observed_agreement == 1.0
        assert result.expected_agreement == 1.0
        assert result.sample_count == 20

    def test_cohens_kappa_perfect_agreement_multiclass(self):
        rater1 = ["microsoft", "google", "meta", "apple"] * 5
        rater2 = ["microsoft", "google", "meta", "apple"] * 5
        result = compute_cohens_kappa_from_labels(rater1, rater2)
        assert result.status == "valid"
        assert result.kappa == 1.0
        assert result.observed_agreement == 1.0

    def test_cohens_kappa_partial_agreement(self):
        rater1 = ["A", "A", "A", "B", "B", "B", "C", "C", "C", "A"]
        rater2 = ["A", "A", "B", "B", "B", "A", "C", "C", "C", "A"]
        result = compute_cohens_kappa_from_labels(rater1, rater2)
        assert result.status == "valid"
        assert 0.0 < result.kappa < 1.0

    def test_cohens_kappa_difficult_cases_filtering(self):
        """Các ca khó (difficult_case=True) phải được loại bỏ khỏi mẫu tính Kappa."""
        rater1 = ["phish", "phish", "benign", "phish"]
        rater2 = ["phish", "phish", "benign", "benign"]  # Mẫu 4 là ca khó bất đồng
        is_difficult = [False, False, False, True]

        # Khi loại ca khó thứ 4, 3 mẫu còn lại đồng thuận 100%
        result = compute_cohens_kappa_from_labels(rater1, rater2, is_difficult=is_difficult, random_subset=[True, True, True, False])
        assert result.sample_count == 3
        assert result.observed_agreement == 1.0

        # Ca khó thứ 4 thuộc random thì phải được giữ, kể cả khi bất đồng.
        result = compute_cohens_kappa_from_labels(rater1, rater2, is_difficult=is_difficult, random_subset=[True] * 4)
        assert result.sample_count == 4
        assert result.observed_agreement == 0.75

    def test_cohens_kappa_length_mismatch(self):
        with pytest.raises(ValueError, match="cùng độ dài"):
            compute_cohens_kappa_from_labels(["A", "B"], ["A"])

    def test_cohens_kappa_missing_data(self):
        with pytest.raises(ValueError, match="Thiếu dữ liệu nhãn"):
            compute_cohens_kappa_from_labels(["A", None], ["A", "B"])
        with pytest.raises(ValueError, match="Thiếu dữ liệu nhãn"):
            compute_cohens_kappa_from_labels(["A", "  "], ["A", "B"])
