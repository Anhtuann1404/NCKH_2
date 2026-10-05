"""Draft URL/DOM/text extraction. No model, labels, or corpus fitting here."""

from dataclasses import dataclass
from html.parser import HTMLParser
import ipaddress
from urllib.parse import parse_qsl, urlsplit

from phishing.preprocessing import PREPROCESSING_VERSION, PreparedSnapshot

FEATURE_VERSION = "features-dev-0"


@dataclass(frozen=True, slots=True)
class ExtractedFeatures:
    url: dict[str, int | float]
    dom: dict[str, int | float] | None
    text: str | None


class _DOMFeatures(HTMLParser):
    def __init__(self, hostname: str) -> None:
        super().__init__(convert_charrefs=True)
        self.hostname = hostname
        self.counts = dict.fromkeys((
            "element_count", "form_count", "input_count", "iframe_count", "image_count",
            "link_count", "same_host_link_count", "other_host_link_count",
        ), 0)
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.counts["element_count"] += 1
        counter = {"form": "form_count", "input": "input_count", "iframe": "iframe_count", "img": "image_count"}.get(tag)
        if counter:
            self.counts[counter] += 1
        if tag == "a":
            self.counts["link_count"] += 1
            href = dict(attrs).get("href")
            if href:
                target = urlsplit(href).hostname
                if target:
                    key = "same_host_link_count" if target == self.hostname else "other_host_link_count"
                    self.counts[key] += 1

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)


def extract(snapshot: PreparedSnapshot) -> ExtractedFeatures:
    """Extract only deterministic signals from an already prepared snapshot.

    capture_mode and preprocessing_version validate input, but are not features.
    same_host is intentionally not an eTLD+1 or ownership comparison.
    """
    if not isinstance(snapshot, PreparedSnapshot):
        raise TypeError("Feature input must be a PreparedSnapshot, not a dataset row")
    if snapshot.preprocessing_version != PREPROCESSING_VERSION:
        raise ValueError("Unsupported preprocessing version")
    parts = urlsplit(snapshot.url)
    host = parts.hostname or ""
    try:
        ipaddress.ip_address(host)
        is_ip = 1
    except ValueError:
        is_ip = 0
    url_features = {
        "url_length": len(snapshot.url),
        "hostname_length": len(host),
        "hostname_dot_count": host.count("."),
        "hostname_hyphen_count": host.count("-"),
        "hostname_is_ip": is_ip,
        "hostname_has_punycode": int(any(label.startswith("xn--") for label in host.split("."))),
        "is_https": int(parts.scheme == "https"),
        "path_length": len(parts.path),
        "path_segment_count": sum(bool(segment) for segment in parts.path.split("/")),
        "path_digit_count": sum(character.isdigit() for character in parts.path),
        "query_key_count": len(parse_qsl(parts.query, keep_blank_values=True)),
    }
    if snapshot.html is None:
        return ExtractedFeatures(url_features, None, None)
    parser = _DOMFeatures(host)
    parser.feed(snapshot.html)
    parser.close()
    text = " ".join(" ".join(parser.text_parts).split())
    return ExtractedFeatures(url_features, parser.counts, text)
