/** Minimal typed HTTP client for the ACEDRA API. Tokens live in sessionStorage (cleared when the tab closes). */
const BASE = '/api/v1';

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.status = status; }
}

const store = {
  get access() { try { return sessionStorage.getItem('acedra.access'); } catch { return null; } },
  get refresh() { try { return sessionStorage.getItem('acedra.refresh'); } catch { return null; } },
  set(access: string, refresh: string) { try { sessionStorage.setItem('acedra.access', access); sessionStorage.setItem('acedra.refresh', refresh); } catch { /* ignore */ } },
  clear() { try { sessionStorage.removeItem('acedra.access'); sessionStorage.removeItem('acedra.refresh'); } catch { /* ignore */ } },
};
export const tokens = store;

let onUnauthorized: () => void = () => {};
export function setUnauthorizedHandler(fn: () => void) { onUnauthorized = fn; }

export type Params = Record<string, string | number | boolean | undefined | null>;

function qs(params?: Params) {
  if (!params) return '';
  const p = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '');
  return p.length ? '?' + new URLSearchParams(p.map(([k, v]) => [k, String(v)])).toString() : '';
}

let refreshing: Promise<boolean> | null = null;
async function tryRefresh(): Promise<boolean> {
  const rt = store.refresh;
  if (!rt) return false;
  refreshing ??= fetch(`${BASE}/auth/refresh`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: rt }),
  }).then(async (r) => {
    if (!r.ok) return false;
    const d: { access_token: string; refresh_token: string } = await r.json();
    store.set(d.access_token, d.refresh_token);
    return true;
  }).catch(() => false).finally(() => { setTimeout(() => { refreshing = null; }, 0); });
  return refreshing;
}

async function request<T>(method: string, path: string, body?: unknown, params?: Params, retry = true): Promise<T> {
  const headers: Record<string, string> = {};
  const isForm = body instanceof FormData;
  if (body !== undefined && !isForm) headers['Content-Type'] = 'application/json';
  if (store.access) headers.Authorization = `Bearer ${store.access}`;
  const res = await fetch(`${BASE}${path}${qs(params)}`, {
    method, headers, body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
  });
  if (res.status === 401 && retry && store.refresh && !path.startsWith('/auth/')) {
    if (await tryRefresh()) return request<T>(method, path, body, params, false);
  }
  if (res.status === 401 && !path.startsWith('/auth/login') && !path.startsWith('/auth/invitations')) {
    store.clear();
    onUnauthorized();
  }
  const ct = res.headers.get('content-type') || '';
  const data: unknown = ct.includes('application/json') ? await res.json() : await res.text();
  if (!res.ok) throw new ApiError(errorDetail(data), res.status);
  return data as T;
}

/** The server's error message (`detail`, else `message`), or a generic fallback. */
function errorDetail(data: unknown): string {
  if (typeof data === 'string' && data) return data;
  if (data && typeof data === 'object') {
    const { detail, message } = data as { detail?: unknown; message?: unknown };
    if (typeof detail === 'string') return detail;
    if (typeof message === 'string') return message;
  }
  return 'Something went wrong. Try again.';
}

/** A readable message for anything caught from an API call or other async work. */
export function errorMessage(e: unknown, fallback = 'Something went wrong. Try again.'): string {
  return e instanceof Error && e.message ? e.message : fallback;
}

/** Typed HTTP verbs. Pass the expected response type, e.g. `api.post<Recommendation>(...)`. */
export const api = {
  get: <T = unknown>(path: string, params?: Params) => request<T>('GET', path, undefined, params),
  post: <T = unknown>(path: string, body?: unknown, params?: Params) => request<T>('POST', path, body ?? {}, params),
  put: <T = unknown>(path: string, body?: unknown) => request<T>('PUT', path, body ?? {}),
  patch: <T = unknown>(path: string, body?: unknown) => request<T>('PATCH', path, body ?? {}),
  del: <T = unknown>(path: string) => request<T>('DELETE', path),
  async download(path: string, filename: string) {
    const res = await fetch(`${BASE}${path}`, { headers: store.access ? { Authorization: `Bearer ${store.access}` } : {} });
    if (!res.ok) throw new ApiError('Download failed', res.status);
    const url = URL.createObjectURL(await res.blob());
    const a = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  },
};
