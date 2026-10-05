"""Selected fixture fit export and offline/API parity; no real-data training."""
import copy
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from phishing.serving.demo_model import SyntheticDemoModel
from phishing.serving.selected_demo import SelectedSyntheticModel, digest, selection_inputs
from phishing.serving.mock_api import MockSettings, create_app
from phishing.evaluation.metrics import select_validation_threshold
from phishing.preprocessing import prepare_snapshot
from test_mock_api import TOKEN, EXTENSION_ID, HEADERS, payload


class SelectedFitBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = SelectedSyntheticModel()
        cls.samples, cls.dictionary, cls.fold, cls.provenance = selection_inputs(cls.model.training_summary['config'])

    def test_selected_fit_is_fixed_and_threshold_uses_validation(self):
        self.assertEqual((self.fold.seed, self.fold.number), (17, 0))
        summary = self.model.training_summary
        self.assertFalse(summary['research_evidence'])
        parts = summary['sample_ids']
        self.assertFalse(set(parts['train']) & set(parts['validation']))
        self.assertFalse(set(parts['train']) & set(parts['test']))
        self.assertNotIn('test_ap', json.dumps(summary))
        validation = [self.samples[i] for i in self.fold.validation]
        for phase, model in self.model.models.items():
            scores = model.predict_proba([s.snapshot for s in validation])[:, 1].tolist()
            point = select_validation_threshold([s.label for s in validation], scores, 0.05)
            self.assertEqual(self.model.thresholds[phase], point.threshold)
            self.assertEqual(summary['choices'][phase]['validation_metrics'], asdict(point.validation_metrics))
        self.assertEqual(self.model.bundle()['dictionary_sha256'], digest(self.dictionary))

    def test_roundtrip_offline_and_api_parity_without_refit(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'bundle'; self.model.save(target)
            with patch('phishing.serving.selected_demo.fit_fold', side_effect=AssertionError('fit on load')):
                loaded = SelectedSyntheticModel.load(target)
            api = TestClient(create_app(MockSettings(TOKEN, EXTENSION_ID), backend=loaded), base_url='http://127.0.0.1:8765')
            with api:
                self.assertEqual(api.get('/v1/model', headers=HEADERS).json(), loaded.bundle())
                for i in self.fold.test[:8]:
                    sample = self.samples[i]
                    for content in (False, True):
                        for mode in (('stored_html', 'rendered_dom') if content else ('url_only',)):
                            req = payload(content); req.update(url=sample.snapshot.url, capture_mode=mode)
                            if content: req['html'] = sample.snapshot.html
                            snapshot = prepare_snapshot(req['url'], req.get('html'), capture_mode=mode)
                            expected = float(self.model.models[req['phase']].predict_proba([snapshot])[0, 1])
                            response = api.post('/v1/analyze', headers=HEADERS, json=req)
                            self.assertEqual(response.status_code, 200)
                            body = response.json()
                            self.assertEqual(body['score'], expected)
                            self.assertEqual(body['threshold'], self.model.thresholds[req['phase']])
                            self.assertEqual(body['verdict'], 'warning' if expected >= body['threshold'] else 'no_indication')
                req = payload(); req['html'] = '<script>private</script>'
                body = api.post('/v1/analyze', headers=HEADERS, json=req).json()
                self.assertEqual(body['verdict'], 'unable_to_assess')
                self.assertIsNone(body['score'])
            with self.assertRaises(FileExistsError): self.model.save(target)

    def test_missing_or_changed_manifest_fields_rejected_before_deserialization(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'bundle'; self.model.save(target)
            path = target / 'manifest.json'; original = json.loads(path.read_text())
            for field in original:
                broken = copy.deepcopy(original); broken.pop(field)
                path.write_text(json.dumps(broken))
                with self.subTest(missing=field), patch('phishing.serving.demo_model.joblib.load', side_effect=AssertionError('deserialized')):
                    with self.assertRaises(ValueError): SelectedSyntheticModel.load(target)
            for field, value in (('bundle', {}), ('feature_version', 'wrong'), ('runtime_versions', {}),
                                 ('source_sha256', {}), ('research_evidence', True), ('preprocessing_version', 'wrong'),
                                 ('thresholds', {'url_only': True, 'url_content': 0.5})):
                broken = copy.deepcopy(original); broken[field] = value; path.write_text(json.dumps(broken))
                with self.subTest(field=field), patch('phishing.serving.demo_model.joblib.load', side_effect=AssertionError('deserialized')):
                    with self.assertRaises(ValueError): SelectedSyntheticModel.load(target)

    def test_provenance_tampering_and_predictor_checksum_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'bundle'; self.model.save(target)
            path = target / 'manifest.json'; original = json.loads(path.read_text())
            for field, value in (('scope', 'research'), ('research_evidence', True), ('fold', {}),
                                 ('dictionary_sha256', 'bad'), ('sample_ids', {}), ('choices', {})):
                broken = copy.deepcopy(original); broken['training_summary'][field] = value
                path.write_text(json.dumps(broken))
                with self.subTest(field=field), patch('phishing.serving.demo_model.joblib.load', side_effect=AssertionError('deserialized')):
                    with self.assertRaises(ValueError): SelectedSyntheticModel.load(target)
            path.write_text(json.dumps(original))
            (target / 'predictors.joblib').write_bytes(b'bad')
            with patch('phishing.serving.demo_model.joblib.load', side_effect=AssertionError('deserialized')):
                with self.assertRaisesRegex(ValueError, 'checksum'): SelectedSyntheticModel.load(target)

    def test_valid_but_changed_threshold_is_rejected_against_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'bundle'; self.model.save(target)
            path = target / 'manifest.json'; value = json.loads(path.read_text())
            value['thresholds']['url_content'] = 1.0 if self.model.thresholds['url_content'] != 1 else 0
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'validation/threshold'): SelectedSyntheticModel.load(target)

    def test_demo_bundle_cannot_be_misidentified_as_selected_fit(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'bundle'; SyntheticDemoModel().save(target)
            with self.assertRaises(ValueError): SelectedSyntheticModel.load(target)


if __name__ == '__main__':
    unittest.main()
