"""Driver/season analytics built on the pure algorithms in
``app.common.algorithms``. Each function = one algorithm applied to real
F1 rows; the router below just serialises them.

  form_guide        sliding window   rolling points average, momentum
  streaks           one-pass scans   longest win/podium/points runs + Kadane
  progression       prefix sums      cumulative points per round
  career_overlap    intervals        did two careers overlap, and when
  active_in         intervals        who was active in a given season
  title_math        greedy bound     who can still mathematically win
  fantasy_optimize  0/1 knapsack     best roster under a budget
  lap_rank          binary search    where a lap time ranks in a field
"""

from __future__ import annotations

from typing import NamedTuple

from sqlalchemy.orm import Session, joinedload

from app.common.algorithms import binary_search, intervals, knapsack, prefix_sum, sliding_window, streaks
from app.models import Driver, DriverEntry, DriverStanding, QualifyingResult, Race, RaceResult


class StatsError(Exception):
    pass


# ── shared loaders ─────────────────────────────────────────────────────────

def _driver_or_raise(db: Session, driver_id: str) -> Driver:
    d = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if d is None:
        raise StatsError(f"Unknown driver: {driver_id}")
    return d


def _results_chronological(db: Session, driver_id: str, season: int | None = None) -> list[RaceResult]:
    q = (
        db.query(RaceResult)
        .join(Race, Race.id == RaceResult.race_id)
        .options(joinedload(RaceResult.race))
        .filter(RaceResult.driver_id == driver_id)
    )
    if season is not None:
        q = q.filter(Race.season == season)
    return q.order_by(Race.date.asc(), Race.round.asc()).all()


def _name(d: Driver) -> str:
    return f"{d.given_name} {d.family_name}".strip()


# ── form guide (sliding window) ────────────────────────────────────────────

class FormPoint(NamedTuple):
    race_id: int
    race: str
    season: int
    round: int
    position: int | None
    points: float
    rolling_avg: float


def form_guide(db: Session, driver_id: str, k: int = 5) -> dict:
    """Rolling k-race points average over the driver's most recent season,
    plus momentum = current window avg − the window k races earlier."""
    _driver_or_raise(db, driver_id)
    results = _results_chronological(db, driver_id)
    if not results:
        raise StatsError("No results for this driver.")
    latest_season = results[-1].race.season
    season_results = [r for r in results if r.race.season == latest_season]
    pts = [r.points or 0.0 for r in season_results]
    avgs = sliding_window.rolling_average(pts, k)
    series = [
        FormPoint(r.race.id, r.race.name, r.race.season, r.race.round, r.position, r.points or 0.0, round(a, 2))
        for r, a in zip(season_results, avgs)
    ]
    current = avgs[-1]
    earlier = avgs[-1 - k] if len(avgs) > k else avgs[0]
    return {
        "driver_id": driver_id,
        "season": latest_season,
        "window": k,
        "current_avg": round(current, 2),
        "momentum": round(current - earlier, 2),
        "best_window_avg": round(max(sliding_window.sliding_max(avgs, 1)), 2) if avgs else 0.0,
        "series": [p._asdict() for p in series],
    }


# ── streaks (longest run + Kadane) ─────────────────────────────────────────

def _run_to_dict(results: list[RaceResult], run: tuple[int, int, int]) -> dict | None:
    length, s, e = run
    if length == 0:
        return None
    return {
        "length": length,
        "from": {"race_id": results[s].race.id, "race": results[s].race.name, "season": results[s].race.season},
        "to": {"race_id": results[e - 1].race.id, "race": results[e - 1].race.name, "season": results[e - 1].race.season},
    }


