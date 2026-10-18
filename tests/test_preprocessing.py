from dataclasses import replace
from pathlib import Path
import unittest
from unittest.mock import patch

from phishing.features import extract
from phishing.preprocessing import prepare_snapshot
from phishing.preprocessing.html import MAX_HTML_CHARACTERS
from phishing.preprocessing.urls import normalize_url

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_login.html"
PAGE_URL = "https://org.fixture.test/login?ticket=SECRET_TICKET#SECRET_FRAGMENT"


class URLPreparationTests(unittest.TestCase):
    def test_removes_credentials_values_and_fragment_preserving_repeated_keys(self):
        result = normalize_url("HTTPS://alice:secret@Org.Fixture.test:443/login?a=one&a=two&blank=#private")
        self.assertEqual(result, "https://org.fixture.test/login?a=_redacted_&a=_redacted_&blank=_redacted_")
        self.assertEqual(normalize_url(result), result)

    def test_ipv6_idna_and_nondefault_port(self):
        self.assertEqual(normalize_url("https://[2001:db8::1]:8443/"), "https://[2001:db8::1]:8443/")
        self.assertEqual(normalize_url("https://bücher.test/"), "https://xn--bcher-kva.test/")
        self.assertEqual(normalize_url("https://org.fixture.test./"), "https://org.fixture.test/")

    def test_rejects_ambiguous_or_non_http_urls(self):
        for url in (
            "file:///tmp/page.html", "javascript:alert(1)", "//org.fixture.test/", "https:///login",
            "https://org.fixture.test:99999/", "https://org.fixture.test/%ZZ",
            "https://org.fixture.test/\nlogin", "https://org.fixture.test\\@evil.test/",
            "https://bad_host.test/", "https://org.fixture.test/" + "x" * 8192,
        ):
            with self.subTest(url=url[:80]), self.assertRaises(ValueError):
                normalize_url(url)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.html = FIXTURE.read_text(encoding="utf-8")

    def test_removes_prefilled_content_and_active_attributes(self):
        snapshot = prepare_snapshot(PAGE_URL, self.html)
        self.assertNotIn("SECRET_", snapshot.html)
        self.assertNotIn("SECRET_", snapshot.url)
        for removed in ("<script", "<style", "onload=", "onclick=", "srcdoc=", "value="):
            self.assertNotIn(removed, snapshot.html)
        self.assertIn('<input name="password" type="password">', snapshot.html)
        self.assertIn("token=_redacted_", snapshot.html)
        self.assertIn("Fixture Organization", snapshot.html)
        replay = prepare_snapshot(snapshot.url, snapshot.html, capture_mode="rendered_dom")
        self.assertEqual(snapshot.html, replay.html)
        self.assertEqual(extract(snapshot), extract(replay))

    def test_features_do_not_depend_on_sensitive_field_values(self):
        original = extract(prepare_snapshot(PAGE_URL, self.html))
        changed = extract(prepare_snapshot(PAGE_URL.replace("SECRET_TICKET", "different"), self.html.replace("SECRET_", "DIFFERENT_")))
        self.assertEqual(original, changed)
        self.assertEqual(original.dom["form_count"], 1)
        self.assertEqual(original.dom["input_count"], 2)
        self.assertEqual(original.dom["iframe_count"], 1)
        self.assertEqual(original.dom["same_host_link_count"], 1)
        self.assertEqual(original.dom["other_host_link_count"], 1)
        self.assertNotIn("script_count", original.dom)
        self.assertNotIn("capture_mode", original.url)

    def test_no_network_or_process_execution_when_parsing_source_html(self):
        with (
            patch("socket.socket", side_effect=AssertionError("Network access attempted")),
            patch("urllib.request.urlopen", side_effect=AssertionError("HTTP fetch attempted")),
            patch("subprocess.Popen", side_effect=AssertionError("Process execution attempted")),
        ):
            features = extract(prepare_snapshot(PAGE_URL, self.html))
            self.assertIn("SYNTHETIC TEST PAGE", features.text)

    def test_dataset_metadata_cannot_enter_feature_input(self):
        for metadata in ("label", "target", "date", "tier", "sha256", "split", "group"):
            with self.subTest(metadata=metadata), self.assertRaises(TypeError):
                prepare_snapshot(PAGE_URL, self.html, **{metadata: "private"})
        with self.assertRaises(TypeError):
            extract({"url": PAGE_URL, "html": self.html, "label": 1})

    def test_url_only_and_empty_content_remain_distinguishable(self):
        url_only = extract(prepare_snapshot(PAGE_URL))
        empty = extract(prepare_snapshot(PAGE_URL, ""))
        self.assertIsNone(url_only.dom)
        self.assertIsNone(url_only.text)
        self.assertEqual(empty.dom["element_count"], 0)
        self.assertEqual(empty.text, "")

    def test_rejects_incompatible_modes_versions_and_oversize_html(self):
        for html, mode in ((None, "stored_html"), ("<p>x</p>", "url_only"), (None, "unknown")):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                prepare_snapshot(PAGE_URL, html, capture_mode=mode)
        with self.assertRaises(ValueError):
            prepare_snapshot(PAGE_URL, "x" * (MAX_HTML_CHARACTERS + 1))
        with self.assertRaises(ValueError):
            extract(replace(prepare_snapshot(PAGE_URL), preprocessing_version="other-version"))

    def test_nested_editable_hidden_and_malformed_html(self):
        html = '<div contenteditable><p>SECRET_A<span>SECRET_B</span></p></div><p aria-hidden="true">SECRET_C</p><p>Visible &amp; public'
        snapshot = prepare_snapshot(PAGE_URL, html)
        self.assertNotIn("SECRET_", snapshot.html)
        self.assertIn("Visible & public", extract(snapshot).text)
        self.assertEqual(prepare_snapshot(snapshot.url, snapshot.html).html, snapshot.html)

    def test_url_attributes_keep_structure_but_remove_values(self):
        html = '<a href="javascript:alert(1)">Bad</a><iframe srcdoc="SECRET"></iframe><a href="../help?otp=SECRET#private">Help</a>'
        snapshot = prepare_snapshot(PAGE_URL, html)
        self.assertNotIn("javascript:", snapshot.html)
        self.assertNotIn("SECRET", snapshot.html)
        self.assertNotIn("srcdoc", snapshot.html)
        self.assertIn("https://org.fixture.test/help?otp=_redacted_", snapshot.html)


if __name__ == "__main__":
    unittest.main()
