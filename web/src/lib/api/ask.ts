/** Natural-language stats: ask, shareable answers, per-user history. */

import { apiFetch } from './client';

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
  cached: boolean;
  answer_id: string | null;
}

export interface AskAnswerResponse {
  slug: string;
  question: string;
  sql: string;
  reasoning: string;
  columns: string[];
  rows: unknown[][];
  truncated: boolean;
  model: string;
  created_at: string;
}

export interface AskHistoryItem {
  slug: string;
  question: string;
  created_at: string;
}

export const askApi = {
  ask(question: string): Promise<AskResponse> {
    // Auth is optional here — send the token when we have one so the ask
    // lands in the user's history; anonymous asks still work.
    return apiFetch('/api/v1/ask', {
      method: 'POST',
      json: { question }
    });
  },
  getAnswer(slug: string): Promise<AskAnswerResponse> {
    return apiFetch(`/api/v1/ask/answers/${slug}`, { skipAuth: true });
  },
  history(): Promise<AskHistoryItem[]> {
    return apiFetch('/api/v1/ask/history');
  }
};