def career_streaks(db: Session, driver_id: str) -> dict:
    _driver_or_raise(db, driver_id)
    results = _results_chronological(db, driver_id)
    if not results:
        raise StatsError("No results for this driver.")
    wins = streaks.longest_run(results, lambda r: r.position == 1)
    podiums = streaks.longest_run(results, lambda r: r.position is not None and r.position <= 3)
    points = streaks.longest_run(results, lambda r: (r.points or 0) > 0)

    # Kadane on (points − career average): the hottest stretch *relative to
    # this driver's own norm*, so a midfielder's purple patch shows up too.
    pts = [r.points or 0.0 for r in results]
    avg = sum(pts) / len(pts)
    best_sum, s, e = streaks.max_subarray([p - avg for p in pts])
    return {
        "driver_id": driver_id,
        "races": len(results),
        "longest_win_streak": _run_to_dict(results, wins),
        "longest_podium_streak": _run_to_dict(results, podiums),
        "longest_points_streak": _run_to_dict(results, points),
        "hottest_stretch": {
            **(_run_to_dict(results, (e - s, s, e)) or {}),
            "points_above_average": round(best_sum, 1),
            "career_avg_points": round(avg, 2),
        },
    }


# ── points progression (prefix sums) ───────────────────────────────────────

def progression(db: Session, driver_id: str, season: int) -> dict:
    _driver_or_raise(db, driver_id)
    results = _results_chronological(db, driver_id, season)
    if not results:
        raise StatsError(f"No {season} results for this driver.")
    pts = [r.points or 0.0 for r in results]
    ps = prefix_sum.PrefixSum(pts)
    cumulative = ps.cumulative()
    return {
        "driver_id": driver_id,
        "season": season,
        "total": ps.total(),
        "rounds": [
            {"round": r.race.round, "race": r.race.name, "points": p, "cumulative": c}
            for r, p, c in zip(results, pts, cumulative)
        ],
    }


# ── careers (intervals) ────────────────────────────────────────────────────

def _career_interval(db: Session, driver_id: str) -> intervals.Interval | None:
    seasons = {s for (s,) in db.query(DriverEntry.season).filter(DriverEntry.driver_id == driver_id)}
    seasons |= {
        s for (s,) in db.query(Race.season).join(RaceResult, RaceResult.race_id == Race.id)
        .filter(RaceResult.driver_id == driver_id)
    }
    return (min(seasons), max(seasons)) if seasons else None


def career_overlap(db: Session, a: str, b: str) -> dict:
    da, dbb = _driver_or_raise(db, a), _driver_or_raise(db, b)
    ia, ib = _career_interval(db, a), _career_interval(db, b)
    if ia is None or ib is None:
        raise StatsError("One of the drivers has no recorded seasons.")
    shared = intervals.overlap(ia, ib)
    return {
        "a": {"driver_id": a, "name": _name(da), "career": {"from": ia[0], "to": ia[1]}},
        "b": {"driver_id": b, "name": _name(dbb), "career": {"from": ib[0], "to": ib[1]}},
        "overlap": {"from": shared[0], "to": shared[1], "seasons": shared[1] - shared[0] + 1} if shared else None,
    }


def active_in(db: Session, year: int) -> dict:
    rows = db.query(DriverEntry.driver_id, DriverEntry.season).all()
    spans: dict[str, intervals.Interval] = {}
    for d, s in rows:
        lo, hi = spans.get(d, (s, s))
        spans[d] = (min(lo, s), max(hi, s))
    ids = sorted(intervals.active_at(spans, year))
    peak, peak_year = intervals.max_concurrent(spans.values())
    return {"year": year, "count": len(ids), "driver_ids": ids, "peak": {"count": peak, "year": peak_year}}


# ── title math (greedy upper bound) ────────────────────────────────────────

MAX_POINTS_PER_ROUND = 25   # a win; sprints (+8) aren't modelled yet, so this is conservative


