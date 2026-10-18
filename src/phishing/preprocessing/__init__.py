"""Metadata-free feature inputs shared by offline analysis and later serving."""

from dataclasses import dataclass
from typing import Literal

from .html import clean_html
from .urls import normalize_url

PREPROCESSING_VERSION = "snapshot-dev-0"
CaptureMode = Literal["url_only", "stored_html", "rendered_dom"]


@dataclass(frozen=True, slots=True)
class PreparedSnapshot:
    url: str
    html: str | None
    capture_mode: CaptureMode
    preprocessing_version: str = PREPROCESSING_VERSION


def prepare_snapshot(
    url: str, html: str | None = None, *, capture_mode: CaptureMode | None = None,
) -> PreparedSnapshot:
    """Only URL/HTML/capture mode are accepted; source labels are never inputs."""
    mode = capture_mode or ("url_only" if html is None else "stored_html")
    if mode not in {"url_only", "stored_html", "rendered_dom"}:
        raise ValueError("Unknown capture mode")
    if (mode == "url_only") != (html is None):
        raise ValueError("Capture mode and HTML presence must agree")
    normalized = normalize_url(url)
    cleaned = clean_html(html, normalized) if html is not None else None
    return PreparedSnapshot(normalized, cleaned, mode)
