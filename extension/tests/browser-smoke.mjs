// Isolated Chromium/profile; only local synthetic pages are loaded.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { cp, mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { chromium } from 'playwright';

const project = path.resolve('..');
const builtExtension = path.resolve('dist');
const fixtures = path.join(project, 'tests/fixtures/demo_pages');
const token = 'synthetic-fixture-token-never-use-in-production';
const profile = await mkdtemp(path.join(tmpdir(), 'nckh-extension-test-'));
const extension = path.join(profile, 'extension');
const portProbe = createServer();
await new Promise(resolve => portProbe.listen(0, '127.0.0.1', resolve));
const apiPort = portProbe.address().port;
await new Promise(resolve => portProbe.close(resolve));
const apiOrigin = `http://127.0.0.1:${apiPort}`;
await cp(builtExtension, extension, { recursive: true });
for (const name of ['manifest.json', 'background.js', 'core.js']) {
  const file = path.join(extension, name);
  await writeFile(file, (await readFile(file, 'utf8')).replaceAll('http://127.0.0.1:8765', apiOrigin));
}
const sampleArg = process.argv.indexOf('--latency-samples');
const latencyCount = sampleArg < 0 ? 0 : Number(process.argv[sampleArg + 1]);
if (!Number.isInteger(latencyCount) || latencyCount < 0 || latencyCount > 200) throw new Error('Latency samples must be an integer from 0 to 200.');
const latencyRows = [];
const checks = [];
const apiBodies = [];
let context, processAPI, extensionId;

