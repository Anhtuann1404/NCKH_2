import { analyzeWithRetry, AnalyzeRequest, APIError, isCurrent, PREPROCESSING_VERSION, TabState } from './core';

interface Settings { enabled: boolean; analyzeContent: boolean; token: string }
const defaults: Settings = { enabled: false, analyzeContent: false, token: '' };
const states = new Map<number, TabState>();
const jobs = new Map<number, { abort: AbortController; done: Promise<void> }>();
const key = (id: number) => `tab:${id}`;
const initialized = (async () => {
  await chrome.storage.local.setAccessLevel({ accessLevel: 'TRUSTED_CONTEXTS' });
  await chrome.storage.session.setAccessLevel({ accessLevel: 'TRUSTED_CONTEXTS' });
  const saved = await chrome.storage.session.get(null);
  for (const [name, value] of Object.entries(saved)) {
    if (!name.startsWith('tab:')) continue;
    const state = value as TabState;
    if (state.status === 'pending') { state.status = 'unable_to_assess'; state.verdict = 'unable_to_assess'; state.code = 'worker_restarted'; }
    states.set(Number(name.slice(4)), state);
    await chrome.storage.session.set({ [name]: state });
  }
})();

async function settings(): Promise<Settings> {
  return { ...defaults, ...await chrome.storage.local.get(defaults) } as Settings;
}

async function publish(tabId: number, state: TabState): Promise<void> {
  states.set(tabId, state);
  await chrome.storage.session.set({ [key(tabId)]: state });
  if (states.get(tabId) !== state) return;
  try { await chrome.tabs.sendMessage(tabId, { type: 'analysis_state', state }); } catch { /* tab may already be closed */ }
}

function fail(tabId: number, request: AnalyzeRequest, code: string) {
  if (isCurrent(states.get(tabId), request)) void publish(tabId, { ...states.get(tabId)!, status: 'unable_to_assess', verdict: 'unable_to_assess', code });
}

async function acceptSnapshot(message: Record<string, unknown>, sender: chrome.runtime.MessageSender) {
  await initialized;
  const tabId = sender.tab?.id;
  if (tabId === undefined || sender.frameId !== 0 || !sender.documentId) return { accepted: false };
  const currentFrame = await chrome.webNavigation.getFrame({ tabId, frameId: 0 });
  if (!currentFrame || currentFrame.documentId !== sender.documentId) return { accepted: false };
  const config = await settings();
  if (!config.enabled || (message.phase === 'url_content' && !config.analyzeContent)) return { accepted: false };
  if (typeof message.navigation_id !== 'string' || !/^[0-9a-f-]{36}$/iu.test(message.navigation_id) || typeof message.dom_revision !== 'number' || !Number.isSafeInteger(message.dom_revision) || message.dom_revision < 0 || typeof message.url !== 'string' || !['url_only', 'url_content'].includes(String(message.phase))) return { accepted: false };
  if (message.phase === 'url_content' && (typeof message.html !== 'string' || !message.html.length || message.html.length > 1_000_000)) return { accepted: false };
  const old = states.get(tabId);
  if (old?.navigation_id === message.navigation_id && old.dom_revision >= message.dom_revision) return { accepted: false };
  const request: AnalyzeRequest = {
    request_id: crypto.randomUUID(), navigation_id: message.navigation_id, dom_revision: message.dom_revision,
    phase: message.phase as AnalyzeRequest['phase'], url: message.url,
    preprocessing_version: PREPROCESSING_VERSION, capture_mode: message.phase === 'url_content' ? 'rendered_dom' : 'url_only',
  };
  if (request.phase === 'url_content') request.html = message.html as string;
  const previous = jobs.get(tabId);
  previous?.abort.abort();
  const abort = new AbortController();
  // Persist only IDs and presentation state; never URL, HTML, or token.
  const cleanState: TabState = { navigation_id: request.navigation_id, dom_revision: request.dom_revision, request_id: request.request_id, phase: request.phase, status: 'pending', verdict: null, mock: true };
  await publish(tabId, cleanState);
  const done = (async () => {
    await previous?.done;
    if (!isCurrent(states.get(tabId), request) || abort.signal.aborted) return;
    if (!config.token) return fail(tabId, request, 'missing_token');
    try {
      const result = await analyzeWithRetry(request, config.token, {
        signal: abort.signal,
        onAttempt: attempt => {
          const current = isCurrent(states.get(tabId), request);
          request.request_id = attempt.request_id;
          if (current) void publish(tabId, { ...cleanState, request_id: attempt.request_id });
        },
      });
      if (!isCurrent(states.get(tabId), result.request) || abort.signal.aborted || !(await settings()).enabled) return;
      await publish(tabId, { ...cleanState, request_id: result.request.request_id, status: result.response.status === 'completed' ? 'completed' : 'unable_to_assess', verdict: result.response.verdict, mock: result.response.model.model_id.startsWith('mock-only-'), demo_kind: result.response.model.model_id.startsWith('mock-only-') ? 'mock' : 'synthetic_model', timing_ms: { ...result.response.timing_ms, client_roundtrip: result.elapsedMs } });
    } catch (error) {
      if (!abort.signal.aborted) fail(tabId, request, error instanceof APIError ? error.code : 'network_error');
    }
  })();
  jobs.set(tabId, { abort, done });
  void done.finally(() => { if (jobs.get(tabId)?.abort === abort) jobs.delete(tabId); });
  return { accepted: true };
}

chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (message?.type === 'get_config') {
    void initialized.then(settings).then(config => respond({ enabled: config.enabled, analyzeContent: config.analyzeContent }));
  } else if (message?.type === 'snapshot') {
    void acceptSnapshot(message, sender).then(respond).catch(() => respond({ accepted: false }));
  } else if (message?.type === 'snapshot_error' && sender.tab?.id !== undefined) {
    const id = sender.tab.id;
    void initialized.then(async () => {
      const frame = await chrome.webNavigation.getFrame({ tabId: id, frameId: 0 });
      const state = states.get(id);
      if (state && sender.frameId === 0 && frame?.documentId === sender.documentId && state.navigation_id === message.navigation_id) {
        jobs.get(id)?.abort.abort();
        await publish(id, { ...state, status: 'unable_to_assess', verdict: 'unable_to_assess', code: 'snapshot_too_large' });
      }
      respond({ accepted: true });
    });
  } else return false;
  return true;
});

chrome.webNavigation.onCommitted.addListener(details => {
  if (details.frameId !== 0) return;
  jobs.get(details.tabId)?.abort.abort();
  states.delete(details.tabId);
  void chrome.storage.session.remove(key(details.tabId));
});
chrome.tabs.onRemoved.addListener(tabId => {
  jobs.get(tabId)?.abort.abort(); states.delete(tabId);
  void chrome.storage.session.remove(key(tabId));
});
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== 'local' || !['enabled', 'analyzeContent', 'token'].some(name => name in changes)) return;
  void initialized.then(async () => {
    for (const job of jobs.values()) job.abort.abort();
    states.clear();
    await chrome.storage.session.clear();
    for (const tab of await chrome.tabs.query({})) if (tab.id !== undefined) {
      try { await chrome.tabs.sendMessage(tab.id, { type: 'config_changed' }); } catch { /* restricted/closed tab */ }
    }
  });
});
