import { assessmentNote, normalizeURL, observedSignalText, OBSERVATION_NOTE, PREPROCESSING_VERSION, statusText, TabState } from './core';
import { snapshotHTML } from './snapshot';

let navigation = crypto.randomUUID();
let revision = 0;
let enabled = false;
let contentAllowed = false;
let showBanner = true;
let pageURL = location.href;
let timer: ReturnType<typeof setTimeout> | undefined;
let bannerTimer: ReturnType<typeof setTimeout> | undefined;
let banner: HTMLElement | undefined;
let bannerParts: { card: HTMLElement; mode: HTMLElement; title: HTMLElement; note: HTMLElement; signals: HTMLElement } | undefined;

function dismissBanner() {
  clearTimeout(bannerTimer);
  banner?.remove();
  banner = undefined;
  bannerParts = undefined;
}

function show(state: TabState) {
  if (!enabled || !showBanner || state.navigation_id !== navigation || state.dom_revision !== revision) return;
  if (!banner?.isConnected) {
    banner = document.createElement('div');
    banner.id = 'nckh-phishing-demo-banner';
    const root = banner.attachShadow({ mode: 'closed' });
    const style = document.createElement('style');
    style.textContent = `
      :host { all: initial; position: fixed; right: 16px; bottom: 16px; z-index: 2147483647; width: min(360px, calc(100vw - 32px)); font: 13px/1.45 system-ui, sans-serif; }
      .card { --accent: #8ca4c5; padding: 14px 16px; border: 1px solid #ffffffd9; border-left: 4px solid var(--accent); border-radius: 20px; background: #f7f9fce8; color: #17243b; box-shadow: 0 14px 34px #17243b3d, inset 0 1px #fff; backdrop-filter: blur(20px) saturate(160%); -webkit-backdrop-filter: blur(20px) saturate(160%); }
      .card[data-tone="warning"] { --accent: #ff7c87; }
      .card[data-tone="clear"] { --accent: #84b9ff; }
      .card[data-tone="unknown"] { --accent: #ffd27a; }
      .top { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
      .mode { color: #526076; font-size: 10px; font-weight: 800; letter-spacing: .06em; }
      button { width: 24px; height: 24px; padding: 0; border: 0; border-radius: 50%; background: transparent; color: #526076; font: 20px/1 system-ui; cursor: pointer; }
      button:hover, button:focus-visible { background: #17243b15; outline: none; }
      .title { display: block; margin-top: 5px; font-size: 16px; line-height: 1.3; }
      .note { margin: 5px 0 0; color: #526076; font-size: 11px; }
      .signals { margin-top: 10px; padding-top: 9px; border-top: 1px solid #17243b24; font-size: 11px; }
      .signals[hidden] { display: none; }
      .signals ul { margin: 5px 0; padding-left: 18px; }
      .signals p { margin: 6px 0 0; color: #526076; }
      @media (max-width: 420px) { :host { right: 12px; bottom: 12px; width: calc(100vw - 24px); } }
    `;
    const card = document.createElement('section'); card.className = 'card'; card.setAttribute('role', 'status');
    const top = document.createElement('div'); top.className = 'top';
    const mode = document.createElement('span'); mode.className = 'mode';
    const close = document.createElement('button'); close.type = 'button'; close.setAttribute('aria-label', 'Đóng thông báo'); close.textContent = '×';
    close.addEventListener('click', dismissBanner);
    top.append(mode, close);
    const title = document.createElement('strong'); title.className = 'title';
    const note = document.createElement('p'); note.className = 'note';
    const signals = document.createElement('div'); signals.className = 'signals';
    card.append(top, title, note, signals);
    root.append(style, card);
    document.documentElement.append(banner);
    bannerParts = { card, mode, title, note, signals };
  }
  const parts = bannerParts!;
  const observations = observedSignalText(state);
  parts.card.dataset.tone = state.status === 'pending' ? 'pending'
    : state.status === 'unable_to_assess' || state.verdict === 'unable_to_assess' ? 'unknown'
      : state.verdict === 'warning' ? 'warning' : state.verdict === 'no_indication' ? 'clear' : 'pending';
  parts.mode.textContent = `DEMO MÔ PHỎNG · ${state.demo_kind === 'synthetic_model' ? 'DỮ LIỆU HƯ CẤU' : 'CHƯA NHẬN DIỆN THẬT'}`;
  parts.title.textContent = statusText(state);
  parts.note.textContent = assessmentNote(state);
  parts.signals.replaceChildren();
  parts.signals.hidden = !observations.length;
  if (observations.length) {
    const heading = document.createElement('strong'); heading.textContent = 'Tín hiệu quan sát được';
    const list = document.createElement('ul');
    for (const observation of observations) { const item = document.createElement('li'); item.textContent = observation; list.append(item); }
    const caution = document.createElement('p'); caution.textContent = OBSERVATION_NOTE;
    parts.signals.append(heading, list, caution);
  }
  banner!.dataset.phase = state.phase;
  clearTimeout(bannerTimer);
  bannerTimer = setTimeout(dismissBanner, state.verdict === 'warning' ? 8000 : 4000);
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
    enabled = config.enabled === true; contentAllowed = config.analyzeContent === true; showBanner = config.showBanner !== false;
    clearTimeout(timer); dismissBanner();
    navigation = crypto.randomUUID(); revision = 0; pageURL = location.href;
    if (enabled) { void send('url_only'); contentSnapshot(); }
  } catch { enabled = false; }
}

chrome.runtime.onMessage.addListener(message => {
  if (message?.type === 'analysis_state') show(message.state);
  if (message?.type === 'config_changed') void configure();
});
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== 'local' || !('showBanner' in changes)) return;
  showBanner = changes.showBanner.newValue !== false;
  if (!showBanner) dismissBanner();
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
