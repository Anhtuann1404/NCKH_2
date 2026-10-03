"""Conservative domain-rule primitives; no production brand dictionary yet."""

from dataclasses import dataclass
from typing import Literal
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

    def __post_init__(self) -> None:
        normalize_hostname(self.hostname)
        if not isinstance(self.include_subdomains, bool):
            raise ValueError("Subdomain permission must be a boolean")
        if self.role not in {"first_party_identity", "first_party_content", "user_content_hosting", "authorized_service", "unverified"}:
            raise ValueError("Unknown domain role")
        if self.path_prefix is not None and (
            not self.path_prefix.startswith("/") or any(character in self.path_prefix for character in "%?#\\")
        ):
            raise ValueError("Path prefix must be an unescaped absolute path")


def domain_relation(url: str, rules: tuple[DomainRule, ...]) -> DomainRelation:
    """An observed relation is not a benign verdict or an allowlist decision.

    Shared hosting overrides broader provider matches, in any rule order.
    Path-limited verification conservatively rejects ambiguous encoded/dot paths.
    """
    parts = urlsplit(normalize_url(url))
    matched: list[DomainRole] = []
    ambiguous_scope = False
    for rule in rules:
        if not hostname_matches(parts.hostname or "", rule.hostname, include_subdomains=rule.include_subdomains):
            continue
        if rule.path_prefix is not None:
            if "%" in parts.path or any(segment in {".", ".."} for segment in parts.path.split("/")):
                ambiguous_scope = True
                continue
            prefix = rule.path_prefix.rstrip("/")
            if parts.path != prefix and not parts.path.startswith(prefix + "/"):
                continue
        matched.append(rule.role)
    if "user_content_hosting" in matched:
        return "unverified_shared_hosting"
    if ambiguous_scope or "unverified" in matched:
        return "unverified"
    if {"first_party_identity", "first_party_content"}.intersection(matched):
        return "verified_first_party"
    if "authorized_service" in matched:
        return "verified_authorized"
    return "unverified"
