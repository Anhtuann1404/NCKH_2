import { statusText, TabState } from './core';

const enabled = document.querySelector<HTMLInputElement>('#enabled')!;
const content = document.querySelector<HTMLInputElement>('#content')!;
const token = document.querySelector<HTMLInputElement>('#token')!;
const status = document.querySelector<HTMLElement>('#status')!;
const note = document.querySelector<HTMLElement>('#note')!;

document.querySelector<HTMLElement>('#extension-id')!.textContent = chrome.runtime.id;
async function refresh() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const config = await chrome.storage.local.get({ enabled: false });
  if (!config.enabled) { status.textContent = 'Đã tắt phân tích'; return; }
  if (tab?.id === undefined) { status.textContent = 'Chưa đánh giá được'; return; }
  const saved = await chrome.storage.session.get(`tab:${tab.id}`);
  const state = saved[`tab:${tab.id}`] as TabState | undefined;
  status.textContent = statusText(state);
  note.textContent = state?.code ? `Mã trạng thái: ${state.code}` : (state?.demo_kind === 'synthetic_model' ? 'Mô hình học từ dữ liệu hư cấu; chỉ kiểm thử tích hợp, không xác nhận trang an toàn.' : 'Kết quả hiện tại chỉ dùng kiểm thử luồng, không xác nhận trang an toàn.');
}

void chrome.storage.local.get({ enabled: false, analyzeContent: false, token: '' }).then(config => {
  enabled.checked = config.enabled === true; content.checked = config.analyzeContent === true; token.value = typeof config.token === 'string' ? config.token : '';
  void refresh();
});
document.querySelector<HTMLFormElement>('#settings')!.addEventListener('submit', event => {
  event.preventDefault();
  void chrome.storage.local.set({ enabled: enabled.checked, analyzeContent: content.checked, token: token.value.trim() }).then(() => {
    note.textContent = 'Đã lưu. Nội dung chỉ được gửi đến API trên máy khi bật cho phép.';
    void refresh();
  });
});
chrome.storage.onChanged.addListener(() => { void refresh(); });
