/**
 * Thin typed wrapper around the FastAPI backend.
 *
 * `apiFetch` handles:
 *   - PUBLIC_API_BASE_URL prefix
 *   - Bearer token injection from the auth store
 *   - Automatic refresh + retry on 401 (once)
 *   - JSON / form encoding
 *   - Typed `ApiError` on non-2xx responses
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
  json?: unknown;
  form?: Record<string, string>;
  query?: Record<string, string | number | undefined | null>;
  /** Skip the bearer token even if one exists (e.g. login itself). */
  skipAuth?: boolean;
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

async function apiFetch<T>(path: string, opts: RequestOptions = {}): Promise<T> {
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

// ---------------------------------------------------------------------------
// Shared types
// ---------------------------------------------------------------------------

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
  is_verified: boolean;
  created_at: string;
}

export interface DriverResponse {
  driver_id: string;
  given_name: string;
  family_name: string;
  date_of_birth: string | null;
  nationality: string | null;
}

export interface ConstructorResponse {
  constructor_id: string;
  name: string;
  nationality: string | null;
}

export interface CircuitResponse {
  circuit_id: string;
  name: string;
  locality: string | null;
  country: string | null;
}

export interface SeasonResponse {
  year: number;
}

export interface RaceResponse {
  id: number;
  season: number;
  round: number;
  name: string;
  date: string;
  time: string | null;
  circuit: CircuitResponse;
}

export interface RaceResultResponse {
  id: number;
  position: number | null;
  position_text: string | null;
  grid_position: number | null;
  points: number;
  laps: number | null;
  time: string | null;
  fastest_lap_time: string | null;
  fastest_lap_rank: number | null;
  status: string | null;
  driver: DriverResponse;
  constructor: ConstructorResponse;
}

export interface QualifyingResultResponse {
  id: number;
  position: number | null;
  q1_time: string | null;
  q2_time: string | null;
  q3_time: string | null;
  driver: DriverResponse;
  constructor: ConstructorResponse;
}

export interface DriverStandingResponse {
  id: number;
  season: number;
  round: number;
  position: number;
  points: number;
  wins: number;
  driver: DriverResponse;
}

export interface ConstructorStandingResponse {
  id: number;
  season: number;
  round: number;
  position: number;
  points: number;
  wins: number;
  constructor: ConstructorResponse;
}

export interface CurrentStanding {
  season: number;
  round: number;
  position: number;
  points: number;
  wins: number;
}

export interface DashboardRaceResult {
  race_id: number;
  race_name: string;
  season: number;
  round: number;
  date: string;
  position: number | null;
  points: number;
}

export interface FollowedDriverDashboard {
  driver: DriverResponse;
  current_standing: CurrentStanding | null;
  recent_results: DashboardRaceResult[];
}

export interface FollowedConstructorDashboard {
  constructor: ConstructorResponse;
  current_standing: CurrentStanding | null;
}

export interface DashboardResponse {
  user: UserRead;
  followed_drivers: FollowedDriverDashboard[];
  followed_constructors: FollowedConstructorDashboard[];
  next_race: RaceResponse | null;
}

export interface AskResponse {
  question: string;
  sql: string;
  reasoning: string;
  columns: string[];
  rows: unknown[][];
  row_count: number;
  truncated: boolean;
  model: string;
  llm_latency_ms: number;
  db_latency_ms: number;
  cache_read_tokens: number;
}

// ---------------------------------------------------------------------------
// Endpoint groups
// ---------------------------------------------------------------------------

export const authApi = {
  login(email: string, password: string): Promise<TokenResponse> {
    return apiFetch('/api/v1/auth/login', {
      method: 'POST',
      form: { username: email, password },
      skipAuth: true
    });
  },
  register(email: string, username: string, password: string): Promise<UserRead> {
    return apiFetch('/api/v1/auth/register', {
      method: 'POST',
      json: { email, username, password },
      skipAuth: true
    });
  },
  me(): Promise<UserRead> {
    return apiFetch('/api/v1/auth/me');
  },
  logout(refresh_token: string): Promise<void> {
    return apiFetch('/api/v1/auth/logout', {
      method: 'POST',
      json: { refresh_token },
      skipAuth: true
    });
  },
  forgotPassword(email: string): Promise<void> {
    return apiFetch('/api/v1/auth/password/forgot', {
      method: 'POST',
      json: { email },
      skipAuth: true
    });
  }
};

