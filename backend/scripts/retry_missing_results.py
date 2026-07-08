#!/usr/bin/env python3
"""Retry sync of (year, round) tuples that still have no race_results.

Targets only the missing rounds — does not re-fetch anything that's already
in the database. Sleeps between calls to stay under Ergast/Jolpica's rate
limit (~4 req/s sustained, 500/h budget), and backs off exponentially when
a 429-like error fires.

Usage:
    python -m scripts.retry_missing_results --seasons 2013-2017,2020
    python -m scripts.retry_missing_results --seasons 2014           # single year
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models import Race, RaceResult
from app.services import F1DataService


# Stay well under Ergast's 4 req/s ceiling. The internal sync also fans out
# a few sub-requests per round, so even 1.5s between rounds is conservative.
BASE_SLEEP = 1.5
MAX_RETRIES_PER_ROUND = 3
BACKOFF_INITIAL = 30       # seconds — first 429 retry wait
BACKOFF_MAX = 300
MAX_CONSECUTIVE_FAILS = 8  # circuit-breaker: bail if Ergast is truly down


def parse_seasons(s: str) -> list[int]:
    out: set[int] = set()
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a), int(b) + 1))
        elif part.strip():
            out.add(int(part))
    return sorted(out)


def _is_rate_limited(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(s in msg for s in ("429", "too many requests", "rate limit", "500 calls"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seasons",
        required=True,
        help="Comma-separated season list with optional ranges: '2013-2017,2020'",
    )
    args = parser.parse_args()
    seasons = parse_seasons(args.seasons)
    print(f"Scanning seasons: {seasons}")

    db = SessionLocal()
    try:
        service = F1DataService(db)

        # Build the work list — only rounds with zero results.
        targets: list[tuple[int, int, str]] = []
        for season in seasons:
            races = (
                db.query(Race)
                .filter(Race.season == season)
                .order_by(Race.round)
                .all()
            )
            for r in races:
                exists = (
                    db.query(RaceResult)
                    .filter(RaceResult.race_id == r.id)
                    .first()
                )
                if exists is None:
                    targets.append((r.season, r.round, r.name))

        if not targets:
            print("Nothing missing — every round already has results.")
            return

        print(f"{len(targets)} rounds missing. Starting retry pass.")
        print(f"Pace: {BASE_SLEEP}s between calls, backoff {BACKOFF_INITIAL}-{BACKOFF_MAX}s on 429.\n")

        consecutive_fails = 0
        total_success = 0
        total_failed = 0
        backoff = BACKOFF_INITIAL

        for season, rnd, name in targets:
            attempt = 0
            while attempt < MAX_RETRIES_PER_ROUND:
                attempt += 1
                try:
                    results = service.sync_race_results(season, rnd)
                    print(f"  ✓ {season} R{rnd:>2} {name}: {len(results)} results")
                    total_success += 1
                    consecutive_fails = 0
                    backoff = BACKOFF_INITIAL  # reset on success
                    time.sleep(BASE_SLEEP)
                    break
                except Exception as exc:
                    db.rollback()
                    if _is_rate_limited(exc) and attempt < MAX_RETRIES_PER_ROUND:
                        wait = min(backoff, BACKOFF_MAX)
                        print(f"  ⏸  {season} R{rnd:>2} {name}: 429 — sleeping {wait}s")
                        time.sleep(wait)
                        backoff = min(backoff * 2, BACKOFF_MAX)
                        continue
                    print(f"  ✗ {season} R{rnd:>2} {name}: {exc}")
                    total_failed += 1
                    consecutive_fails += 1
                    break

            if consecutive_fails >= MAX_CONSECUTIVE_FAILS:
                print(f"\n!! {consecutive_fails} consecutive failures — Ergast may be down. Stopping early.")
                break

        skipped = len(targets) - total_success - total_failed
        print(
            f"\nDone. {total_success} succeeded, {total_failed} failed"
            + (f", {skipped} skipped (early stop)" if skipped else "")
            + "."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
