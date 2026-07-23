/** Daily AI-generated "stat of the day". */

import { apiFetch } from './client';

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
