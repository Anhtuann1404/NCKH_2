"""Persistence parity and rejection before deserializing local demo bundles."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from phishing.serving.demo_model import SyntheticDemoModel
from phishing.training.synthetic import make_dataset


class DemoBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = SyntheticDemoModel()
        cls.snapshots = [s.snapshot for s in make_dataset()[0][-8:]]

    def test_reload_has_identical_scores_thresholds_without_training(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'bundle'
            self.model.save(target)
            with patch('phishing.serving.demo_model.make_pipeline', side_effect=AssertionError('training')):
                loaded = SyntheticDemoModel.load(target)
            self.assertEqual(loaded.thresholds, self.model.thresholds)
            self.assertEqual(loaded.bundle(), self.model.bundle())
            for phase in ('url_only', 'url_content'):
                np.testing.assert_array_equal(loaded.models[phase].predict_proba(self.snapshots),
                                              self.model.models[phase].predict_proba(self.snapshots))
            with self.assertRaises(FileExistsError):
                self.model.save(target)

    def test_corrupt_predictors_rejected_before_joblib_load(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'bundle'; self.model.save(target)
            (target / 'predictors.joblib').write_bytes(b'corrupted artifact')
            with patch('phishing.serving.demo_model.joblib.load', side_effect=AssertionError('deserialized')):
                with self.assertRaisesRegex(ValueError, 'checksum'):
                    SyntheticDemoModel.load(target)

    def test_metadata_and_environment_mismatch_rejected_before_load(self):
        cases = [('research_evidence', True), ('preprocessing_version', 'wrong'),
                 ('runtime_versions', {}), ('source_sha256', {}),
                 ('thresholds', {'url_only': float('nan'), 'url_content': 0.5})]
        for field, value in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / 'bundle'; self.model.save(target)
                path = target / 'manifest.json'; manifest = json.loads(path.read_text())
                manifest[field] = value; path.write_text(json.dumps(manifest))
                with patch('phishing.serving.demo_model.joblib.load', side_effect=AssertionError('deserialized')):
                    with self.assertRaises(ValueError):
                        SyntheticDemoModel.load(target)


if __name__ == '__main__':
    unittest.main()
