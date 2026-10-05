"""Build an ignored synthetic model bundle at a new path, without corpus access."""
import argparse
from pathlib import Path
from phishing.serving.demo_model import SyntheticDemoModel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('artifacts/models/synthetic-demo-v1'))
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; choose a new --output path. Existing bundles are preserved.')
    model = SyntheticDemoModel()
    model.save(args.output)
    print(f'Saved synthetic-only demo bundle to {args.output}; not research evidence.')


if __name__ == '__main__':
    main()
