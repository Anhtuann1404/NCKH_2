import json
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from phishing.preprocessing import PREPROCESSING_VERSION
from phishing.serving.mock_api import create_app, MockSettings

TOKEN = 'synthetic-fixture-token-never-use-in-production'
EXTENSION_ID = 'a' * 32
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Origin': f'chrome-extension://{EXTENSION_ID}'}
ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads((ROOT / 'docs/openapi.json').read_text())


def payload(content=True):
    request = {
        'request_id': '11111111-1111-4111-8111-111111111111',
        'navigation_id': '22222222-2222-4222-8222-222222222222',
        'dom_revision': 1, 'phase': 'url_content' if content else 'url_only',
        'url': 'https://org.fixture.test/login', 'preprocessing_version': PREPROCESSING_VERSION,
        'capture_mode': 'stored_html' if content else 'url_only',
    }
    if content:
        request['html'] = '<h1>SYNTHETIC TEST PAGE</h1><form><input type="password" value="SECRET"></form>'
    return request


def client(**options):
    return TestClient(create_app(MockSettings(TOKEN, EXTENSION_ID, **options)), base_url='http://127.0.0.1:8765', raise_server_exceptions=False)


class MockAPITests(unittest.TestCase):
    def assert_schema(self, name, body):
        Draft202012Validator({'$ref': f'#/components/schemas/{name}', 'components': SPEC['components']}, format_checker=FormatChecker()).validate(body)

    def test_health_never_claims_real_model_ready(self):
        with client() as api:
            result = api.get('/health')
            self.assertEqual(result.status_code, 200)
            self.assertFalse(result.json()['model_ready'])
            self.assert_schema('HealthResponse', result.json())

    def test_mock_results_match_contract_in_both_phases_and_all_scenarios(self):
        for scenario in ('warning', 'no_indication', 'insufficient_content'):
            for content in (False, True):
                with self.subTest(scenario=scenario, content=content), client(scenario=scenario) as api:
                    result = api.post('/v1/analyze', headers=HEADERS, json=payload(content))
                    self.assertEqual(result.status_code, 200)
                    body = result.json()
                    self.assert_schema('AnalyzeResponse', body)
                    self.assertTrue(body['model']['model_id'].startswith('mock-only-'))
                    self.assertIn('mock_response_not_model_result', body['limitations'])
                    self.assertEqual(body['verdict'], 'unable_to_assess' if scenario == 'insufficient_content' else scenario)
                    self.assertNotIn('SECRET', result.text)

    def test_metadata_is_explicitly_synthetic(self):
        with client() as api:
            result = api.get('/v1/model', headers=HEADERS)
            self.assert_schema('ActiveBundle', result.json())
            self.assertEqual(result.json()['bundle_id'], 'mock-only-synthetic')

    def test_token_host_and_origin_are_enforced(self):
        with client() as api:
            cases = (
                ({}, 401), ({'Authorization': 'Bearer invalid'}, 401),
                ({**HEADERS, 'Origin': 'https://untrusted.test'}, 403),
                ({**HEADERS, 'Host': 'untrusted.test'}, 403),
                ({**HEADERS, 'Origin': 'chrome-extension://' + 'b' * 32}, 403),
            )
            for headers, status in cases:
                with self.subTest(status=status, headers=list(headers)):
                    result = api.post('/v1/analyze', headers=headers, json=payload())
                    self.assertEqual(result.status_code, status)
                    self.assert_schema('ErrorResponse', result.json())

    def test_isolated_port_enforces_its_own_host_boundary(self):
        app = create_app(MockSettings(TOKEN, EXTENSION_ID, port=18765))
        with TestClient(app, base_url='http://127.0.0.1:18765') as api:
            self.assertEqual(api.post('/v1/analyze', headers=HEADERS, json=payload()).status_code, 200)
            self.assertEqual(api.post('/v1/analyze', headers={**HEADERS, 'Host': '127.0.0.1:8765'}, json=payload()).status_code, 403)

    def test_preflight_only_grants_configured_extension(self):
        with client() as api:
            result = api.options('/v1/analyze', headers={'Origin': HEADERS['Origin'], 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'authorization,content-type'})
            self.assertEqual(result.status_code, 204)
            self.assertEqual(result.headers['access-control-allow-origin'], HEADERS['Origin'])
            blocked = api.options('/v1/analyze', headers={'Origin': 'https://bad.test', 'Access-Control-Request-Method': 'POST'})
            self.assertEqual(blocked.status_code, 403)
            self.assertNotIn('access-control-allow-origin', blocked.headers)

    def test_metadata_fields_invalid_urls_and_uuid_are_rejected(self):
        with client() as api:
            for field in ('label', 'target', 'tier', 'score', 'date'):
                request = {**payload(), field: 'SECRET_METADATA'}
                result = api.post('/v1/analyze', headers=HEADERS, json=request)
                self.assertEqual(result.status_code, 422)
                self.assertNotIn('SECRET_METADATA', result.text)
            for key, value in (('request_id', 'invalid'), ('dom_revision', True), ('dom_revision', -1), ('url', 'file:///tmp/private'), ('url', 'https://bad_host.test/')):
                result = api.post('/v1/analyze', headers=HEADERS, json={**payload(), key: value})
                self.assertEqual(result.status_code, 422)

    def test_version_mismatch_and_missing_content(self):
        with client() as api:
            result = api.post('/v1/analyze', headers=HEADERS, json={**payload(), 'preprocessing_version': 'snapshot-v1'})
            self.assertEqual(result.status_code, 409)
            missing = payload(); del missing['html']
            self.assertEqual(api.post('/v1/analyze', headers=HEADERS, json=missing).status_code, 422)
            result = api.post('/v1/analyze', headers=HEADERS, json={**payload(), 'html': '<script>SECRET</script>'})
            self.assertEqual(result.json()['verdict'], 'unable_to_assess')
            self.assertIsNone(result.json()['score'])

    def test_body_limits_before_parse_for_content_length_and_stream(self):
        with client(max_body_bytes=128) as api:
            result = api.post('/v1/analyze', headers=HEADERS, json=payload())
            self.assertEqual(result.status_code, 413)
            chunks = (b'x' * 80 for _ in range(3))
            result = api.post('/v1/analyze', headers={**HEADERS, 'Content-Type': 'application/json'}, content=chunks)
            self.assertEqual(result.status_code, 413)
        with client() as api:
            result = api.post('/v1/analyze', headers=HEADERS, content='private text')
            self.assertEqual(result.status_code, 415)
            result = api.post('/v1/analyze', headers={**HEADERS, 'Content-Type': 'application/json'}, content='{SECRET invalid json}')
            self.assertEqual(result.status_code, 422)
            self.assertNotIn('SECRET', result.text)

    def test_mock_api_does_not_fetch_or_execute_html(self):
        with client() as api, patch('urllib.request.urlopen', side_effect=AssertionError('fetch')), patch('subprocess.Popen', side_effect=AssertionError('exec')):
            result = api.post('/v1/analyze', headers=HEADERS, json=payload())
            self.assertEqual(result.status_code, 200)

    def test_unavailable_timeout_and_rate_limit(self):
        with client(scenario='unavailable') as api:
            self.assertEqual(api.get('/health').status_code, 200)
            self.assertEqual(api.get('/v1/model', headers=HEADERS).status_code, 503)
            self.assertEqual(api.post('/v1/analyze', headers=HEADERS, json=payload()).status_code, 503)
        with client(delay_ms=50, processing_timeout_seconds=0.01) as api:
            self.assertEqual(api.post('/v1/analyze', headers=HEADERS, json=payload()).status_code, 504)
        with client(requests_per_minute=1) as api:
            api.get('/v1/model', headers=HEADERS)
            self.assertEqual(api.post('/v1/analyze', headers=HEADERS, json=payload()).status_code, 429)

    def test_internal_error_does_not_echo_exception_or_input(self):
        with client() as api, patch('phishing.serving.mock_api.extract', side_effect=RuntimeError('SECRET_EXCEPTION')):
            result = api.post('/v1/analyze', headers=HEADERS, json=payload())
            self.assertEqual(result.status_code, 500)
            self.assert_schema('ErrorResponse', result.json())
            self.assertNotIn('SECRET', result.text)


if __name__ == '__main__':
    unittest.main()
