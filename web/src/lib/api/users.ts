/** User profile, follows, and the personalized dashboard. */

import { apiFetch } from './client';
import type { UserRead } from './auth';
import type { ConstructorResponse, DriverResponse, RaceResponse } from './f1';

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
