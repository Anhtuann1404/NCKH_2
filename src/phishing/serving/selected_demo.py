"""Export one preselected fixture CV fit; never select a fold using test results."""
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from sklearn.metrics import average_precision_score

from phishing.evaluation.grouped import make_folds
from phishing.evaluation.metrics import select_validation_threshold
from phishing.serving.demo_model import SyntheticDemoModel
from phishing.training.config import load_config, validate_config
from phishing.training.experiment import fit_fold
from phishing.training.synthetic import make_dataset


def digest(value):
    return sha256(json.dumps(value, default=asdict, sort_keys=True,
                             separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def selection_inputs(config):
    config = validate_config(config)
    samples, dictionary = make_dataset(config['groups'])
    # Preselected, not the best-performing outer test fold. No outer-train refit.
    fold = make_folds(samples, seeds=(17,))[0]
    provenance = {
        'scope': 'synthetic_fixture_only', 'research_evidence': False,
        'selection_policy': 'fixed_seed17_fold0_validation_C_and_threshold_no_refit',
        'target_validation_fpr': 0.05, 'config': config, 'config_sha256': digest(config),
        'dataset_sha256': digest([asdict(s) for s in samples]),
        'dictionary_sha256': digest(dictionary), 'fold': asdict(fold),
        'sample_ids': {name: [samples[i].sample_id for i in getattr(fold, name)]
                       for name in ('train', 'validation', 'test')},
    }
    return samples, dictionary, fold, provenance


class SelectedSyntheticModel(SyntheticDemoModel):
    def __init__(self, config=None):
        samples, dictionary, fold, provenance = selection_inputs(load_config() if config is None else config)
        self.models, self.thresholds = {}, {}
        choices = {}
        for phase, variant in (('url_only', 'M0'), ('url_content', 'M3')):
            model, report, _ = fit_fold(samples, fold, variant, dictionary,
                                       candidates=provenance['config']['C_grid'], targets=(0.05,))
            point = report['operating_points']['0.05']
            if point['threshold'] is None:
                raise ValueError('No feasible validation threshold for selected fixture fit')
            self.models[phase] = model
            self.thresholds[phase] = point['threshold']
            choices[phase] = {'C': report['C'], 'validation_ap': report['validation_ap'],
                              'validation_metrics': point['validation']}
        # Test scores/metrics from fit_fold are deliberately not selection inputs or exports.
        self.training_summary = {**provenance, 'choices': choices}

    @staticmethod
    def _source_hashes():
        hashes = SyntheticDemoModel._source_hashes()
        root = Path(__file__).resolve().parents[3]
        for name in ('serving/selected_demo.py', 'training/experiment.py', 'training/config.py',
                     'training/plan.py', 'evaluation/grouped.py'):
            path = root / 'src/phishing' / name
            hashes[str(path.relative_to(root))] = sha256(path.read_bytes()).hexdigest()
        return hashes

    def bundle(self):
        bundle = super().bundle()
        bundle['bundle_id'] = 'synthetic-demo-selected-fit-v1'
        bundle['dictionary_sha256'] = digest(make_dataset(10)[1])
        return bundle

    @classmethod
    def load(cls, directory):
        manifest = json.loads((Path(directory) / 'manifest.json').read_text(encoding='utf-8'))
        required = {'bundle_format', 'research_evidence', 'preprocessing_version', 'feature_version',
                    'bundle', 'thresholds', 'training_summary', 'runtime_versions',
                    'source_sha256', 'predictors_sha256'}
        if not isinstance(manifest, dict) or set(manifest) != required:
            raise ValueError('Missing or unexpected selected-fit bundle metadata')
        summary = manifest['training_summary']
        try:
            samples, dictionary, fold, expected = selection_inputs(summary['config'])
            choices = summary['choices']
            if set(summary) != set(expected) | {'choices'} or any(digest(summary[k]) != digest(v) for k, v in expected.items()):
                raise ValueError('Selected-fit provenance mismatch')
            if set(choices) != {'url_only', 'url_content'}:
                raise ValueError('Missing selected-fit model choices')
            for choice in choices.values():
                if (set(choice) != {'C', 'validation_ap', 'validation_metrics'}
                        or type(choice['C']) not in (int, float)
                        or choice['C'] not in expected['config']['C_grid']):
                    raise ValueError('Invalid selected-fit validation choices')
        except (KeyError, TypeError, AttributeError) as error:
            raise ValueError('Invalid selected-fit provenance') from error
        # Base loader checks identity, runtime/source/checksum/thresholds before joblib.load.
        instance = super().load(directory)
        validation = [samples[i] for i in fold.validation]
        for phase, model in instance.models.items():
            numeric = dict(model.named_steps['features'].transformer_list)['numeric']
            if digest(numeric.named_steps['extract'].dictionary) != digest(dictionary):
                raise ValueError('Selected-fit dictionary mismatch')
            scores = model.predict_proba([s.snapshot for s in validation])[:, 1].tolist()
            labels = [s.label for s in validation]
            point = select_validation_threshold(labels, scores, 0.05)
            actual = {'C': model.named_steps['classifier'].C,
                      'validation_ap': float(average_precision_score(labels, scores)),
                      'validation_metrics': asdict(point.validation_metrics) if point else None}
            if not point or point.threshold != instance.thresholds[phase] or actual != choices[phase]:
                raise ValueError('Selected-fit predictor/validation/threshold mismatch')
        return instance
