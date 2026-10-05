"""Synthetic integration tests; no research labels or corpus access."""
import unittest
from fastapi.testclient import TestClient
from phishing.serving.demo_model import SyntheticDemoModel
from phishing.serving.mock_api import MockSettings, create_app
from phishing.training.synthetic import make_dataset
from phishing.preprocessing import prepare_snapshot
from test_mock_api import TOKEN, EXTENSION_ID, HEADERS, payload
import test_mock_api


class DemoModelAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = SyntheticDemoModel()

    def api(self):
        return TestClient(create_app(MockSettings(TOKEN, EXTENSION_ID), backend=self.backend),
                          base_url='http://127.0.0.1:8765', raise_server_exceptions=False)

    def test_schema_and_score_parity_for_both_phases(self):
        samples, _ = make_dataset()
        sample = samples[-4]
        with self.api() as api:
            self.assertTrue(api.get('/health').json()['model_ready'])
            test_mock_api.MockAPITests().assert_schema('ActiveBundle', api.get('/v1/model', headers=HEADERS).json())
            for content in (False, True):
                request = payload(content)
                request['url'] = sample.snapshot.url
                if content:
                    request['html'] = sample.snapshot.html
                body = api.post('/v1/analyze', headers=HEADERS, json=request).json()
                test_mock_api.MockAPITests().assert_schema('AnalyzeResponse', body)
                self.assertIn('not_research_evidence', body['limitations'])
                self.assertNotIn('mock_response_not_model_result', body['limitations'])
                expected = self.backend.models[request['phase']].predict_proba([sample.snapshot])[0, 1]
                self.assertAlmostEqual(body['score'], float(expected))
                self.assertEqual(body['threshold'], self.backend.thresholds[request['phase']])

    def test_content_changes_prediction_instead_of_fixed_mock_score(self):
        with self.api() as api:
            request = payload()
            request['html'] = '<h1>Northstar Fixture</h1><p>Verify your account</p><form action="https://collector.fixture.test/send"><input type="password"></form>'
            first = api.post('/v1/analyze', headers=HEADERS, json=request).json()
            request['html'] = '<h1>News</h1><p>Article about Northstar Fixture community activities</p>'
            second = api.post('/v1/analyze', headers=HEADERS, json=request).json()
            self.assertNotAlmostEqual(first['score'], second['score'], places=4)
            self.assertGreater(first['score'], second['score'])

    def test_empty_content_and_auth_do_not_produce_benign_verdict(self):
        with self.api() as api:
            self.assertEqual(api.post('/v1/analyze', json=payload()).status_code, 401)
            request = payload(); request['html'] = '<script>private</script>'
            body = api.post('/v1/analyze', headers=HEADERS, json=request).json()
            self.assertEqual(body['verdict'], 'unable_to_assess')
            self.assertIsNone(body['score'])
            self.assertEqual([s['code'] for s in body['signals']], ['synthetic_training_only'])

    def test_observations_follow_content_and_do_not_change_score(self):
        with self.api() as api:
            request = payload()
            request['html'] = '<h1>Northstar Fixture</h1><form action="https://collector.fixture.test/send"><input type="password" value="secret"></form>'
            body = api.post('/v1/analyze', headers=HEADERS, json=request).json()
            codes = {s['code'] for s in body['signals']}
            self.assertTrue({'observed_password_input', 'observed_organization_mention',
                             'observed_unverified_domain', 'observed_external_form'} <= codes)
            snapshot = prepare_snapshot(
                request['url'], request['html'], capture_mode=request['capture_mode'])
            self.assertAlmostEqual(body['score'], float(self.backend.models['url_content'].predict_proba([snapshot])[0, 1]))
            self.assertNotIn('secret', str(body['signals']))
            request['html'] = '<h1>Community news</h1>'
            ordinary = api.post('/v1/analyze', headers=HEADERS, json=request).json()
            self.assertEqual([s['code'] for s in ordinary['signals']], ['synthetic_training_only'])
            preliminary = api.post('/v1/analyze', headers=HEADERS, json=payload(False)).json()
            self.assertEqual([s['code'] for s in preliminary['signals']], ['synthetic_training_only'])


if __name__ == '__main__':
    unittest.main()
