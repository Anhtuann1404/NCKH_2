import { assessmentNote, normalizeURL, observedSignalText, OBSERVATION_NOTE, PREPROCESSING_VERSION, statusText, TabState } from './core';
import { snapshotHTML } from './snapshot';

let navigation = crypto.randomUUID();
let revision = 0;
let enabled = false;
let contentAllowed = false;
let pageURL = location.href;
let timer: ReturnType<typeof setTimeout> | undefined;
let banner: HTMLElement | undefined;

function show(state: TabState) {
  if (!enabled || state.navigation_id !== navigation || state.dom_revision !== revision) return;
  if (!banner?.isConnected) {
    banner = document.createElement('div');
    banner.id = 'nckh-phishing-demo-banner';
    const root = banner.attachShadow({ mode: 'closed' });
    const text = document.createElement('div');
    text.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:2147483647;max-width:360px;padding:14px 18px;border-radius:10px;background:#17243b;color:#fff;font:14px/1.5 system-ui;box-shadow:0 4px 20px #0004';
    root.append(text);
    document.documentElement.append(banner);
    (banner as HTMLElement & { statusText?: HTMLElement }).statusText = text;
  }
  const text = (banner as HTMLElement & { statusText?: HTMLElement }).statusText!;
  const observations = observedSignalText(state);
  text.textContent = `DEMO MÔ PHỎNG — ${state.demo_kind === 'synthetic_model' ? 'mô hình học từ dữ liệu hư cấu' : 'chưa nhận diện thật'}\n${statusText(state)}\n${assessmentNote(state)}${observations.length ? '\nTín hiệu quan sát được:\n• ' + observations.join('\n• ') + '\n' + OBSERVATION_NOTE : ''}`;
  text.style.whiteSpace = 'pre-line';
}

async function send(phase: 'url_only' | 'url_content') {
  if (!enabled || (phase === 'url_content' && !contentAllowed)) return;
  try {
    const url = normalizeURL(location.href);
    const html = phase === 'url_content' ? snapshotHTML(document, url) : undefined;
    await chrome.runtime.sendMessage({ type: 'snapshot', navigation_id: navigation, dom_revision: revision, phase, url, ...(html === undefined ? {} : { html }), preprocessing_version: PREPROCESSING_VERSION });
  } catch {
    if (phase === 'url_content') {
      show({ navigation_id: navigation, dom_revision: revision, request_id: '', phase, status: 'unable_to_assess', verdict: 'unable_to_assess', code: 'snapshot_error', mock: true });
      try { await chrome.runtime.sendMessage({ type: 'snapshot_error', navigation_id: navigation }); } catch { /* extension may have reloaded */ }
    }
  }
}

function contentSnapshot() {
  if (!enabled || !contentAllowed) return;
  clearTimeout(timer);
  timer = setTimeout(() => { revision++; void send('url_content'); }, 500);
}

async function configure() {
  try {
    const config = await chrome.runtime.sendMessage({ type: 'get_config' });
    enabled = config.enabled === true; contentAllowed = config.analyzeContent === true;
    clearTimeout(timer); banner?.remove(); banner = undefined;
    navigation = crypto.randomUUID(); revision = 0; pageURL = location.href;
    if (enabled) { void send('url_only'); contentSnapshot(); }
  } catch { enabled = false; }
}

chrome.runtime.onMessage.addListener(message => {
  if (message?.type === 'analysis_state') show(message.state);
  if (message?.type === 'config_changed') void configure();
});
const observer = new MutationObserver(records => {
  if (records.every(record => {
    if ((record.target as Element).id === 'nckh-phishing-demo-banner') return true;
    return record.type === 'childList' && [...record.addedNodes, ...record.removedNodes].every(node => (node as Element).id === 'nckh-phishing-demo-banner');
  })) return;
  contentSnapshot();
});
observer.observe(document.documentElement, { subtree: true, childList: true, characterData: true, attributes: true });
// Poll location only for SPA navigation; no URL/history log is retained.
setInterval(() => {
  if (location.href !== pageURL) { pageURL = location.href; void configure(); }
}, 500);
void configure();
