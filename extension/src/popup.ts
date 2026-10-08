import { assessmentNote, observedSignalText, OBSERVATION_NOTE, statusText, TabState } from './core';

const enabled = document.querySelector<HTMLInputElement>('#enabled')!;
const content = document.querySelector<HTMLInputElement>('#content')!;
const token = document.querySelector<HTMLInputElement>('#token')!;
const status = document.querySelector<HTMLElement>('#status')!;
const note = document.querySelector<HTMLElement>('#note')!;
const signals = document.querySelector<HTMLElement>('#signals')!;
const result = document.querySelector<HTMLElement>('#result')!;
const saveStatus = document.querySelector<HTMLElement>('#save-status')!;

document.querySelector<HTMLElement>('#extension-id')!.textContent = chrome.runtime.id;
async function refresh() {
  signals.textContent = '';
  signals.hidden = true;
  result.dataset.tone = 'idle';
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const config = await chrome.storage.local.get({ enabled: false });
  if (!config.enabled) { status.textContent = 'Đã tắt phân tích'; note.textContent = 'Bật demo để bắt đầu đánh giá trang.'; return; }
  if (tab?.id === undefined) { status.textContent = 'Chưa đánh giá được'; note.textContent = 'Chưa có trang để phân tích.'; result.dataset.tone = 'unknown'; return; }
  const saved = await chrome.storage.session.get(`tab:${tab.id}`);
  const state = saved[`tab:${tab.id}`] as TabState | undefined;
  status.textContent = statusText(state);
  note.textContent = assessmentNote(state);
  result.dataset.tone = state?.status === 'pending' ? 'pending'
    : state?.status === 'unable_to_assess' || state?.verdict === 'unable_to_assess' ? 'unknown'
      : state?.verdict === 'warning' ? 'warning' : state?.verdict === 'no_indication' ? 'clear' : 'idle';
  const observations = observedSignalText(state);
  if (observations.length) {
    signals.hidden = false;
    const heading = document.createElement('strong'); heading.textContent = 'Tín hiệu quan sát được';
    const list = document.createElement('ul');
    for (const observation of observations) { const item = document.createElement('li'); item.textContent = observation; list.append(item); }
    const caution = document.createElement('p'); caution.textContent = OBSERVATION_NOTE;
    signals.append(heading, list, caution);
  }
}

void chrome.storage.local.get({ enabled: false, analyzeContent: false, token: '' }).then(config => {
  enabled.checked = config.enabled === true; content.checked = config.analyzeContent === true; token.value = typeof config.token === 'string' ? config.token : '';
  void refresh();
});
document.querySelector<HTMLFormElement>('#settings')!.addEventListener('submit', event => {
  event.preventDefault();
  void chrome.storage.local.set({ enabled: enabled.checked, analyzeContent: content.checked, token: token.value.trim() }).then(() => {
    saveStatus.textContent = 'Đã lưu thiết lập.';
    void refresh();
  });
});
chrome.storage.onChanged.addListener(() => { void refresh(); });
