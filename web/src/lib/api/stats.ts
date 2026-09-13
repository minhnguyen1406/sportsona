/** F1 analytics endpoints (each backed by one algorithm — see backend services/stats.py). */

import { apiFetch } from './client';

export interface FormPoint { race_id: number; race: string; season: number; round: number; position: number | null; points: number; rolling_avg: number; }
export interface FormGuide { driver_id: string; season: number; window: number; current_avg: number; momentum: number; best_window_avg: number; series: FormPoint[]; }

export interface StreakRef { race_id: number; race: string; season: number; }
export interface Streak { length: number; from: StreakRef; to: StreakRef; }
export interface Streaks {
  driver_id: string; races: number;
  longest_win_streak: Streak | null; longest_podium_streak: Streak | null; longest_points_streak: Streak | null;
  hottest_stretch: Partial<Streak> & { points_above_average: number; career_avg_points: number };
}

export interface ProgressionRound { round: number; race: string; points: number; cumulative: number; }
export interface Progression { driver_id: string; season: number; total: number; rounds: ProgressionRound[]; }

export interface TitleRow { driver_id: string; name: string; position: number; points: number; max_possible: number; alive: boolean; needs_per_round: number | null; }
export interface TitleMath { season: number; after_round: number; remaining_rounds: number; remaining_sprints: number; max_points_per_round: number; leader: TitleRow | null; clinched: boolean; still_alive: number; drivers: TitleRow[]; }

export const statsApi = {
  form(driverId: string, k = 5): Promise<FormGuide> {
    return apiFetch(`/api/v1/f1/drivers/${driverId}/form`, { query: { k }, skipAuth: true });
  },
  streaks(driverId: string): Promise<Streaks> {
    return apiFetch(`/api/v1/f1/drivers/${driverId}/streaks`, { skipAuth: true });
  },
  progression(driverId: string, season: number): Promise<Progression> {
    return apiFetch(`/api/v1/f1/drivers/${driverId}/progression`, { query: { season }, skipAuth: true });
  },
  titleMath(year: number): Promise<TitleMath> {
    return apiFetch(`/api/v1/f1/seasons/${year}/title-math`, { skipAuth: true });
  }
};
