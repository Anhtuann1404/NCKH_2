"""Unit tests for the 6 surface hard-case flags (difficulty stratification)."""

from __future__ import annotations

import pytest

from phishing.data.difficulty_strata import (
    DIFFICULTY_RULES,
    evaluate_difficulty_flags,
    is_hard_case,
)


def test_difficulty_rules_has_six_flags():
    assert len(DIFFICULTY_RULES) == 6
    assert "shared_hosting_or_ugc" in DIFFICULTY_RULES
    assert "brand_in_subdomain_or_path" in DIFFICULTY_RULES
    assert "login_credential_form" in DIFFICULTY_RULES
    assert "external_action_or_links" in DIFFICULTY_RULES
    assert "suspicious_url_syntax" in DIFFICULTY_RULES
    assert "non_ascii_or_cjk" in DIFFICULTY_RULES


def test_rule_shared_hosting_or_ugc():
    ugc_url = "https://phish-site.pages.dev/login"
    flags = evaluate_difficulty_flags(ugc_url, "<html><body>Hello</body></html>")
    assert flags["shared_hosting_or_ugc"] is True

    shop_url = "https://aheadmusic.shop/"
    flags_shop = evaluate_difficulty_flags(shop_url, "<html><body>Hello</body></html>")
    assert flags_shop["shared_hosting_or_ugc"] is True

    regular_url = "https://example.com/"
    flags_reg = evaluate_difficulty_flags(regular_url, "<html><body>Hello</body></html>")
    assert flags_reg["shared_hosting_or_ugc"] is False


def test_rule_brand_in_subdomain_or_path():
    # Brand token in subdomain on non-brand domain
    lure_url = "https://paypal-security.support-center.org/login"
    flags = evaluate_difficulty_flags(lure_url, "<html><body>Verify identity</body></html>")
    assert flags["brand_in_subdomain_or_path"] is True

    # Brand token on first-party official domain is not flagged
    official_url = "https://www.paypal.com/signin"
    flags_off = evaluate_difficulty_flags(official_url, "<html><body>Sign in</body></html>")
    assert flags_off["brand_in_subdomain_or_path"] is False


def test_rule_login_credential_form():
    html_with_login = """
    <html><body>
    <form action="/auth" method="post">
      <input type="text" name="username">
      <input type="password" name="pwd">
      <button type="submit">Log in</button>
    </form>
    </body></html>
    """
    flags = evaluate_difficulty_flags("https://example.com/login", html_with_login)
    assert flags["login_credential_form"] is True

    html_plain = "<html><body><h1>News Article</h1><p>No forms here.</p></body></html>"
    flags_plain = evaluate_difficulty_flags("https://example.com/news", html_plain)
    assert flags_plain["login_credential_form"] is False


def test_rule_external_action_or_links():
    html_with_ext = '<html><body><a href="https://external-domain.org/help">Help</a></body></html>'
    flags = evaluate_difficulty_flags("https://example.com/home", html_with_ext)
    assert flags["external_action_or_links"] is True

    html_internal = '<html><body><a href="/about">About</a></body></html>'
    flags_int = evaluate_difficulty_flags("https://example.com/home", html_internal)
    assert flags_int["external_action_or_links"] is False


def test_rule_suspicious_url_syntax():
    ip_url = "http://192.168.1.100/secure"
    assert evaluate_difficulty_flags(ip_url, "<html></html>")["suspicious_url_syntax"] is True

    at_url = "https://legit.com@phish.net/login"
    assert evaluate_difficulty_flags(at_url, "<html></html>")["suspicious_url_syntax"] is True

    hyphens_url = "https://my-super-secure-login.com/"
    assert evaluate_difficulty_flags(hyphens_url, "<html></html>")["suspicious_url_syntax"] is True

    many_sub_url = "https://a.b.c.d.example.com/"
    assert evaluate_difficulty_flags(many_sub_url, "<html></html>")["suspicious_url_syntax"] is True

    clean_url = "https://www.example.com/"
    assert evaluate_difficulty_flags(clean_url, "<html></html>")["suspicious_url_syntax"] is False


def test_rule_non_ascii_or_cjk():
    ja_html = "<html><body>こんにちは。ログインしてください。</body></html>"
    flags_ja = evaluate_difficulty_flags("https://example.com/", ja_html)
    assert flags_ja["non_ascii_or_cjk"] is True

    ascii_html = "<html><body>Standard English news text.</body></html>"
    flags_en = evaluate_difficulty_flags("https://example.com/", ascii_html)
    assert flags_en["non_ascii_or_cjk"] is False


def test_is_hard_case():
    all_false = {r: False for r in DIFFICULTY_RULES}
    assert is_hard_case(all_false) is False

    one_true = dict(all_false)
    one_true["login_credential_form"] = True
    assert is_hard_case(one_true) is True


def test_is_composite_ambiguous_case():
    from phishing.data.difficulty_strata import (
        count_surface_cooccurrences,
        has_cooccurring_surface_indicators,
        is_composite_ambiguous_case,
    )

    all_false = {r: False for r in DIFFICULTY_RULES}
    assert count_surface_cooccurrences(all_false) == 0
    assert has_cooccurring_surface_indicators(all_false, min_indicators=2) is False
    assert is_composite_ambiguous_case(all_false, min_flags=2) is False

    one_true = dict(all_false)
    one_true["login_credential_form"] = True
    assert count_surface_cooccurrences(one_true) == 1
    assert has_cooccurring_surface_indicators(one_true, min_indicators=2) is False
    assert is_composite_ambiguous_case(one_true, min_flags=2) is False

    two_true = dict(one_true)
    two_true["external_action_or_links"] = True
    assert count_surface_cooccurrences(two_true) == 2
    assert has_cooccurring_surface_indicators(two_true, min_indicators=2) is True
    assert is_composite_ambiguous_case(two_true, min_flags=2) is True


