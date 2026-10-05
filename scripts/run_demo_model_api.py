"""Run M0/M3 learned on synthetic fixtures through the local extension API."""
import argparse
from pathlib import Path
import uvicorn
from run_mock_api import local_token
from phishing.serving.demo_model import SyntheticDemoModel
from phishing.serving.mock_api import MockSettings, create_app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extension-id', required=True)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--requests-per-minute', type=int, default=90)
    parser.add_argument('--token-file', type=Path, default=Path('.env.phishing.local'))
    parser.add_argument('--bundle', type=Path, default=Path('artifacts/models/synthetic-demo-observed-v1'),
                        help='Trusted locally built demo bundle; created once if missing')
    parser.add_argument("--selected-fit", action="store_true", help="Load a separately exported fixture CV-fit bundle; no startup fitting")
    args = parser.parse_args()
    try:
        settings = MockSettings(local_token(args.token_file), args.extension_id, port=args.port, requests_per_minute=args.requests_per_minute)
    except (ValueError, OSError):
        parser.error('Invalid extension ID or local token configuration.')
    model_class = SyntheticDemoModel
    if args.selected_fit:
        from phishing.serving.selected_demo import SelectedSyntheticModel
        model_class = SelectedSyntheticModel
        if not args.bundle.exists():
            parser.error("Selected-fit bundle is missing; build it first at an explicit --bundle path.")
    try:
        if args.bundle.exists():
            backend = model_class.load(args.bundle)
            print('Loaded local synthetic demo bundle; no training at startup.')
        else:
            backend = SyntheticDemoModel()
            backend.save(args.bundle)
            print('Created local synthetic demo bundle for subsequent runs.')
    except (ValueError, OSError, KeyError, TypeError):
        parser.error('Cannot load demo bundle; check integrity/runtime or build a new bundle at a new path.')
    print('SYNTHETIC MODEL DEMO — M0/M3 trained only on invented fixtures; not research evidence.')
    print(f'API: http://127.0.0.1:{settings.port} | local token never logged.')
    uvicorn.run(create_app(settings, backend=backend), host='127.0.0.1', port=settings.port,
                access_log=False, log_level='warning', log_config=None)


if __name__ == '__main__':
    main()