const server = createServer(async (req, res) => {
  const name = new URL(req.url, 'http://127.0.0.1').pathname.split('/').pop();
  if (['large.html', 'oversize.html'].includes(name)) {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    const text = name === 'large.html' ? '<p>' + 'Synthetic long content. '.repeat(4) + '</p>' : '<p>' + 'x'.repeat(1_100_000) + '</p>';
    res.end('<!doctype html><html><head><title>Large synthetic fixture</title></head><body>' + (name === 'large.html' ? text.repeat(6000) : text) + '</body></html>');
    return;
  }
  if (!['login.html', 'ordinary.html'].includes(name)) { res.writeHead(404); res.end(); return; }
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.end(await readFile(path.join(fixtures, name)));
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;

async function eventually(fn, description, timeout = 12000) {
  const until = Date.now() + timeout;
  while (Date.now() < until) {
    if (await fn()) return;
    await new Promise(resolve => setTimeout(resolve, 80));
  }
  throw new Error(`Timeout waiting for ${description}`);
}
async function stopAPI() {
  if (processAPI && processAPI.exitCode === null) {
    const ended = new Promise(resolve => processAPI.once('exit', resolve));
    processAPI.kill('SIGTERM'); await ended;
  }
  processAPI = undefined;
}
async function startAPI(scenario = 'warning', delay = 0) {
  await stopAPI();
  let occupied = false;
  try { await fetch(`${apiOrigin}/health`); occupied = true; } catch { /* no service listening */ }
  if (occupied) throw new Error('Port 8765 is already in use; this test will not stop an unrelated service.');
  processAPI = spawn(path.join(project, '.venv/bin/python'), (scenario === 'synthetic_model' ? ['scripts/run_demo_model_api.py', '--extension-id', extensionId, '--port', String(apiPort), '--requests-per-minute', '300'] : ['scripts/run_mock_api.py', '--extension-id', extensionId, '--port', String(apiPort), '--scenario', scenario, '--delay-ms', String(delay)]), {
    cwd: project, env: { ...process.env, PYTHONPATH: 'src', PHISHING_LOCAL_API_TOKEN: token }, stdio: ['ignore', 'ignore', 'pipe'],
  });
  let stderr = '';
  processAPI.stderr.on('data', data => { stderr += data.toString(); });
  await eventually(async () => {
    if (processAPI.exitCode !== null) throw new Error(`Mock API exited: ${stderr}`);
    try { return (await fetch(`${apiOrigin}/health`)).ok; } catch { return false; }
  }, 'mock API health');
}

try {
  // Do not attach to the user's Chrome profile or logged-in sessions.
  context = await chromium.launchPersistentContext(profile, { channel: 'chromium', headless: true, args: [`--disable-extensions-except=${extension}`, `--load-extension=${extension}`] });
  let [worker] = context.serviceWorkers();
  if (!worker) worker = await context.waitForEvent('serviceworker');
  extensionId = worker.url().split('/')[2];
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    return url.protocol === 'chrome-extension:' || url.hostname === '127.0.0.1' ? route.continue() : route.abort();
  });
  context.on('request', request => {
    if (request.url() === `${apiOrigin}/v1/analyze`) apiBodies.push(request.postDataJSON());
  });
  await startAPI();
  const page = await context.newPage();
  await page.goto(`${origin}/login.html?token=SECRET_PAGE#SECRET_HASH`);
  await new Promise(resolve => setTimeout(resolve, 800));
  assert.equal(apiBodies.length, 0);
  checks.push('disabled_by_default_sends_no_snapshot');

  const popup = await context.newPage();
  await popup.goto(`chrome-extension://${extensionId}/popup.html`);
  assert.match(await popup.locator('body').innerText(), /DEMO MÔ PHỎNG/);
  await popup.locator('#token').fill(token);
  await popup.locator('#enabled').check();
  await popup.locator('button').click();
  await page.bringToFront();
  await eventually(async () => apiBodies.some(body => body.phase === 'url_only'), 'URL-only request');
  assert.equal(apiBodies.some(body => body.phase === 'url_content'), false);
  assert.equal(apiBodies[0].url.includes('SECRET_'), false);
  checks.push('url_only_without_content_consent');

  await popup.locator('#content').check();
  await popup.locator('button').click();
  await page.bringToFront();
  await eventually(async () => apiBodies.some(body => body.phase === 'url_content'), 'content request');
  const content = apiBodies.filter(body => body.phase === 'url_content').at(-1);
  assert.equal(content.html.includes('SECRET_'), false);
  assert.equal(content.html.includes('onclick='), false);
  assert.equal(content.html.includes('value='), false);
  assert.equal(content.html.includes('nckh-phishing-demo-banner'), false);
  checks.push('snapshot_removes_prefilled_values_handlers_and_banner');
  const tabId = await worker.evaluate(async url => (await chrome.tabs.query({})).find(tab => tab.url === url).id, page.url());
  async function savedState() { return worker.evaluate(async id => (await chrome.storage.session.get(`tab:${id}`))[`tab:${id}`], tabId); }
  await eventually(async () => (await savedState())?.status === 'completed', 'mock warning state');
  assert.equal((await savedState()).verdict, 'warning');
  const keys = Object.keys(await savedState());
  assert.equal(keys.some(name => ['url', 'html', 'token'].includes(name)), false);
  checks.push('mock_warning_and_no_payload_in_session_storage');

  const beforeDynamic = (await savedState()).dom_revision;
  await page.locator('#dynamic').click();
  await eventually(async () => (await savedState())?.dom_revision > beforeDynamic && (await savedState())?.status === 'completed', 'dynamic DOM snapshot');
  checks.push('dynamic_dom_increments_revision');
  const beforeSPA = (await savedState()).navigation_id;
  await page.locator('#spa').click();
  await eventually(async () => (await savedState())?.navigation_id !== beforeSPA && (await savedState())?.status === 'completed', 'SPA navigation');
  checks.push('spa_creates_new_navigation');

  await startAPI('no_indication');
  await page.goto(`${origin}/ordinary.html`);
  await eventually(async () => (await savedState())?.verdict === 'no_indication', 'mock no indication');
  checks.push('mock_no_indication');

  await startAPI('insufficient_content');
  await page.goto(`${origin}/login.html`);
  await eventually(async () => (await savedState())?.status === 'unable_to_assess', 'insufficient content');
  checks.push('insufficient_content_is_unable_to_assess');

  await startAPI('warning', 1200);
  await page.goto(`${origin}/login.html`);
  await eventually(async () => (await savedState())?.status === 'pending', 'pending old navigation');
  const oldNavigation = (await savedState()).navigation_id;
  await page.goto(`${origin}/ordinary.html`);
  await eventually(async () => (await savedState())?.status === 'completed', 'new navigation result');
  assert.notEqual((await savedState()).navigation_id, oldNavigation);
  checks.push('navigation_drops_old_result');

  await startAPI('synthetic_model');
  await page.goto(`${origin}/login.html`);
  await eventually(async () => (await savedState())?.demo_kind === 'synthetic_model' && (await savedState())?.phase === 'url_content' && (await savedState())?.status === 'completed', 'fitted TF-IDF model result through extension');
  assert.equal((await savedState()).mock, false);
  checks.push('synthetic_fitted_model_api_extension');

  if (latencyCount) {
    // Measure settled requests, separately per phase; two warmups excluded.
    for (const phase of ['url_only', 'url_content']) {
      await worker.evaluate(async allowContent => chrome.storage.local.set({ analyzeContent: allowContent }), phase === 'url_content');
      await new Promise(resolve => setTimeout(resolve, 200));
      for (let index = -2; index < latencyCount; index++) {
        const previousNavigation = (await savedState())?.navigation_id;
        await page.goto(`${origin}/${index % 2 === 0 ? 'ordinary.html' : 'login.html'}?iteration=${index}`);
        await eventually(async () => {
          const state = await savedState();
          return state?.navigation_id !== previousNavigation && state?.demo_kind === 'synthetic_model' && state?.phase === phase && state?.status === 'completed' && Number.isFinite(state?.timing_ms?.client_roundtrip);
        }, `latency sample ${phase}/${index}`);
        if (index >= 0) {
          const state = await savedState();
          latencyRows.push({ phase, fixture: index % 2 === 0 ? 'ordinary' : 'login', timing_ms: state.timing_ms });
        }
      }
    }
    checks.push('latency_samples_for_both_phases');
  }

  await worker.evaluate(async () => chrome.storage.local.set({ analyzeContent: true }));
  await new Promise(resolve => setTimeout(resolve, 200));
  const beforeLarge = apiBodies.length;
  await page.goto(`${origin}/large.html`);
  await eventually(async () => {
    const state = await savedState();
    return state?.phase === 'url_content' && state?.status === 'completed' && apiBodies.slice(beforeLarge).some(body => body.phase === 'url_content');
  }, 'large DOM model inference', 20000);
  const largeBody = apiBodies.slice(beforeLarge).find(body => body.phase === 'url_content');
  assert(largeBody.html.length > 500000 && largeBody.html.length < 1000000);
  checks.push('large_dom_under_limit_is_analyzed');

  const beforeOversize = apiBodies.length;
  await page.goto(`${origin}/oversize.html`);
  await eventually(async () => (await savedState())?.status === 'unable_to_assess' && (await savedState())?.code === 'snapshot_too_large', 'oversize DOM blocked');
  assert.equal(apiBodies.slice(beforeOversize).some(body => body.phase === 'url_content'), false);
  checks.push('oversize_dom_is_not_sent_or_truncated');

  // Invalid credentials must never become a no-indication verdict.
  await worker.evaluate(async () => chrome.storage.local.set({ token: 'incorrect-demo-token' }));
  await page.goto(`${origin}/login.html`);
  await eventually(async () => (await savedState())?.code === 'http_401' && (await savedState())?.status === 'unable_to_assess', 'invalid token state');
  checks.push('invalid_token_is_unable_to_assess');
  await worker.evaluate(async value => chrome.storage.local.set({ token: value }), token);
  await new Promise(resolve => setTimeout(resolve, 200));


  await stopAPI();
  await page.goto(`${origin}/login.html`);
  await eventually(async () => (await savedState())?.status === 'unable_to_assess', 'offline state');
  assert.equal((await savedState()).code, 'network_error');
  checks.push('offline_is_unable_to_assess');
  await popup.bringToFront();
  await popup.locator('#enabled').uncheck();
  await popup.locator('button').click();
  await eventually(async () => (await savedState()) === undefined, 'disabled state clear');
  const countDisabled = apiBodies.length;
  await page.goto(`${origin}/ordinary.html`);
  await new Promise(resolve => setTimeout(resolve, 800));
  assert.equal(apiBodies.length, countDisabled);
  checks.push('disable_clears_state_and_stops_requests');

  await popup.bringToFront();
  await mkdir(path.join(project, 'artifacts/smoke'), { recursive: true });
  await popup.locator('body').screenshot({ path: path.join(project, 'artifacts/smoke/popup.png') });
  const report = { checked_at: new Date().toISOString(), scope: 'synthetic mock and fitted-model integration; no research accuracy or latency claim', browser: context.browser()?.version(), checks, passed: checks.length };
  await writeFile(path.join(project, 'artifacts/smoke/browser-report.json'), JSON.stringify(report, null, 2) + '\n');
  if (latencyCount) {
    const percentile = (values, p) => {
      const sorted = [...values].sort((a, b) => a - b);
      const position = (sorted.length - 1) * p;
      const low = Math.floor(position), high = Math.ceil(position);
      return sorted[low] + (sorted[high] - sorted[low]) * (position - low);
    };
    const summary = {};
    for (const phase of ['url_only', 'url_content']) {
      summary[phase] = {};
      for (const field of ['client_roundtrip', 'preprocess', 'extract', 'infer', 'server_total']) {
        const values = latencyRows.filter(row => row.phase === phase).map(row => row.timing_ms[field]);
        assert.equal(values.length, latencyCount);
        assert(values.every(value => Number.isFinite(value) && value >= 0));
        summary[phase][field] = { n: values.length, p50_ms: percentile(values, 0.5), p95_ms: percentile(values, 0.95) };
      }
    }
    const bundleManifest = JSON.parse(await readFile(path.join(project, 'artifacts/models/synthetic-demo-v1/manifest.json'), 'utf8'));
    const latencyReport = { checked_at: report.checked_at, research_evidence: false,
      scope: 'headless Chromium loopback synthetic integration; sequential settled requests',
      client_roundtrip_definition: 'service worker before serialization/fetch through response parse/validation; includes retry delay if any',
      excluded: ['DOM snapshot construction', '500ms content debounce', 'page navigation/rendering', 'banner display', 'bundle load/startup'],
      warmups_per_phase: 2, samples_per_phase: latencyCount, api_requests_per_minute: 300, browser: report.browser,
      runtime_versions: bundleManifest.runtime_versions, source_sha256: bundleManifest.source_sha256,
      bundle_id: bundleManifest.bundle.bundle_id, predictors_sha256: bundleManifest.predictors_sha256,
      summary, samples: latencyRows, failure_checks: checks };
    await writeFile(path.join(project, 'artifacts/smoke/latency-report.json'), JSON.stringify(latencyReport, null, 2) + '\n');
    console.log(JSON.stringify({ latency_summary: summary }, null, 2));
  }

  console.log(JSON.stringify(report, null, 2));
} finally {
  await context?.close(); await stopAPI();
  await new Promise(resolve => server.close(resolve));
  await rm(profile, { recursive: true, force: true });
}
