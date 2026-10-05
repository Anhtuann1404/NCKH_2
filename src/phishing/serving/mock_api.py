"""Contract-compatible mock API; fixed demo scenarios are not ML predictions."""

import asyncio
from collections import deque
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import secrets
from time import perf_counter
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from jsonschema import Draft202012Validator, FormatChecker
from starlette.exceptions import HTTPException

from phishing.features import FEATURE_VERSION, extract
from phishing.preprocessing import PREPROCESSING_VERSION, prepare_snapshot

SPEC_PATH = Path(__file__).resolve().parents[3] / 'docs' / 'openapi.json'
Scenario = Literal['warning', 'no_indication', 'insufficient_content', 'unavailable']


@dataclass(frozen=True)
class MockSettings:
    token: str
    extension_id: str
    port: int = 8765
    scenario: Scenario = 'warning'
    delay_ms: int = 0
    max_body_bytes: int = 2_097_152
    requests_per_minute: int = 90
    processing_timeout_seconds: float = 4.5

    def __post_init__(self):
        if len(self.token) < 32 or not self.token.isascii():
            raise ValueError('A local ASCII token of at least 32 characters is required')
        if not re.fullmatch('[a-p]{32}', self.extension_id):
            raise ValueError('Extension ID must contain 32 lowercase a-p characters')
        if not 1 <= self.port <= 65535 or self.scenario not in {'warning', 'no_indication', 'insufficient_content', 'unavailable'}:
            raise ValueError('Invalid mock configuration')
        if self.delay_ms < 0 or self.max_body_bytes < 1 or self.requests_per_minute < 1:
            raise ValueError('Invalid mock limits')

    @property
    def origin(self):
        return f'chrome-extension://{self.extension_id}'


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({'error': {'code': code, 'message': message}, 'request_id': None}, status_code=status)


class LocalBoundary:
    """Check origin/auth and bound bytes before the route parses JSON."""

    def __init__(self, app, settings: MockSettings):
        self.app = app
        self.settings = settings
        self.recent = deque()

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = {}
        for key, value in scope['headers']:
            if key in {b'host', b'origin', b'authorization', b'content-length'} and key in headers:
                return await error_response(403, 'invalid_headers', 'Duplicate security header.')(scope, receive, send)
            headers[key] = value.decode('latin-1')
        if headers.get(b'host') != f'127.0.0.1:{self.settings.port}':
            return await error_response(403, 'host_denied', 'Local host is not allowed.')(scope, receive, send)
        origin = headers.get(b'origin')
        if origin is not None and origin != self.settings.origin:
            return await error_response(403, 'origin_denied', 'Origin is not allowed.')(scope, receive, send)

        async def cors_send(message):
            if message['type'] == 'http.response.start':
                message['headers'] = list(message.get('headers', [])) + [(b'cache-control', b'no-store')]
                if origin == self.settings.origin:
                    message['headers'] += [(b'access-control-allow-origin', origin.encode()), (b'vary', b'Origin')]
            await send(message)

        if scope['method'] == 'OPTIONS':
            if origin != self.settings.origin or headers.get(b'access-control-request-method') not in {'GET', 'POST'}:
                return await error_response(403, 'preflight_denied', 'Preflight is not allowed.')(scope, receive, cors_send)
            requested = {part.strip().lower() for part in headers.get(b'access-control-request-headers', '').split(',') if part.strip()}
            if not requested <= {'authorization', 'content-type'}:
                return await error_response(403, 'preflight_denied', 'Preflight headers are not allowed.')(scope, receive, cors_send)
            return await Response(status_code=204, headers={
                'Access-Control-Allow-Methods': 'GET, POST',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
            })(scope, receive, cors_send)

        if scope['path'].startswith('/v1/'):
            supplied = headers.get(b'authorization', '')
            if not secrets.compare_digest(supplied.encode('latin-1'), f'Bearer {self.settings.token}'.encode('ascii')):
                return await error_response(401, 'unauthorized', 'Missing or invalid local token.')(scope, receive, cors_send)
            now = perf_counter()
            while self.recent and self.recent[0] <= now - 60:
                self.recent.popleft()
            if len(self.recent) >= self.settings.requests_per_minute:
                response = error_response(429, 'rate_limited', 'Too many requests. Retry later.')
                response.headers['Retry-After'] = '1'
                return await response(scope, receive, cors_send)
            self.recent.append(now)

        if scope['method'] == 'POST':
            if headers.get(b'content-type', '').split(';')[0].strip().lower() != 'application/json':
                return await error_response(415, 'unsupported_media_type', 'JSON body is required.')(scope, receive, cors_send)
            length = headers.get(b'content-length')
            if length is not None:
                if not length.isdecimal():
                    return await error_response(422, 'invalid_length', 'Invalid content length.')(scope, receive, cors_send)
                if int(length) > self.settings.max_body_bytes:
                    return await error_response(413, 'payload_too_large', 'Payload exceeds the byte limit.')(scope, receive, cors_send)
            body = bytearray()
            while True:
                message = await receive()
                if message['type'] == 'http.disconnect':
                    return
                body.extend(message.get('body', b''))
                if len(body) > self.settings.max_body_bytes:
                    return await error_response(413, 'payload_too_large', 'Payload exceeds the byte limit.')(scope, receive, cors_send)
                if not message.get('more_body', False):
                    break
            delivered = False

            async def body_receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
                return await receive()

            return await self.app(scope, body_receive, cors_send)
        return await self.app(scope, receive, cors_send)


