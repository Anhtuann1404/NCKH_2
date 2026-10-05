"""Build an ignored synthetic model bundle at a new path, without corpus access."""
import argparse
from pathlib import Path
from phishing.serving.demo_model import SyntheticDemoModel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('artifacts/models/synthetic-demo-v1'))
    parser.add_argument("--selected-fit", action="store_true", help="Export fixed seed17/fold0 with validation-selected C and threshold")
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; choose a new --output path. Existing bundles are preserved.')
    if args.selected_fit:
        from phishing.serving.selected_demo import SelectedSyntheticModel
        model = SelectedSyntheticModel()
    else:
        model = SyntheticDemoModel()
    model.save(args.output)
    print(f'Saved synthetic-only demo bundle to {args.output}; not research evidence.')


if __name__ == '__main__':
    main()
