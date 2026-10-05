"""Exercise TF-IDF/LR/grouped CV on invented snapshots only; no real-data loader."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
from phishing.training.experiment import run_synthetic
from phishing.training.config import DEFAULT_CONFIG, load_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--groups', type=int)
    parser.add_argument('--bootstrap-repetitions', type=int)
    parser.add_argument('--output', type=Path, default=Path('artifacts/runs') / ('synthetic-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')))
    args = parser.parse_args()
    try:
        config = load_config(args.config, groups=args.groups, repetitions=args.bootstrap_repetitions)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print('SYNTHETIC ONLY — outputs verify code; they are not phishing research results.', flush=True)
    result = run_synthetic(args.output, config=config)
    print(f'Artifacts: {result.resolve()}', flush=True)


if __name__ == '__main__':
    main()
