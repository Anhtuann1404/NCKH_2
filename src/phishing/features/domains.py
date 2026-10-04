"""Conservative domain-rule primitives and organization matching.

Academic Research Skills (ARS) Principles:
1. An observed relation is an empirical feature observation, NOT a benign verdict or safelist.
2. User Content Hosting (UGC) ALWAYS takes precedence over broader first-party rules, in ANY rule order.
3. Path-limited verification conservatively rejects ambiguous encoded/dot paths.
4. Hostname matching enforces strict DNS boundary checks.
"""

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Literal, Sequence, Tuple
from urllib.parse import urlsplit

from phishing.preprocessing.urls import hostname_matches, normalize_hostname, normalize_url

DomainRole = Literal["first_party_identity", "first_party_content", "user_content_hosting", "authorized_service", "unverified"]
DomainRelation = Literal["verified_first_party", "verified_authorized", "unverified_shared_hosting", "unverified"]


@dataclass(frozen=True, slots=True)
class DomainRule:
    hostname: str
    role: DomainRole
    include_subdomains: bool = False
    path_prefix: str | None = None
    pattern: str | None = None

    def __post_init__(self) -> None:
        if self.pattern is not None:
            try:
                re.compile(self.pattern, re.IGNORECASE)
            except re.error as err:
                raise ValueError(f"Invalid regex pattern: {err}") from err
        if self.hostname:
            normalize_hostname(self.hostname)
        if not isinstance(self.include_subdomains, bool):
            raise ValueError("Subdomain permission must be a boolean")
        if self.role not in {"first_party_identity", "first_party_content", "user_content_hosting", "authorized_service", "unverified"}:
            raise ValueError("Unknown domain role")
        if self.path_prefix is not None and (
            not self.path_prefix.startswith("/") or any(character in self.path_prefix for character in "%?#\\")
        ):
            raise ValueError("Path prefix must be an unescaped absolute path")


def domain_relation(url: str, rules: Sequence[DomainRule]) -> DomainRelation:
    """An observed relation is not a benign verdict or an allowlist decision.

    Shared hosting (user_content_hosting) overrides broader provider matches, in any rule order.
    Path-limited verification conservatively rejects ambiguous encoded/dot paths.
    """
    parts = urlsplit(normalize_url(url))
    host = parts.hostname or ""
    matched: list[DomainRole] = []
    ambiguous_scope = False

    for rule in rules:
        matched_host = False
        if rule.pattern is not None:
            matched_host = bool(re.search(rule.pattern, host, re.IGNORECASE))
        elif rule.hostname:
            matched_host = hostname_matches(host, rule.hostname, include_subdomains=rule.include_subdomains)

        if not matched_host:
            continue

        if rule.path_prefix is not None:
            if "%" in parts.path or any(segment in {".", ".."} for segment in parts.path.split("/")):
                ambiguous_scope = True
                continue
            prefix = rule.path_prefix.rstrip("/")
            if parts.path != prefix and not parts.path.startswith(prefix + "/"):
                continue

        matched.append(rule.role)

    # 1. UGC / Shared hosting takes absolute precedence regardless of evaluation order
    if "user_content_hosting" in matched:
        return "unverified_shared_hosting"

    # 2. Ambiguous path or explicit unverified role
    if ambiguous_scope or "unverified" in matched:
        return "unverified"

    # 3. Verified first party identity or content
    if {"first_party_identity", "first_party_content"}.intersection(matched):
        return "verified_first_party"

    # 4. Verified authorized service
    if "authorized_service" in matched:
        return "verified_authorized"

    return "unverified"


def load_rules_from_org_dict(org_dict: Dict[str, Any]) -> Tuple[DomainRule, ...]:
    """Chuyển đổi các quy tắc domain_rules trong từ điển JSON sang tuple DomainRule dùng chung."""
    rules: List[DomainRule] = []
    for r in org_dict.get("domain_rules", []):
        pattern = r.get("pattern")
        hostname = r.get("hostname", "placeholder.invalid") if pattern else r.get("hostname", "")
        role = r.get("role", "unverified")
        include_subdomains = r.get("include_subdomains", False)
        path_prefix = r.get("path_prefix")
        rules.append(
            DomainRule(
                hostname=hostname,
                role=role,
                include_subdomains=include_subdomains,
                path_prefix=path_prefix,
                pattern=pattern,
            )
        )
    return tuple(rules)
