/** Personalized race recaps. */

import { apiFetch } from './client';

export interface RecapResponse {
  race_id: number;
  content: string;
  prompt_version: string;
  model: string;
  created_at: string;
  cached: boolean;
}

export const recapApi = {
  get(raceId: number): Promise<RecapResponse> {
    return apiFetch(`/api/v1/races/${raceId}/recap`);
  }
};