export const usersApi = {
  update(payload: {
    username?: string;
    current_password?: string;
    new_password?: string;
  }): Promise<UserRead> {
    return apiFetch('/api/v1/users/me', { method: 'PATCH', json: payload });
  },

  dashboard(): Promise<DashboardResponse> {
    return apiFetch('/api/v1/users/me/dashboard');
  },

  listFollowedDrivers(): Promise<DriverResponse[]> {
    return apiFetch('/api/v1/users/me/followed-drivers');
  },
  followDriver(driverId: string): Promise<void> {
    return apiFetch(`/api/v1/users/me/followed-drivers/${driverId}`, { method: 'POST' });
  },
  unfollowDriver(driverId: string): Promise<void> {
    return apiFetch(`/api/v1/users/me/followed-drivers/${driverId}`, { method: 'DELETE' });
  },

  listFollowedConstructors(): Promise<ConstructorResponse[]> {
    return apiFetch('/api/v1/users/me/followed-constructors');
  },
  followConstructor(constructorId: string): Promise<void> {
    return apiFetch(`/api/v1/users/me/followed-constructors/${constructorId}`, {
      method: 'POST'
    });
  },
  unfollowConstructor(constructorId: string): Promise<void> {
    return apiFetch(`/api/v1/users/me/followed-constructors/${constructorId}`, {
      method: 'DELETE'
    });
  }
};

export const f1Api = {
  listSeasons(): Promise<SeasonResponse[]> {
    return apiFetch('/api/v1/f1/seasons');
  },
  listRacesBySeason(year: number): Promise<RaceResponse[]> {
    return apiFetch(`/api/v1/f1/seasons/${year}/races`);
  },
  driverStandings(year: number, round?: number): Promise<DriverStandingResponse[]> {
    return apiFetch(`/api/v1/f1/seasons/${year}/standings/drivers`, { query: { round } });
  },
  constructorStandings(
    year: number,
    round?: number
  ): Promise<ConstructorStandingResponse[]> {
    return apiFetch(`/api/v1/f1/seasons/${year}/standings/constructors`, {
      query: { round }
    });
  },

  listDrivers(opts: {
    search?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<DriverResponse[]> {
    return apiFetch('/api/v1/f1/drivers', { query: opts });
  },
  getDriver(id: string): Promise<DriverResponse> {
    return apiFetch(`/api/v1/f1/drivers/${id}`);
  },

  listConstructors(opts: { limit?: number; offset?: number } = {}): Promise<ConstructorResponse[]> {
    return apiFetch('/api/v1/f1/constructors', { query: opts });
  },
  getConstructor(id: string): Promise<ConstructorResponse> {
    return apiFetch(`/api/v1/f1/constructors/${id}`);
  },

  listCircuits(opts: { limit?: number; offset?: number } = {}): Promise<CircuitResponse[]> {
    return apiFetch('/api/v1/f1/circuits', { query: opts });
  },
  getCircuit(id: string): Promise<CircuitResponse> {
    return apiFetch(`/api/v1/f1/circuits/${id}`);
  },

  getRace(id: number): Promise<RaceResponse> {
    return apiFetch(`/api/v1/f1/races/${id}`);
  },
  getRaceResults(id: number): Promise<RaceResultResponse[]> {
    return apiFetch(`/api/v1/f1/races/${id}/results`);
  },
  getQualifyingResults(id: number): Promise<QualifyingResultResponse[]> {
    return apiFetch(`/api/v1/f1/races/${id}/qualifying`);
  }
};

export const askApi = {
  ask(question: string): Promise<AskResponse> {
    return apiFetch('/api/v1/ask', {
      method: 'POST',
      json: { question },
      skipAuth: true
    });
  }
};

export interface StatOfDayResponse {
  date: string;
  question: string;
  sql: string;
  columns: string[];
  rows: unknown[][];
  narration: string;
  model: string;
  created_at: string;
}

export const statApi = {
  today(): Promise<StatOfDayResponse> {
    return apiFetch('/api/v1/stat-of-the-day');
  }
};
