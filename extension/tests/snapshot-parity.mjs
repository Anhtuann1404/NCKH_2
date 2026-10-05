// Fixture-only comparison against the Python offline pipeline.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, rm, mkdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { chromium } from 'playwright';

const project = path.resolve('..');
const temporary = await mkdtemp(path.join(tmpdir(), 'nckh-parity-'));
const wrap = body => '<!doctype html><html><head><meta charset="utf-8"><title>Synthetic parity</title></head><body>' + body + '</body></html>';
const fixtures = [
  { name: 'forms_and_relative_links', html: wrap('<h1>Fixture login</h1><form action="../submit?ticket=PRIVATE_QUERY"><input name="account" value="PRIVATE_VALUE"><input type="password" value="PRIVATE_PASSWORD"></form><a href="/help?token=PRIVATE_QUERY#PRIVATE_FRAGMENT">Help</a>') },
  { name: 'privacy_hidden_editable_scripts', html: wrap('<p>Visible text</p><div hidden>PRIVATE_HIDDEN</div><div aria-hidden="true">PRIVATE_ARIA</div><textarea>PRIVATE_TEXTAREA</textarea><div contenteditable>PRIVATE_EDITABLE</div><!--PRIVATE_COMMENT--><script>window.parityFixture = "PRIVATE_SCRIPT"</script><style>.x{color:red}</style>') },
  { name: 'unicode_and_duplicate_attributes', html: wrap('<p>Đăng nhập ngân hàng — 😀 😀</p><a href="/verify?a=PRIVATE_QUERY&a=OTHER" title="Fixture" title="Ignored">Xác minh</a><input type="password" type="text">') },
  { name: 'malformed_table_repair', html: wrap('<table><p>Moved by browser</p><tr><td>Cell</td></tr></table>') },
  { name: 'nested_form_repair', html: wrap('<form action="/one"><p>One</p><form action="/two"><input type="password"></form></form>') },
  { name: 'dynamic_dom', html: wrap('<p id="initial">Initial</p><script>document.getElementById("initial").textContent="Dynamic content"</script>') },
];
const server = createServer(async (req, res) => {
  if (req.url === '/snapshot.js') {
    res.setHeader('Content-Type', 'text/javascript');
    res.end(await readFile(path.resolve('dist/snapshot.js'))); return;
  }
  const index = Number(new URL(req.url, 'http://127.0.0.1').searchParams.get('case'));
  if (!Number.isInteger(index) || !fixtures[index]) { res.writeHead(404); res.end(); return; }
  res.setHeader('Content-Type', 'text/html; charset=utf-8'); res.end(fixtures[index].html);
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
let browser;
try {
  browser = await chromium.launch({ channel: 'chromium', headless: true });
  const context = await browser.newContext();
  await context.route('**/*', route => new URL(route.request().url()).hostname === '127.0.0.1' ? route.continue() : route.abort());
  const captured = [];
  for (let index = 0; index < fixtures.length; index++) {
    const page = await context.newPage();
    await page.goto(`${origin}/?case=${index}`);
    const url = 'https://parity.fixture.test/path/page?session=PRIVATE_QUERY';
    const output = await page.evaluate(async ({ origin, url }) => {
      const { snapshotHTML } = await import(`${origin}/snapshot.js`);
      return { rendered_html: document.documentElement.outerHTML, extension_html: snapshotHTML(document, url) };
    }, { origin, url });
    assert(!output.extension_html.includes('PRIVATE_'), `${fixtures[index].name}: private fixture marker leaked`);
    captured.push({ name: fixtures[index].name, stored_html: fixtures[index].html, url, ...output });
    await page.close();
  }
  const input = path.join(temporary, 'fixtures.json');
  await writeFile(input, JSON.stringify(captured));
  const result = await new Promise((resolve, reject) => {
    const child = spawn(path.join(project, '.venv/bin/python'), ['scripts/check_snapshot_parity.py', '--input', input],
      { cwd: project, env: { ...process.env, PYTHONPATH: 'src', PYTHONDONTWRITEBYTECODE: '1' }, stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '', stderr = '';
    child.stdout.on('data', data => { stdout += data; }); child.stderr.on('data', data => { stderr += data; });
    child.on('error', reject);
    child.on('exit', code => code === 0 ? resolve(JSON.parse(stdout)) : reject(new Error(`Parity checker exited: ${stderr}`)));
  });
  result.browser = browser.version(); result.checked_at = new Date().toISOString();
  result.scope = 'six invented fixtures; semantic features/text parity on rendered DOM, not byte HTML identity';
  result.passed = result.cases.filter(item => item.rendered_vs_extension_equal).length;
  result.stored_rendered_drift_cases = result.cases.filter(item => !item.stored_vs_rendered_equal).map(item => item.case);
  await mkdir(path.join(project, 'artifacts/smoke'), { recursive: true });
  await writeFile(path.join(project, 'artifacts/smoke/parity-report.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({ passed: result.passed, total: result.cases.length, stored_rendered_drift_cases: result.stored_rendered_drift_cases }, null, 2));
  assert.equal(result.passed, fixtures.length, 'Rendered DOM parity mismatch; see report');
} finally {
  await browser?.close();
  await new Promise(resolve => server.close(resolve));
  await rm(temporary, { recursive: true, force: true });
}
