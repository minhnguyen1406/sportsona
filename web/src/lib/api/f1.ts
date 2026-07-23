/** F1 sport module — types + endpoints. Template for future sports:
 *  a new sport is a sibling file (e.g. `nba.ts`) added to the barrel. */

import { apiFetch } from './client';

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
