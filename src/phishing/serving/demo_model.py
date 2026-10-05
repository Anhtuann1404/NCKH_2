"""Actual fitted predictors for integration demos, using invented fixtures only.

No corpus input or research accuracy claim. Bundles are locally built demos only.
"""
import asyncio
from importlib.metadata import version
import io
import json
import math
from pathlib import Path
import platform
import shutil
import tempfile

import joblib
from hashlib import sha256
from time import perf_counter

from phishing.evaluation.metrics import select_validation_threshold
from phishing.features import FEATURE_VERSION, extract
from phishing.preprocessing import PREPROCESSING_VERSION, prepare_snapshot
from phishing.training.pipeline import make_pipeline
from phishing.training.synthetic import make_dataset


class SyntheticDemoModel:
    def __init__(self):
        samples, dictionary = make_dataset()
        # Fixed disjoint groups. Fit train only; thresholds use validation only.
        train = [s for s in samples if int(s.group_id.rsplit('-', 1)[1]) < 30]
        validation = [s for s in samples if int(s.group_id.rsplit('-', 1)[1]) >= 30]
        self.models = {}
        self.thresholds = {}
        for phase, variant in [('url_only', 'M0'), ('url_content', 'M3')]:
            model = make_pipeline(variant, dictionary, seed=17)
            model.fit([s.snapshot for s in train], [s.label for s in train])
            scores = model.predict_proba([s.snapshot for s in validation])[:, 1].tolist()
            point = select_validation_threshold([s.label for s in validation], scores, 0.05)
            if point is None:
                raise ValueError('Synthetic validation has no feasible operating point')
            self.models[phase] = model
            self.thresholds[phase] = point.threshold
        self.training_summary = {'train_samples': len(train), 'validation_samples': len(validation),
                                 'seed': 17, 'research_evidence': False}

    @staticmethod
    def _runtime_versions():
        return {'python': platform.python_version(), **{name: version(name)
                for name in ('scikit-learn', 'numpy', 'scipy', 'joblib')}}

    @staticmethod
    def _source_hashes():
        root = Path(__file__).resolve().parents[3]
        paths = sorted((root / 'src/phishing/preprocessing').glob('*.py'))
        paths += sorted((root / 'src/phishing/features').glob('*.py'))
        paths += [root / 'src/phishing/training/pipeline.py',
                  root / 'src/phishing/training/synthetic.py',
                  root / 'src/phishing/evaluation/metrics.py', Path(__file__).resolve()]
        return {str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest() for path in paths}

    def save(self, directory):
        """Write a new local demo directory; never overwrite an existing bundle."""
        directory = Path(directory)
        if directory.exists():
            raise FileExistsError('Bundle already exists; choose a new output directory')
        directory.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix='.synthetic-bundle-', dir=directory.parent))
        try:
            model_path = staging / 'predictors.joblib'
            joblib.dump(self.models, model_path, compress=3)
            manifest = {
                'bundle_format': 'synthetic-demo-v1', 'research_evidence': False,
                'preprocessing_version': PREPROCESSING_VERSION, 'feature_version': FEATURE_VERSION,
                'bundle': self.bundle(), 'thresholds': self.thresholds,
                'training_summary': self.training_summary,
                'runtime_versions': self._runtime_versions(), 'source_sha256': self._source_hashes(),
                'predictors_sha256': sha256(model_path.read_bytes()).hexdigest(),
            }
            (staging / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
            staging.rename(directory)
        finally:
            if staging.exists():
                shutil.rmtree(staging)

    @classmethod
    def load(cls, directory):
        """Load only a trusted locally generated bundle. Hashes detect corruption,
        not malicious replacement: joblib can execute code. Never load uploads.
        """
        directory = Path(directory)
        manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
        if (manifest.get('bundle_format') != 'synthetic-demo-v1'
                or manifest.get('research_evidence') is not False
                or manifest.get('preprocessing_version') != PREPROCESSING_VERSION
                or manifest.get('feature_version') != FEATURE_VERSION):
            raise ValueError('Unsupported demo bundle or preprocessing version')
        if manifest.get('runtime_versions') != cls._runtime_versions():
            raise ValueError('Bundle runtime mismatch; build a new bundle with this environment')
        if manifest.get('source_sha256') != cls._source_hashes():
            raise ValueError('Bundle source mismatch; build a new bundle after code changes')
        thresholds = manifest.get('thresholds', {})
        if set(thresholds) != {'url_only', 'url_content'} or any(
                type(t) not in (int, float) or not math.isfinite(t) or not 0 <= t <= 1
                for t in thresholds.values()):
            raise ValueError('Invalid bundle operating thresholds')
        model_bytes = (directory / 'predictors.joblib').read_bytes()
        if sha256(model_bytes).hexdigest() != manifest.get('predictors_sha256'):
            raise ValueError('Bundle predictor checksum mismatch')
        instance = cls.__new__(cls)  # No training on the load path.
        if manifest.get('bundle') != instance.bundle():
            raise ValueError('Unexpected demo bundle identity')
        models = joblib.load(io.BytesIO(model_bytes))
        if not isinstance(models, dict) or set(models) != {'url_only', 'url_content'}:
            raise ValueError('Invalid demo predictor set')
        for phase, variant in [('url_only', 'M0'), ('url_content', 'M3')]:
            model = models[phase]
            numeric = dict(model.named_steps['features'].transformer_list)['numeric']
            if numeric.named_steps['extract'].variant != variant or list(model.classes_) != [0, 1]:
                raise ValueError('Demo predictor phase or classes mismatch')
        instance.models = models
        instance.thresholds = thresholds
        instance.training_summary = manifest['training_summary']
        return instance

    def metadata(self, phase):
        return {'model_id': f'synthetic-demo-{phase}',
                'variant': 'M0' if phase == 'url_only' else 'M3',
                'preprocessing_version': PREPROCESSING_VERSION,
                'dictionary_version': 'synthetic-only',
                'score_semantics': 'uncalibrated_model_score'}

    def bundle(self):
        return {'bundle_id': 'synthetic-demo-tfidf-lr-v1',
                'url_model': self.metadata('url_only'), 'content_model': self.metadata('url_content'),
                'dictionary_sha256': sha256(b'synthetic-only-not-a-research-dictionary').hexdigest(),
                'feature_version': FEATURE_VERSION}

    def _predict(self, payload):
        started = perf_counter()
        snapshot = prepare_snapshot(payload['url'], payload.get('html'), capture_mode=payload['capture_mode'])
        prepared = perf_counter()
        features = extract(snapshot)
        extracted = perf_counter()
        insufficient = payload['phase'] == 'url_content' and not features.text
        score = None if insufficient else float(self.models[payload['phase']].predict_proba([snapshot])[0, 1])
        threshold = None if insufficient else self.thresholds[payload['phase']]
        ended = perf_counter()
        return {
            **{key: payload[key] for key in ('request_id', 'navigation_id', 'dom_revision', 'phase')},
            'status': 'insufficient_content' if insufficient else 'completed',
            'verdict': 'unable_to_assess' if insufficient else ('warning' if score >= threshold else 'no_indication'),
            'score': score, 'threshold': threshold, 'model': self.metadata(payload['phase']),
            'signals': [{'code': 'synthetic_training_only', 'org_candidate_id': None,
                         'domain_relation': 'not_applicable',
                         'message': 'Mô hình học từ dữ liệu hư cấu; chỉ dùng kiểm thử tích hợp.'}],
            'limitations': ['synthetic_training_only', 'not_research_evidence',
                            'draft_preprocessing_not_frozen', 'uncalibrated_score'],
            'timing_ms': {'preprocess': (prepared-started)*1000, 'extract': (extracted-prepared)*1000,
                          'infer': (ended-extracted)*1000, 'server_total': (ended-started)*1000},
        }

    async def result(self, payload):
        # Keep CPU inference off the event loop; API timeout can return promptly.
        return await asyncio.to_thread(self._predict, payload)
