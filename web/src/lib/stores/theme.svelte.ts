/**
 * Theme store — light / dark / system.
 *
 * Persists to localStorage under `theme`. The `<html>` element gets the
 * `dark` class added/removed whenever the resolved theme changes. An
 * inline script in `app.html` applies the saved theme *before* hydration
 * so users don't see a flash of the wrong palette on first paint.
 *
 * DOM updates happen imperatively in `set()` rather than via $effect,
 * because $effect outside a component lifecycle (e.g. at module scope)
 * doesn't fire on its own — Svelte 5 effects need a component or
 * $effect.root() that's actually mounted.
 */
import { browser } from '$app/environment';

type Theme = 'light' | 'dark' | 'system';
type Resolved = 'light' | 'dark';

const STORAGE_KEY = 'theme';

function readStored(): Theme {
  if (!browser) return 'system';
  const v = localStorage.getItem(STORAGE_KEY);
  return v === 'light' || v === 'dark' || v === 'system' ? v : 'system';
}

function systemPrefers(): Resolved {
  if (!browser) return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyDom(resolved: Resolved) {
  if (!browser) return;
  document.documentElement.classList.toggle('dark', resolved === 'dark');
}

function createThemeStore() {
  let theme = $state<Theme>(readStored());
  let systemDark = $state<boolean>(browser && systemPrefers() === 'dark');

  // Keep `systemDark` in sync with the OS — so toggling macOS dark mode
  // takes effect immediately when the user has selected 'system'.
  if (browser) {
    const mql = window.matchMedia('(prefers-color-scheme: dark)');
    mql.addEventListener('change', (e) => {
      systemDark = e.matches;
      if (theme === 'system') applyDom(e.matches ? 'dark' : 'light');
    });
  }

  const resolved = $derived<Resolved>(
    theme === 'system' ? (systemDark ? 'dark' : 'light') : theme
  );

  function set(next: Theme) {
    theme = next;
    if (!browser) return;
    localStorage.setItem(STORAGE_KEY, next);
    const nextResolved: Resolved =
      next === 'system' ? (systemPrefers()) : next;
    applyDom(nextResolved);
  }

  return {
    get theme() {
      return theme;
    },
    get resolved() {
      return resolved;
    },
    set,
    /** Cycle light → dark → system → light (used by the toggle button). */
    cycle() {
      set(theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light');
    }
  };
}

export const themeStore = createThemeStore();
