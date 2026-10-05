"""Run the loopback demo API. Generates an ignored token file when necessary."""

import argparse
import os
from pathlib import Path
import secrets

import uvicorn

from phishing.serving.mock_api import MockSettings, create_app


def local_token(path: Path) -> str:
    supplied = os.environ.get('PHISHING_LOCAL_API_TOKEN')
    if supplied:
        return supplied
    if not path.exists():
        token = secrets.token_urlsafe(32)
        with path.open('x', encoding='utf-8') as handle:
            os.chmod(path, 0o600)
            handle.write(f'PHISHING_LOCAL_API_TOKEN={token}\n')
    lines = path.read_text(encoding='utf-8').splitlines()
    for line in lines:
        if line.startswith('PHISHING_LOCAL_API_TOKEN='):
            return line.partition('=')[2]
    raise ValueError('Token file does not contain PHISHING_LOCAL_API_TOKEN')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extension-id', required=True)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--scenario', choices=['warning', 'no_indication', 'insufficient_content', 'unavailable'], default='warning')
    parser.add_argument('--delay-ms', type=int, default=0)
    parser.add_argument('--token-file', type=Path, default=Path('.env.phishing.local'))
    args = parser.parse_args()
    try:
        settings = MockSettings(local_token(args.token_file), args.extension_id, port=args.port, scenario=args.scenario, delay_ms=args.delay_ms)
    except (ValueError, OSError):
        parser.error('Invalid configuration; check extension ID, delay and local token file.')
    print('MOCK ONLY — fixed synthetic scores; no real model loaded.')
    print(f'API: http://127.0.0.1:{settings.port} | token in .env.phishing.local or environment; never logged.')
    uvicorn.run(create_app(settings), host='127.0.0.1', port=settings.port, access_log=False, log_level='warning', log_config=None)


if __name__ == '__main__':
    main()
