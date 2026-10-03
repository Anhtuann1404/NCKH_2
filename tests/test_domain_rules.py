import unittest

from phishing.features.domains import DomainRule, domain_relation
from phishing.preprocessing.urls import hostname_matches


class DomainRuleTests(unittest.TestCase):
    def test_dns_boundary_and_subdomains_require_explicit_permission(self):
        self.assertTrue(hostname_matches("org.fixture.test", "org.fixture.test"))
        self.assertFalse(hostname_matches("login.org.fixture.test", "org.fixture.test"))
        self.assertTrue(hostname_matches("login.org.fixture.test", "org.fixture.test", include_subdomains=True))
        for host in ("org.fixture.test.evil.test", "evil-org.fixture.test", "orgfixture.test"):
            with self.subTest(host=host):
                self.assertFalse(hostname_matches(host, "org.fixture.test", include_subdomains=True))

    def test_brand_in_path_query_or_userinfo_does_not_verify_hostname(self):
        rules = (DomainRule("org.fixture.test", "first_party_identity"),)
        for url in (
            "https://evil.test/org.fixture.test/login",
            "https://evil.test/?brand=org.fixture.test",
            "https://org.fixture.test@evil.test/",
            "https://org.fixture.test.evil.test/",
        ):
            with self.subTest(url=url):
                self.assertEqual(domain_relation(url, rules), "unverified")

    def test_shared_hosting_overrides_provider_in_both_rule_orders(self):
        provider = DomainRule("fixture.test", "first_party_content", include_subdomains=True)
        hosting = DomainRule("pages.fixture.test", "user_content_hosting", include_subdomains=True)
        for rules in ((provider, hosting), (hosting, provider)):
            self.assertEqual(domain_relation("https://customer.pages.fixture.test/org/login", rules), "unverified_shared_hosting")
        # A relation is an observation; this module never produces a verdict.
        self.assertEqual(domain_relation("https://fixture.test/", (provider,)), "verified_first_party")

    def test_path_rules_use_segment_boundaries_and_reject_ambiguous_paths(self):
        rules = (DomainRule("auth.fixture.test", "first_party_identity", path_prefix="/login"),)
        self.assertEqual(domain_relation("https://auth.fixture.test/login/flow", rules), "verified_first_party")
        for path in ("/login-fake", "/other", "/login/%2E%2E/tenant", "/login/../tenant", "/login%2Ftenant"):
            with self.subTest(path=path):
                self.assertEqual(domain_relation("https://auth.fixture.test" + path, rules), "unverified")

    def test_authorized_service_and_unknown_have_distinct_relations(self):
        rules = (DomainRule("sso.fixture.test", "authorized_service"),)
        self.assertEqual(domain_relation("https://sso.fixture.test/", rules), "verified_authorized")
        self.assertEqual(domain_relation("https://unknown.test/", rules), "unverified")
        with self.assertRaises(ValueError):
            DomainRule("fixture.test", "benign")
        with self.assertRaises(ValueError):
            DomainRule("fixture.test", "first_party_identity", path_prefix="login")
        with self.assertRaises(ValueError):
            DomainRule("fixture.test", "first_party_identity", include_subdomains="false")

    def test_ambiguous_path_cannot_fall_back_to_broad_provider_verification(self):
        rules = (
            DomainRule("fixture.test", "first_party_content"),
            DomainRule("fixture.test", "user_content_hosting", path_prefix="/pages"),
        )
        self.assertEqual(domain_relation("https://fixture.test/pages/customer", rules), "unverified_shared_hosting")
        self.assertEqual(domain_relation("https://fixture.test/pages/%63ustomer", rules), "unverified")


if __name__ == "__main__":
    unittest.main()
