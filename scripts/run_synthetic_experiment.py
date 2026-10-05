"""Exercise TF-IDF/LR/grouped CV on invented snapshots only; no real-data loader."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
from phishing.training.experiment import run_synthetic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--groups', type=int, default=40)
    parser.add_argument('--bootstrap-repetitions', type=int, default=2000)
    parser.add_argument('--output', type=Path, default=Path('artifacts/runs') / ('synthetic-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')))
    args = parser.parse_args()
    if args.bootstrap_repetitions < 2:
        parser.error('At least two bootstrap repetitions required')
    print('SYNTHETIC ONLY — outputs verify code; they are not phishing research results.', flush=True)
    result = run_synthetic(args.output, groups=args.groups, repetitions=args.bootstrap_repetitions)
    print(f'Artifacts: {result.resolve()}', flush=True)


if __name__ == '__main__':
    main()
