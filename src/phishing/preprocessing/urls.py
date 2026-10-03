"""Deterministic URL preparation, without DNS lookups or HTTP requests."""

import ipaddress
import re
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

MAX_URL_CHARACTERS = 8192
QUERY_VALUE_MARKER = "_redacted_"


def normalize_hostname(hostname: str) -> str:
    host = hostname.lower().rstrip(".")
    if not host:
        raise ValueError("URL must have a hostname")
    try:
        return str(ipaddress.ip_address(host))
    except ValueError:
        pass
    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError:
        raise ValueError("Invalid hostname") from None
    if len(host) > 253 or any(
        not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
        for label in host.split(".")
    ):
        raise ValueError("Invalid hostname")
    return host


def normalize_url(url: str) -> str:
    """Keep URL structure and query keys, but strip credentials and values.

    Paths and query names may still contain personal information. This is an
    analysis representation, not a complete privacy filter or WHATWG parser.
    """
    if not isinstance(url, str):
        raise TypeError("URL must be a string")
    if not url or len(url) > MAX_URL_CHARACTERS:
        raise ValueError("URL is empty or exceeds the character limit")
    if any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in url):
        raise ValueError("Whitespace/control characters are not allowed in URLs")
    if "\\" in url or re.search(r"%(?![0-9a-fA-F]{2})", url):
        raise ValueError("Invalid URL escaping")
    try:
        parts = urlsplit(url)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise ValueError("An absolute HTTP(S) URL is required")
        host = normalize_hostname(parts.hostname)
        port = parts.port
    except ValueError:
        raise ValueError("Invalid HTTP(S) URL") from None
    authority = f"[{host}]" if ":" in host else host
    if port is not None and (parts.scheme, port) not in {("http", 80), ("https", 443)}:
        authority += f":{port}"
    path = quote(parts.path or "/", safe="/:@!$&'()*+,;=-._~%")
    path = re.sub(r"%[0-9a-fA-F]{2}", lambda match: match[0].upper(), path)
    query = urlencode([
        (key, QUERY_VALUE_MARKER)
        for key, _ in parse_qsl(parts.query, keep_blank_values=True)
    ])
    result = urlunsplit((parts.scheme, authority, path, query, ""))
    if len(result) > MAX_URL_CHARACTERS:
        raise ValueError("Prepared URL exceeds the character limit")
    return result


def hostname_matches(hostname: str, reference: str, *, include_subdomains: bool = False) -> bool:
    """Match a hostname, never a brand substring, path, or query value."""
    host = normalize_hostname(hostname)
    reference = normalize_hostname(reference)
    if host == reference:
        return True
    try:
        ipaddress.ip_address(reference)
        return False
    except ValueError:
        return include_subdomains and host.endswith("." + reference)
