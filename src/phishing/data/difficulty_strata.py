"""Evaluation of surface structural indicators (descriptive profiling) without label peeking.

Strict ARS & Ponytail Discipline:
- Evaluates 6 predefined surface structural flags without looking at source labels.
- Uses safe HTML parsing and URL syntactic analysis only (Zero JavaScript, Zero network).
- IMPORTANT METHODOLOGICAL CLARIFICATION:
  These 6 flags are purely descriptive surface indicators (chỉ báo mô tả bề mặt quan sát),
  NOT phishing evidence (không phải bằng chứng tấn công) and NOT pre-selection sampling constraints.
  Sampling was conducted purely via source labels and pseudorandom seed; these flags provide
  post-hoc descriptive profiling of sample diversity.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Set, Tuple
from urllib.parse import urlparse

from phishing.annotation.blind_view import extract_safe_view_content
from phishing.data.grouping import extract_group_id

DIFFICULTY_RULES: Tuple[str, ...] = (
    "shared_hosting_or_ugc",
    "brand_in_subdomain_or_path",
    "login_credential_form",
    "external_action_or_links",
    "suspicious_url_syntax",
    "non_ascii_or_cjk",
)

# Known multi-tenant / user-generated content hosting platforms and free service providers
SHARED_HOSTING_PLATFORMS: Set[str] = frozenset({
    "github.io", "pages.dev", "workers.dev", "vercel.app", "netlify.app",
    "webflow.io", "blogspot.com", "azurewebsites.net", "appspot.com",
    "r.appspot.com", "sites.google.com", "firebaseapp.com", "wixsite.com",
    "weebly.com", "mystrikingly.com", "wordpress.com", "glitch.me",
    "surge.sh", "render.com", "fly.dev", "replit.dev", "web.app",
})

# Catalog 14 brand keywords from configs/dictionary_v1.json (lowercase tokens)
CATALOG_BRAND_TOKENS: Set[str] = frozenset({
    "microsoft", "msft", "office365", "onedrive", "sharepoint", "azure",
    "google", "gmail", "googledrive", "meta", "facebook", "fb",
    "apple", "icloud", "itunes", "amazon", "aws", "linkedin",
    "twitter", "x_twitter", "paypal", "adobe", "booking", "dhl",
    "spotify", "alibaba", "aliexpress", "mastercard",
})

# First-party base domains for catalog brands where brand token in subdomain is legitimate
FIRST_PARTY_BRAND_DOMAINS: Set[str] = frozenset({
    "microsoft.com", "office.com", "live.com", "azure.com",
    "google.com", "gmail.com", "youtube.com", "google.com.vn",
    "meta.com", "facebook.com", "fb.com", "instagram.com",
    "apple.com", "icloud.com",
    "amazon.com", "amazon.co.jp", "amazon.de", "aws.amazon.com",
    "linkedin.com",
    "twitter.com", "x.com",
    "paypal.com",
    "adobe.com",
    "booking.com",
    "dhl.com", "dhl.de",
    "spotify.com",
    "alibaba.com", "aliexpress.com",
    "mastercard.com", "mastercard.us",
})

IP_REGEX = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
CJK_REGEX = re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF]")


def evaluate_difficulty_flags(
    url: str,
    html: str | None = None,
    *,
    max_html_characters: int = 2_000_000,
) -> Dict[str, bool]:
    """Compute 6 surface difficulty flags without inspecting source labels or model scores.

    Returns dict of boolean flags for all DIFFICULTY_RULES.
    """
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    group_id = extract_group_id(url).lower()
    path_and_query = f"{parsed.path} {parsed.query}".lower()

    # Rule 1: shared_hosting_or_ugc
    is_shared = (
        group_id in SHARED_HOSTING_PLATFORMS
        or any(hostname.endswith("." + p) for p in SHARED_HOSTING_PLATFORMS)
        or any(hostname.endswith(tld) for tld in (".shop", ".top", ".xyz", ".online", ".site", ".club"))
    )

    # Rule 2: brand_in_subdomain_or_path
    # Token appears in host/path, but registered domain is not a known first-party domain
    brand_mentioned = False
    if not any(hostname == f or hostname.endswith("." + f) for f in FIRST_PARTY_BRAND_DOMAINS):
        for token in CATALOG_BRAND_TOKENS:
            if token in hostname or re.search(rf"\b{re.escape(token)}\b", path_and_query):
                brand_mentioned = True
                break

    # Parse DOM content safely
    safe_text, summary = extract_safe_view_content(html or "", url, max_html_characters=max_html_characters)

    # Rule 3: login_credential_form
    has_login_form = bool(
        summary.get("has_login_form")
        or summary.get("password_inputs", 0) > 0
        or (summary.get("inputs", 0) > 0 and any(kw in safe_text.lower() for kw in ("login", "sign in", "password", "đăng nhập", "mật khẩu")))
    )

    # Rule 4: external_action_or_links
    has_external_links = summary.get("external_links", 0) > 0

    # Rule 5: suspicious_url_syntax
    # IP address, @ symbol, >= 3 subdomains, or >= 2 hyphens in hostname
    subdomain_parts = [p for p in hostname.split(".") if p]
    is_ip = bool(IP_REGEX.match(hostname))
    has_at_symbol = "@" in url
    many_subdomains = len(subdomain_parts) >= 4  # e.g. a.b.c.example.com
    many_hyphens = hostname.count("-") >= 2
    suspicious_syntax = is_ip or has_at_symbol or many_subdomains or many_hyphens

    # Rule 6: non_ascii_or_cjk
    has_cjk = bool(CJK_REGEX.search(safe_text) or CJK_REGEX.search(url))
    has_non_ascii = any(ord(c) > 127 for c in safe_text) or any(ord(c) > 127 for c in url)
    non_ascii_cjk = has_cjk or has_non_ascii

    return {
        "shared_hosting_or_ugc": bool(is_shared),
        "brand_in_subdomain_or_path": bool(brand_mentioned),
        "login_credential_form": bool(has_login_form),
        "external_action_or_links": bool(has_external_links),
        "suspicious_url_syntax": bool(suspicious_syntax),
        "non_ascii_or_cjk": bool(non_ascii_cjk),
    }


def is_hard_case(flags: Dict[str, bool]) -> bool:
    """Return True if at least one surface flag is triggered.

    NOTE ON SENSITIVITY: Because any() is a broad disjunction, in real-world web corpora
    it flags ~96% of samples (23/24 calibration samples) due to common traits like
    external links or non-ASCII characters. It serves as a broad surface sensitivity flag,
    not a proof of cognitive hardness.
    """
    return any(flags.get(r, False) for r in DIFFICULTY_RULES)


def is_composite_ambiguous_case(flags: Dict[str, bool], min_flags: int = 2) -> bool:
    """Return True if at least min_flags surface indicators co-occur.

    Provides a more selective composite measure of structural ambiguity.
    """
    return sum(1 for r in DIFFICULTY_RULES if flags.get(r, False)) >= min_flags

