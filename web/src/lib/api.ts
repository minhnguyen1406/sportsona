/**
 * Thin typed wrapper around the FastAPI backend.
 *
 * All requests run through `apiFetch`, which:
 *   - prepends PUBLIC_API_BASE_URL
 *   - injects `Authorization: Bearer <access>` from the auth store when present
 *   - parses JSON and surfaces a typed `ApiError` on non-2xx responses
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

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE' | 'PUT';
  /** JSON body — will be stringified and sent with `Content-Type: application/json`. */
  json?: unknown;
  /** Form body — sent with `application/x-www-form-urlencoded`. Used for OAuth2 password flow. */
  form?: Record<string, string>;
  /** Skip the bearer token even if one exists (e.g. login itself). */
  skipAuth?: boolean;
}

async function apiFetch<T>(path: string, opts: RequestOptions = {}): Promise<T> {
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

  const response = await fetch(`${PUBLIC_API_BASE_URL}${path}`, {
    method: opts.method ?? 'GET',
    headers,
    body
  });

  // 204 No Content
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

// --- Auth endpoints ---

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserRead {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  created_at: string;
}

export const authApi = {
  login(email: string, password: string): Promise<TokenResponse> {
    // OAuth2 password flow: form-encoded, "username" field carries the email.
    return apiFetch<TokenResponse>('/api/v1/auth/login', {
      method: 'POST',
      form: { username: email, password },
      skipAuth: true
    });
  },

  register(email: string, username: string, password: string): Promise<UserRead> {
    return apiFetch<UserRead>('/api/v1/auth/register', {
      method: 'POST',
      json: { email, username, password },
      skipAuth: true
    });
  },

  me(): Promise<UserRead> {
    return apiFetch<UserRead>('/api/v1/auth/me');
  },

  refresh(refresh_token: string): Promise<TokenResponse> {
    return apiFetch<TokenResponse>('/api/v1/auth/refresh', {
      method: 'POST',
      json: { refresh_token },
      skipAuth: true
    });
  },

  logout(refresh_token: string): Promise<void> {
    return apiFetch<void>('/api/v1/auth/logout', {
      method: 'POST',
      json: { refresh_token },
      skipAuth: true
    });
  }
};
