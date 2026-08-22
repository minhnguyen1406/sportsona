/** Autocomplete suggestions (Trie-backed) over drivers + teams. */

import { apiFetch } from './client';

export interface Suggestion {
  kind: 'driver' | 'constructor';
  id: string;
  label: string;
  sublabel: string;
  href: string;
}

export const searchApi = {
  suggest(q: string, limit = 8): Promise<Suggestion[]> {
    return apiFetch('/api/v1/search/suggest', { query: { q, limit }, skipAuth: true });
  }
};
