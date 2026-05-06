/**
 * Reactive auth store using Svelte 5 runes.
 *
 * Tokens persist to localStorage so a page refresh keeps the user logged in.
 * The `user` profile is loaded lazily on demand (e.g. by the layout when
 * `accessToken` becomes non-null).
 */

import { browser } from '$app/environment';
import type { TokenResponse, UserRead } from '$lib/api';

const ACCESS_KEY = 'sportsona.access_token';
const REFRESH_KEY = 'sportsona.refresh_token';

function readStorage(key: string): string | null {
  if (!browser) return null;
  return localStorage.getItem(key);
}

function writeStorage(key: string, value: string | null) {
  if (!browser) return;
  if (value === null) localStorage.removeItem(key);
  else localStorage.setItem(key, value);
}

class AuthStore {
  accessToken = $state<string | null>(readStorage(ACCESS_KEY));
  refreshToken = $state<string | null>(readStorage(REFRESH_KEY));
  user = $state<UserRead | null>(null);

  get isAuthenticated() {
    return this.accessToken !== null;
  }

  setTokens(tokens: TokenResponse) {
    this.accessToken = tokens.access_token;
    this.refreshToken = tokens.refresh_token;
    writeStorage(ACCESS_KEY, tokens.access_token);
    writeStorage(REFRESH_KEY, tokens.refresh_token);
  }

  setUser(user: UserRead | null) {
    this.user = user;
  }

  clear() {
    this.accessToken = null;
    this.refreshToken = null;
    this.user = null;
    writeStorage(ACCESS_KEY, null);
    writeStorage(REFRESH_KEY, null);
  }
}

export const auth = new AuthStore();
