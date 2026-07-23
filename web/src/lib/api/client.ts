/**
 * Shared HTTP client for the FastAPI backend.
 *
 * `apiFetch` handles:
 *   - PUBLIC_API_BASE_URL prefix
 *   - Bearer token injection from the auth store
 *   - Automatic refresh + retry on 401 (once)
 *   - JSON / form encoding
 *   - Typed `ApiError` on non-2xx responses
 *
 * Per-domain endpoint groups (f1, ask, recap, …) live in sibling files and
 * all build on `apiFetch` from here. This is the frontend mirror of the
 * backend `core/` layer: one shared foundation, domain modules on top.
 */

import { PUBLIC_API_BASE_URL } from '$env/static/public';
import { auth } from '$lib/stores/auth.svelte';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
    public readonly raw?: unknown
  ) {
    super(detail);
  }
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE' | 'PUT';
  json?: unknown;
  form?: Record<string, string>;
  query?: Record<string, string | number | undefined | null>;
  /** Skip the bearer token even if one exists (e.g. login itself). */
  skipAuth?: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

function buildQueryString(query: RequestOptions['query']): string {
  if (!query) return '';
  const entries = Object.entries(query).filter(
    ([, v]) => v !== undefined && v !== null && v !== ''
  );
  if (entries.length === 0) return '';
  const params = new URLSearchParams();
  for (const [k, v] of entries) params.set(k, String(v));
  return `?${params.toString()}`;
}

/** Single in-flight refresh promise so concurrent 401s only refresh once. */
let refreshInFlight: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  if (!auth.refreshToken) return false;
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    try {
      const tokens = await rawFetch<TokenResponse>('/api/v1/auth/refresh', {
        method: 'POST',
        json: { refresh_token: auth.refreshToken },
        skipAuth: true
      });
      auth.setTokens(tokens);
      return true;
    } catch {
      auth.clear();
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

/** The actual fetch — split out so refresh itself can call it without recursing. */
async function rawFetch<T>(path: string, opts: RequestOptions): Promise<T> {
  const headers: Record<string, string> = {};
  let body: BodyInit | undefined;

  if (opts.json !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(opts.json);
  } else if (opts.form) {
    headers['Content-Type'] = 'application/x-www-form-urlencoded';
    body = new URLSearchParams(opts.form).toString();
  }

  if (!opts.skipAuth && auth.accessToken) {
    headers['Authorization'] = `Bearer ${auth.accessToken}`;
  }

  const response = await fetch(
    `${PUBLIC_API_BASE_URL}${path}${buildQueryString(opts.query)}`,
    { method: opts.method ?? 'GET', headers, body }
  );

  if (response.status === 204) {
    return undefined as T;
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const detail =
      (payload && typeof payload === 'object' && 'detail' in payload && typeof payload.detail === 'string'
        ? payload.detail
        : null) ?? `Request failed with status ${response.status}`;
    throw new ApiError(response.status, detail, payload);
  }

  return payload as T;
}

export async function apiFetch<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  try {
    return await rawFetch<T>(path, opts);
  } catch (err) {
    // Auto-refresh once on 401 if we have a refresh token. Any other error
    // bubbles up unchanged.
    if (
      err instanceof ApiError &&
      err.status === 401 &&
      !opts.skipAuth &&
      auth.refreshToken
    ) {
      const refreshed = await tryRefresh();
      if (refreshed) {
        return rawFetch<T>(path, opts);
      }
    }
    throw err;
  }
}
