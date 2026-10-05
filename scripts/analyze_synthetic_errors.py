"""Export paired M2/M3 error cases from a saved synthetic run; never train."""
import argparse
from datetime import datetime, timezone
from pathlib import Path

from phishing.evaluation.error_analysis import analyze_run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True, help='Saved synthetic experiment directory')
    parser.add_argument('--output', type=Path, default=Path('artifacts/runs') / ('synthetic-errors-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')))
    args = parser.parse_args()
    try:
        result = analyze_run(args.run, args.output)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))
    print('SYNTHETIC ONLY — error inspection is not research evidence.')
    for row in result['summaries']:
        c = row['categories']
        print(f"seed={row['seed']} target={row['target_fpr']}: corrected={c['m3_corrected']} regressed={c['m3_regressed']} both_wrong={c['both_wrong']} missing={c['missing_operating_point']}")
    print(f'Artifacts: {args.output.resolve()}')


if __name__ == '__main__':
    main()