def model_metadata(phase):
    return {
        'model_id': f'mock-only-{phase}', 'variant': 'M0' if phase == 'url_only' else 'M3',
        'preprocessing_version': PREPROCESSING_VERSION, 'dictionary_version': 'synthetic-only',
        'score_semantics': 'uncalibrated_model_score',
    }


async def mock_result(payload, settings):
    started = perf_counter()
    snapshot = prepare_snapshot(payload['url'], payload.get('html'), capture_mode=payload['capture_mode'])
    prepared = perf_counter()
    features = extract(snapshot)
    extracted = perf_counter()
    if settings.delay_ms:
        await asyncio.sleep(settings.delay_ms / 1000)
    insufficient = settings.scenario == 'insufficient_content' or (payload['phase'] == 'url_content' and not features.text)
    score = None if insufficient else (0.82 if settings.scenario == 'warning' else 0.2)
    ended = perf_counter()
    return {
        **{key: payload[key] for key in ('request_id', 'navigation_id', 'dom_revision', 'phase')},
        'status': 'insufficient_content' if insufficient else 'completed',
        'verdict': 'unable_to_assess' if insufficient else ('warning' if score >= 0.75 else 'no_indication'),
        'score': score, 'threshold': None if insufficient else 0.75,
        'model': model_metadata(payload['phase']),
        'signals': [{'code': 'mock_only', 'org_candidate_id': None, 'domain_relation': 'not_applicable', 'message': 'Kết quả mô phỏng để kiểm thử giao diện, không phải dự đoán học máy.'}],
        'limitations': ['mock_response_not_model_result', 'draft_preprocessing_not_frozen'],
        'timing_ms': {
            'preprocess': (prepared - started) * 1000, 'extract': (extracted - prepared) * 1000,
            'infer': (ended - extracted) * 1000, 'server_total': (ended - started) * 1000,
        },
    }


def create_app(settings: MockSettings, *, backend=None):
    spec = json.loads(SPEC_PATH.read_text(encoding='utf-8'))
    validator = Draft202012Validator({
        '$ref': '#/components/schemas/AnalyzeRequest', 'components': spec['components'],
    }, format_checker=FormatChecker())
    app = FastAPI(title='NCKH_2 SYNTHETIC DEMO' if backend else 'NCKH_2 MOCK ONLY', docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(LocalBoundary, settings=settings)

    @app.exception_handler(HTTPException)
    async def http_error(request, exception):
        return error_response(exception.status_code, 'http_error', 'Unsupported route or method.')

    @app.exception_handler(Exception)
    async def internal_error(request, exception):
        return error_response(500, 'internal_error', 'Unable to process the request.')

    @app.get('/health')
    async def health():
        return {'status': 'ok', 'model_ready': backend is not None, 'api_version': '0.1.0'}

    @app.get('/v1/model')
    async def model():
        if backend is not None:
            return backend.bundle()
        if settings.scenario == 'unavailable':
            return error_response(503, 'model_unavailable', 'No real model has been loaded.')
        return {
            'bundle_id': 'mock-only-synthetic', 'url_model': model_metadata('url_only'),
            'content_model': model_metadata('url_content'),
            'dictionary_sha256': sha256(b'synthetic-only-not-a-research-dictionary').hexdigest(),
            'feature_version': FEATURE_VERSION,
        }

    @app.post('/v1/analyze')
    async def analyze(request: Request):
        try:
            payload = json.loads(await request.body())
            if not validator.is_valid(payload):
                return error_response(422, 'invalid_request', 'Request does not match the contract.')
        except (ValueError, UnicodeError, RecursionError):
            return error_response(422, 'invalid_request', 'Invalid JSON request.')
        if payload['preprocessing_version'] != PREPROCESSING_VERSION:
            return error_response(409, 'version_mismatch', 'Preprocessing version is not supported.')
        if settings.scenario == 'unavailable':
            return error_response(503, 'model_unavailable', 'No real model has been loaded.')
        try:
            async with asyncio.timeout(settings.processing_timeout_seconds):
                return await backend.result(payload) if backend is not None else await mock_result(payload, settings)
        except TimeoutError:
            return error_response(504, 'processing_timeout', 'Processing exceeded the time budget.')
        except (ValueError, TypeError):
            return error_response(422, 'invalid_snapshot', 'URL or HTML could not be prepared.')
        except Exception:
            return error_response(500, 'internal_error', 'Unable to process the request.')

    return app
