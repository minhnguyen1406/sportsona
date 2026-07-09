#!/usr/bin/env python3
"""Nightly data sync daemon — keeps the current F1 season fresh.

Runs as its own container (see the `sportsona-scheduler` service in
docker-compose.yml). Once a day at SYNC_HOUR_UTC it syncs the current
season's schedule, race results, qualifying, and standings. Each step is
independently fault-isolated: one failed round never aborts the run, and a
failed run never kills the daemon — it just logs and waits for tomorrow.

Configuration (env):
    SYNC_HOUR_UTC     Hour of day (0-23) to run. Default 4 — after even the
                      latest-finishing race days, before most users wake.
    SYNC_ON_STARTUP   "1" to run one sync immediately at boot (useful after
                      downtime), then fall into the daily schedule.
"""
from __future__ import annotations

import logging
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("scheduled_sync")

SYNC_HOUR_UTC = int(os.environ.get("SYNC_HOUR_UTC", "4"))
SYNC_ON_STARTUP = os.environ.get("SYNC_ON_STARTUP", "0") == "1"


def _current_season() -> int:
    return datetime.now(timezone.utc).year


def _seconds_until_next_run() -> float:
    now = datetime.now(timezone.utc)
    next_run = now.replace(hour=SYNC_HOUR_UTC, minute=0, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)
    return (next_run - now).total_seconds()


def run_sync() -> None:
    """One full sync pass for the current season. Never raises."""
    # Imports deferred so a transient DB outage at boot doesn't kill the
    # daemon before its first retry.
    from app.core.database import SessionLocal
    from app.models import Race
    from app.services import F1DataService

    year = _current_season()
    logger.info("Sync starting for season %s", year)
    db = SessionLocal()
    try:
        service = F1DataService(db)

        try:
            stats = service.sync_season(year)
            logger.info("Season sync: %s", stats)
        except Exception:
            db.rollback()
            logger.exception("Season sync failed — continuing with results")

        completed = (
            db.query(Race)
            .filter(Race.season == year, Race.date <= date.today())
            .order_by(Race.round)
            .all()
        )
        for race in completed:
            rd, rname = race.round, race.name
            try:
                results = service.sync_race_results(year, rd)
                logger.info("Results R%s (%s): %s rows", rd, rname, len(results))
            except Exception:
                db.rollback()
                logger.exception("Results R%s (%s) failed", rd, rname)
            try:
                quali = service.sync_qualifying_results(year, rd)
                logger.info("Qualifying R%s (%s): %s rows", rd, rname, len(quali))
            except Exception:
                db.rollback()
                logger.exception("Qualifying R%s (%s) failed", rd, rname)

        try:
            standings = service.sync_standings(year)
            logger.info("Standings sync: %s", standings)
        except Exception:
            db.rollback()
            logger.exception("Standings sync failed")

        logger.info("Sync finished for season %s", year)
    except Exception:
        logger.exception("Sync pass failed at the top level")
    finally:
        db.close()


def main() -> None:
    logger.info(
        "Scheduler up. Daily sync at %02d:00 UTC%s.",
        SYNC_HOUR_UTC,
        " (plus one run now)" if SYNC_ON_STARTUP else "",
    )
    if SYNC_ON_STARTUP:
        run_sync()

    while True:
        wait = _seconds_until_next_run()
        logger.info("Next sync in %.1f hours", wait / 3600)
        time.sleep(wait)
        run_sync()


if __name__ == "__main__":
    main()
