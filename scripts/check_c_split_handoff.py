"""Audit C's split package integrity without fitting or unlocking a model."""

import argparse
import json

from phishing.training.handoff import inspect_c_split_artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    args = parser.parse_args()
    try:
        groups, grouped = inspect_c_split_artifacts(args.manifest)
        folds = grouped['splits_by_seed']
        if not isinstance(folds, dict):
            raise ValueError('Missing grouped folds')
        result = {'status': 'split_package_integrity_valid', 'research_training_allowed': False,
                  'samples': len(groups['sample_groups']),
                  'folds': sum(len(value) for value in folds.values())}
    except (OSError, ValueError, KeyError, TypeError):
        result = {'status': 'blocked', 'research_training_allowed': False,
                  'reason': 'Split package integrity or schema failed'}
        print(json.dumps(result))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