def title_math(db: Session, season: int) -> dict:
    """For each driver: the most points they could still reach
    (current + 25 × remaining rounds). They're alive iff that bound ≥ the
    leader's current total. The leader has clinched iff nobody else is alive.
    Same reasoning as Jump Game: compute the furthest reachable bound and
    compare."""
    latest = db.query(DriverStanding.round).filter(DriverStanding.season == season).order_by(DriverStanding.round.desc()).first()
    if latest is None:
        raise StatsError(f"No standings for {season}.")
    after_round = latest[0]
    standings = (
        db.query(DriverStanding).options(joinedload(DriverStanding.driver))
        .filter(DriverStanding.season == season, DriverStanding.round == after_round)
        .order_by(DriverStanding.position).all()
    )
    total_rounds = db.query(Race).filter(Race.season == season).count()
    remaining = max(0, total_rounds - after_round)
    leader_pts = standings[0].points if standings else 0.0

    rows = []
    for s in standings:
        max_possible = s.points + MAX_POINTS_PER_ROUND * remaining
        rows.append({
            "driver_id": s.driver_id, "name": _name(s.driver), "position": s.position,
            "points": s.points, "max_possible": max_possible,
            "alive": max_possible >= leader_pts,
            "needs_per_round": round((leader_pts - s.points) / remaining, 2) if remaining else None,
        })
    alive_others = [r for r in rows[1:] if r["alive"]]
    return {
        "season": season, "after_round": after_round, "remaining_rounds": remaining,
        "max_points_per_round": MAX_POINTS_PER_ROUND,
        "leader": rows[0] if rows else None,
        "clinched": bool(rows) and not alive_others,
        "still_alive": sum(r["alive"] for r in rows),
        "drivers": rows,
    }


# ── fantasy optimiser (0/1 knapsack) ───────────────────────────────────────

def _cost_for_position(position: int) -> int:
    """Heuristic price tier derived from championship position — this is a
    cost *model* (we have no real fantasy prices): P1 ≈ 29, P20 ≈ 10."""
    return max(6, 30 - position)


def fantasy_optimize(db: Session, season: int, budget: int = 100, max_drivers: int = 5) -> dict:
    latest = db.query(DriverStanding.round).filter(DriverStanding.season == season).order_by(DriverStanding.round.desc()).first()
    if latest is None:
        raise StatsError(f"No standings for {season}.")
    standings = (
        db.query(DriverStanding).options(joinedload(DriverStanding.driver))
        .filter(DriverStanding.season == season, DriverStanding.round == latest[0]).all()
    )
    pool = [knapsack.Item(s.driver_id, _cost_for_position(s.position), s.points) for s in standings]
    by_id = {s.driver_id: s for s in standings}
    value, chosen = knapsack.knapsack(pool, budget, max_items=max_drivers)
    roster = [
        {"driver_id": d, "name": _name(by_id[d].driver), "position": by_id[d].position,
         "points": by_id[d].points, "cost": _cost_for_position(by_id[d].position)}
        for d in chosen
    ]
    return {
        "season": season, "budget": budget, "max_drivers": max_drivers,
        "total_points": value, "total_cost": sum(r["cost"] for r in roster),
        "roster": roster, "cost_model": "cost = max(6, 30 - championship_position)",
    }


# ── lap rank (binary search) ───────────────────────────────────────────────

def parse_lap_time(text: str) -> float:
    """'1:12.051' → 72.051 seconds. Also accepts plain seconds."""
    text = text.strip()
    if ":" in text:
        m, s = text.split(":", 1)
        return int(m) * 60 + float(s)
    return float(text)


def lap_rank(db: Session, race_id: int, time_text: str) -> dict:
    quali = db.query(QualifyingResult).filter(QualifyingResult.race_id == race_id).all()
    if not quali:
        raise StatsError("No qualifying data for this race.")
    # Each driver's best session time.
    best: list[float] = []
    for q in quali:
        times = [parse_lap_time(t) for t in (q.q3_time, q.q2_time, q.q1_time) if t]
        if times:
            best.append(min(times))
    best.sort()
    t = parse_lap_time(time_text)
    rank, pct = binary_search.rank_of(best, t)
    return {
        "race_id": race_id, "time": t, "rank": rank, "field_size": len(best),
        "beats_percent": round(pct, 1), "pole_time": best[0], "gap_to_pole": round(t - best[0], 3),
    }
