"""Prepare stored HTML for analysis; do not render this output in a browser."""

from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
from urllib.parse import urljoin

from .urls import normalize_url

MAX_HTML_CHARACTERS = 1_000_000
_VOID = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"})
_DROP_SUBTREE = frozenset({"script", "style", "template", "noscript", "object", "embed"})
_KEEP_ATTRIBUTES = frozenset({
    "href", "src", "action", "formaction", "type", "name", "method", "autocomplete",
    "placeholder", "aria-label", "aria-hidden", "title", "alt", "hidden", "contenteditable",
})
_URL_ATTRIBUTES = frozenset({"href", "src", "action", "formaction"})


@dataclass(frozen=True, slots=True)
class _Frame:
    tag: str
    drop: bool
    suppress_text: bool


class _SnapshotParser(HTMLParser):
    def __init__(self, page_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.output: list[str] = []
        self.stack: list[_Frame] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # Keep the first duplicate attribute, consistent with normal HTML DOMs.
        attributes: dict[str, str | None] = {}
        for key, value in attrs:
            attributes.setdefault(key, value)
        parent = self.stack[-1] if self.stack else None
        drop = bool(parent and parent.drop) or tag in _DROP_SUBTREE or tag == "base"
        editable = "contenteditable" in attributes and (attributes["contenteditable"] or "").lower() != "false"
        suppress = bool(parent and parent.suppress_text) or drop or editable or tag == "textarea"
        suppress = suppress or "hidden" in attributes or (attributes.get("aria-hidden") or "").lower() == "true"
        if not drop:
            cleaned: list[str] = []
            for key, value in sorted(attributes.items()):
                if key not in _KEEP_ATTRIBUTES:
                    continue
                if key in _URL_ATTRIBUTES:
                    try:
                        value = normalize_url(urljoin(self.page_url, value or ""))
                    except (ValueError, TypeError):
                        continue
                cleaned.append(key if value is None else f'{key}="{escape(value, quote=True)}"')
            suffix = " " + " ".join(cleaned) if cleaned else ""
            self.output.append(f"<{tag}{suffix}>")
        if tag not in _VOID:
            self.stack.append(_Frame(tag, drop, suppress))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index].tag == tag:
                for frame in reversed(self.stack[index:]):
                    if not frame.drop:
                        self.output.append(f"</{frame.tag}>")
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if not self.stack or not self.stack[-1].suppress_text:
            self.output.append(escape(data, quote=False))

    def finish(self) -> str:
        self.close()
        for frame in reversed(self.stack):
            if not frame.drop:
                self.output.append(f"</{frame.tag}>")
        return "".join(self.output)


def clean_html(html: str, page_url: str) -> str:
    """Drop scripts, event handlers and prefilled values; retain DOM structure.

    URL attributes are resolved against the page URL, with query values removed.
    The v0 draft ignores <base>, CSS visibility and browser tree-repair rules.
    Never use its output as an XSS-safe preview or a fully anonymized document.
    """
    if not isinstance(html, str):
        raise TypeError("HTML must be a string")
    if len(html) > MAX_HTML_CHARACTERS:
        raise ValueError("HTML exceeds the character limit; truncation is not allowed")
    parser = _SnapshotParser(normalize_url(page_url))
    parser.feed(html)
    return parser.finish()
