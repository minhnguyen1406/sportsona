/** "Six degrees of teammates" — BFS shortest chain between two drivers. */

import { apiFetch } from './client';

export interface Via {
  season: number;
  constructor_id: string;
  constructor: string;
}

export interface Hop {
  driver_id: string;
  name: string;
  via: Via | null;
}

export interface Connection {
  from_id: string;
  to_id: string;
  degrees: number;
  path: Hop[];
}

export interface GraphStats {
  drivers: number;
  teammate_links: number;
}

export const connectionsApi = {
  connect(fromId: string, toId: string): Promise<Connection> {
    return apiFetch('/api/v1/connections', { query: { from: fromId, to: toId }, skipAuth: true });
  },
  stats(): Promise<GraphStats> {
    return apiFetch('/api/v1/connections/stats', { skipAuth: true });
  }
};
