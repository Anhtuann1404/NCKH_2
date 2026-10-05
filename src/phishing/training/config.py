"""Fixture run settings; the approved split/model protocol stays fixed."""
import json
from pathlib import Path
from phishing.training.pipeline import VARIANTS

DEFAULT_CONFIG = Path(__file__).resolve().parents[3] / 'configs/synthetic_experiment.json'


def load_config(path=DEFAULT_CONFIG, *, groups=None, repetitions=None):
    config = json.loads(Path(path).read_text(encoding='utf-8'))
    return validate_config(config, groups=groups, repetitions=repetitions)


def validate_config(config, *, groups=None, repetitions=None):
    config = dict(config)
    fixed = {'scope': 'synthetic_fixture_only', 'research_evidence': False,
             'groups': 40, 'seeds': [17, 42, 2026], 'outer_folds': 5, 'inner_folds': 3,
             'C_grid': [0.25, 1.0, 4.0], 'targets': [0.01, 0.05], 'variants': list(VARIANTS),
             'bootstrap_repetitions': 2000, 'bootstrap_seed_base': 813}
    if set(config) != set(fixed):
        raise ValueError('Unexpected or missing synthetic configuration fields')
    for key in fixed.keys() - {'groups', 'bootstrap_repetitions'}:
        # Type comparison also rejects booleans masquerading as numeric settings.
        if json.dumps(config[key]) != json.dumps(fixed[key]):
            raise ValueError(f'Fixture protocol field cannot be changed: {key}')
    if groups is not None:
        config['groups'] = groups
    if repetitions is not None:
        config['bootstrap_repetitions'] = repetitions
    for key, minimum in (('groups', 10), ('bootstrap_repetitions', 2)):
        if type(config[key]) is not int or config[key] < minimum:
            raise ValueError(f'{key} must be an integer >= {minimum}')
    return config
