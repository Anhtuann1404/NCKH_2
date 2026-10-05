import test from 'node:test';
import assert from 'node:assert/strict';
import { analyzeWithRetry, APIError, assessmentNote, isCurrent, observedSignalText, OBSERVATION_NOTE, normalizeURL, statusText, validateResponse } from '../dist/core.js';

const request = () => ({ request_id: crypto.randomUUID(), navigation_id: crypto.randomUUID(), dom_revision: 2, phase: 'url_content', url: 'https://fixture.test/', html: '<p>Fixture</p>', preprocessing_version: 'snapshot-dev-0', capture_mode: 'rendered_dom' });
const response = (req, overrides = {}) => ({ request_id: req.request_id, navigation_id: req.navigation_id, dom_revision: req.dom_revision, phase: req.phase, status: 'completed', verdict: 'warning', score: 0.82, threshold: 0.75, model: { model_id: 'mock-only-url_content', preprocessing_version: 'snapshot-dev-0', variant: 'M3' }, limitations: ['mock_response_not_model_result'], ...overrides });
const state = req => ({ navigation_id: req.navigation_id, dom_revision: req.dom_revision, request_id: req.request_id, phase: req.phase, status: 'pending', verdict: null, mock: true });

test('normalize removes credentials/query values/fragment, preserving repeated keys', () => {
  const clean = normalizeURL('https://alice:secret@Fixture.test/login?a=secret&a=other#private');
  assert.equal(clean, 'https://fixture.test/login?a=_redacted_&a=_redacted_');
  assert.equal(normalizeURL(clean), clean);
  assert.throws(() => normalizeURL('javascript:alert(1)'));
  assert.throws(() => normalizeURL('https://fixture.test/\nlogin'));
});
test('stale navigation, revision, phase and request IDs are rejected', () => {
  const req = request(); const current = state(req);
  assert.equal(isCurrent(current, req), true);
  for (const altered of [{ navigation_id: crypto.randomUUID() }, { dom_revision: 1 }, { phase: 'url_only' }, { request_id: crypto.randomUUID() }]) {
    assert.equal(isCurrent(current, { ...req, ...altered }), false);
    assert.throws(() => validateResponse(response(req, altered), req), /stale_response/);
  }
});
test('completed score/verdict consistency and insufficient content are checked', () => {
  const req = request();
  assert.equal(validateResponse(response(req), req).verdict, 'warning');
  assert.throws(() => validateResponse(response(req, { verdict: 'no_indication' }), req));
  assert.throws(() => validateResponse(response(req, { score: NaN }), req));
  assert.throws(() => validateResponse(response(req, { status: 'insufficient_content' }), req));
  assert.equal(validateResponse(response(req, { status: 'insufficient_content', verdict: 'unable_to_assess', score: null, threshold: null }), req).verdict, 'unable_to_assess');
});
test('mock client refuses unlabeled real-model responses', () => {
  const req = request();
  assert.throws(() => validateResponse(response(req, { limitations: [] }), req), /unsupported_bundle/);
});
test('URL-only status is preliminary, offline is never a benign result', () => {
  const req = request();
  assert.match(statusText({ ...state(req), phase: 'url_only', status: 'completed', verdict: 'warning' }), /sơ bộ/);
  assert.equal(statusText({ ...state(req), status: 'unable_to_assess', verdict: 'unable_to_assess' }), 'Chưa đánh giá được');
});
test('network error retries once with a new request ID', async () => {
  const req = request(); const attempts = [];
  const result = await analyzeWithRetry(req, 'synthetic', { retryDelayMs: 1, fetcher: async (url, options) => {
    const body = JSON.parse(options.body); attempts.push(body.request_id);
    if (attempts.length === 1) throw new Error('offline');
    return new Response(JSON.stringify(response(body)), { status: 200 });
  } });
  assert.equal(attempts.length, 2); assert.notEqual(attempts[0], attempts[1]);
  assert.equal(result.request.request_id, attempts[1]);
});
test('unauthorized response is not retried', async () => {
  let calls = 0;
  await assert.rejects(analyzeWithRetry(request(), 'synthetic', { fetcher: async () => { calls++; return new Response('{}', { status: 401 }); } }), /http_401/);
  assert.equal(calls, 1);
});
test('timeout retries only once then reports timeout', async () => {
  let calls = 0;
  const fetcher = async (url, options) => { calls++; return new Promise((resolve, reject) => options.signal.addEventListener('abort', () => reject(new Error('aborted')), { once: true })); };
  await assert.rejects(analyzeWithRetry(request(), 'synthetic', { fetcher, timeoutMs: 10, retryDelayMs: 1 }), /timeout/);
  assert.equal(calls, 2);
});
test('navigation cancellation does not start a retry', async () => {
  const controller = new AbortController(); controller.abort(); let calls = 0;
  await assert.rejects(analyzeWithRetry(request(), 'synthetic', { signal: controller.signal, fetcher: async () => { calls++; } }), /cancelled/);
  assert.equal(calls, 0);
});

 test('synthetic fitted model accepted only with explicit demo limitations and correct phase', () => {
  const req = request();
  const model = { model_id: 'synthetic-demo-url_content', variant: 'M3', preprocessing_version: 'snapshot-dev-0' };
  const value = response(req, { model, limitations: ['synthetic_training_only', 'not_research_evidence'] });
  assert.equal(validateResponse(value, req).verdict, 'warning');
  assert.throws(() => validateResponse({ ...value, limitations: ['synthetic_training_only'] }, req), /unsupported_bundle/);
  assert.throws(() => validateResponse({ ...value, model: { ...model, variant: 'M0' } }, req), /unsupported_bundle/);
 });

test('roundtrip timing is finite and negative server timing is rejected', async () => {
  const req = request();
  const result = await analyzeWithRetry(req, 'synthetic', { fetcher: async () => new Response(JSON.stringify(response(req)), { status: 200 }) });
  assert(Number.isFinite(result.elapsedMs) && result.elapsedMs >= 0);
  assert.throws(() => validateResponse(response(req, { timing_ms: { preprocess: -1, extract: 0, infer: 0, server_total: 0 } }), req), /invalid_response/);
});

test('observations use fixed copy and disappear for pending, errors and URL-only', () => {
  const value = { ...state(request()), status: 'completed', verdict: 'no_indication', demo_kind: 'synthetic_model',
    observed_signals: ['observed_password_input', '<script>untrusted</script>', 'observed_password_input'] };
  assert.deepEqual(observedSignalText(value), ['Trang có ô nhập mật khẩu.']);
  for (const update of [{ status: 'pending' }, { status: 'unable_to_assess' }, { phase: 'url_only' }, { demo_kind: 'mock' }])
    assert.deepEqual(observedSignalText({ ...value, ...update }), []);
  assert.match(OBSERVATION_NOTE, /không giải thích nguyên nhân/);
  assert.match(assessmentNote({ ...value, status: 'unable_to_assess', code: 'insufficient_content' }), /Không đủ nội dung/);
  assert.match(assessmentNote({ ...value, status: 'unable_to_assess', code: 'http_503' }), /Chưa nhận được kết quả/);
  assert.equal(statusText({ ...value, verdict: null }), 'Chưa đánh giá được');
  const req = request();
  assert.throws(() => validateResponse(response(req, { signals: 'invalid' }), req), /invalid_response/);
});
