export const API_BASE = 'http://127.0.0.1:8765';
export const PREPROCESSING_VERSION = 'snapshot-dev-0';
export type Phase = 'url_only' | 'url_content';
export type Verdict = 'warning' | 'no_indication' | 'unable_to_assess';
export interface AnalyzeRequest {
  request_id: string; navigation_id: string; dom_revision: number; phase: Phase;
  url: string; preprocessing_version: string; capture_mode: 'url_only' | 'rendered_dom'; html?: string;
}
export interface AnalyzeResponse {
  request_id: string; navigation_id: string; dom_revision: number; phase: Phase;
  status: 'completed' | 'insufficient_content'; verdict: Verdict;
  score: number | null; threshold: number | null;
  model: { model_id: string; preprocessing_version: string; variant: string };
  limitations: string[];
  timing_ms?: { preprocess: number; extract: number; infer: number; server_total: number };
}
export interface TabState {
  navigation_id: string; dom_revision: number; phase: Phase; request_id: string;
  status: 'pending' | 'completed' | 'unable_to_assess'; verdict: Verdict | null;
  code?: string; mock: boolean; demo_kind?: 'mock' | 'synthetic_model';
  timing_ms?: { client_roundtrip: number; preprocess?: number; extract?: number; infer?: number; server_total?: number };
}
export class APIError extends Error {
  constructor(public code: string, public retryable = false) { super(code); }
}

export function isCurrent(state: TabState | undefined, request: Pick<AnalyzeRequest, 'navigation_id' | 'dom_revision' | 'phase' | 'request_id'>): boolean {
  return !!state && state.navigation_id === request.navigation_id && state.dom_revision === request.dom_revision && state.phase === request.phase && state.request_id === request.request_id;
}

export function normalizeURL(raw: string, base?: string): string {
  if (/[\s\u0000-\u001f\u007f\\]/u.test(raw) || /%(?![\da-f]{2})/iu.test(raw)) throw new APIError('invalid_url');
  const url = base ? new URL(raw, base) : new URL(raw);
  if (!['http:', 'https:'].includes(url.protocol)) throw new APIError('invalid_url');
  url.username = ''; url.password = ''; url.hash = '';
  url.hostname = url.hostname.replace(/\.+$/u, '');
  const keys = [...url.searchParams.keys()];
  url.search = '';
  for (const key of keys) url.searchParams.append(key, '_redacted_');
  const normalized = url.href;
  if (normalized.length > 8192) throw new APIError('invalid_url');
  return normalized;
}

export function validateResponse(value: unknown, request: AnalyzeRequest): AnalyzeResponse {
  if (!value || typeof value !== 'object') throw new APIError('invalid_response');
  const response = value as AnalyzeResponse;
  if (!isCurrent({ ...request, status: 'pending', verdict: null, mock: true }, response)) throw new APIError('stale_response');
  const mock = response.model?.model_id?.startsWith('mock-only-') && response.limitations?.includes('mock_response_not_model_result');
  const synthetic = response.model?.model_id?.startsWith('synthetic-demo-') && response.limitations?.includes('synthetic_training_only') && response.limitations?.includes('not_research_evidence') && response.model.variant === (request.phase === 'url_only' ? 'M0' : 'M3');
  if ((!mock && !synthetic) || response.model?.preprocessing_version !== PREPROCESSING_VERSION) throw new APIError('unsupported_bundle');
  if (response.status === 'insufficient_content') {
    if (response.verdict !== 'unable_to_assess' || response.score !== null || response.threshold !== null) throw new APIError('invalid_response');
  } else if (response.status === 'completed') {
    if (typeof response.score !== 'number' || !Number.isFinite(response.score) || response.score < 0 || response.score > 1 || typeof response.threshold !== 'number' || !Number.isFinite(response.threshold) || response.threshold < 0 || response.threshold > 1 || response.verdict !== (response.score >= response.threshold ? 'warning' : 'no_indication')) throw new APIError('invalid_response');
  } else throw new APIError('invalid_response');
  if (response.timing_ms && Object.values(response.timing_ms).some(value => typeof value !== 'number' || !Number.isFinite(value) || value < 0)) throw new APIError('invalid_response');
  return response;
}

export async function analyzeWithRetry(
  initial: AnalyzeRequest, token: string,
  options: { fetcher?: typeof fetch; timeoutMs?: number; signal?: AbortSignal; onAttempt?: (request: AnalyzeRequest) => void; retryDelayMs?: number } = {},
): Promise<{ response: AnalyzeResponse; request: AnalyzeRequest; elapsedMs: number }> {
  const started = performance.now();
  const fetcher = options.fetcher ?? fetch;
  let request = initial;
  for (let attempt = 0; attempt < 2; attempt++) {
    if (options.signal?.aborted) throw new APIError('cancelled');
    if (attempt) request = { ...request, request_id: crypto.randomUUID() };
    options.onAttempt?.(request);
    const controller = new AbortController();
    const onAbort = () => controller.abort();
    options.signal?.addEventListener('abort', onAbort, { once: true });
    const timer = setTimeout(() => controller.abort(), options.timeoutMs ?? 5000);
    let error: APIError;
    try {
      const result = await fetcher(`${API_BASE}/v1/analyze`, {
        method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(request), signal: controller.signal, cache: 'no-store',
      });
      if (!result.ok) throw new APIError(`http_${result.status}`, [429, 504].includes(result.status));
      const response = validateResponse(await result.json(), request);
      return { response, request, elapsedMs: performance.now() - started };
    } catch (caught) {
      if (options.signal?.aborted) throw new APIError('cancelled');
      error = caught instanceof APIError ? caught : new APIError(controller.signal.aborted ? 'timeout' : 'network_error', true);
    } finally {
      clearTimeout(timer);
      options.signal?.removeEventListener('abort', onAbort);
    }
    if (!error.retryable || attempt) throw error;
    await new Promise(resolve => setTimeout(resolve, options.retryDelayMs ?? 500));
  }
  throw new APIError('network_error');
}

export function statusText(state?: TabState): string {
  if (!state) return 'Chưa đánh giá được';
  if (state.status === 'pending') return 'Đang phân tích mô phỏng…';
  if (state.status === 'unable_to_assess' || state.verdict === 'unable_to_assess') return 'Chưa đánh giá được';
  const label = state.verdict === 'warning' ? 'Có dấu hiệu phishing' : 'Chưa phát hiện dấu hiệu phishing';
  return state.phase === 'url_only' ? `${label} — URL sơ bộ` : label;
}
