#!/usr/bin/env python3
"""Nightly data sync daemon — keeps the current F1 season fresh.

Runs as its own container (see the `sportsona-scheduler` service in
docker-compose.yml). Once a day at SYNC_HOUR_UTC it syncs the current
season's schedule, race results, qualifying, and standings. Each step is
independently fault-isolated: one failed round never aborts the run, and a
failed run never kills the daemon — it just logs, alerts, and waits for
tomorrow.

On boot the daemon checks whether any completed race this season is missing
results (the signature of downtime across a race weekend) and runs a
catch-up sync if so, so an outage heals itself on restart.

Configuration (env):
    SYNC_HOUR_UTC     Hour of day (0-23) to run. Default 4 — after even the
                      latest-finishing race days, before most users wake.
    SYNC_ON_STARTUP   "1" to always run one sync at boot, even when nothing
                      looks stale, then fall into the daily schedule.
    ALERT_EMAIL       Where to send a summary when a sync pass has failures.
                      Empty = log-only (delivery uses common.email, so it
                      also needs RESEND_API_KEY to actually send).
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
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "").strip()

# How long to keep retrying the boot-time staleness check while the DB is
# still coming up (compose healthchecks cover the normal path; this covers
# a scheduler that outlives a DB restart).
_BOOT_RETRIES = 12
_BOOT_RETRY_DELAY_S = 10


def _current_season() -> int:
    return datetime.now(timezone.utc).year


def _seconds_until_next_run() -> float:
    now = datetime.now(timezone.utc)
    next_run = now.replace(hour=SYNC_HOUR_UTC, minute=0, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)
    return (next_run - now).total_seconds()


def _rounds_missing_results() -> list[int] | None:
    """Rounds this season that are past their race date but have no results.

    Returns None when the DB can't be reached (caller decides how to retry).
    """
    from app.core.database import SessionLocal
    from app.models import Race, RaceResult

    db = SessionLocal()
    try:
        rows = (
            db.query(Race.round)
            .filter(
                Race.season == _current_season(),
                Race.date < date.today(),
                ~db.query(RaceResult.id).filter(RaceResult.race_id == Race.id).exists(),
            )
            .order_by(Race.round)
            .all()
        )
        return [r.round for r in rows]
    except Exception:
        logger.exception("Staleness check failed (DB not ready?)")
        return None
    finally:
        db.close()


def _send_alert(subject: str, body: str) -> None:
    """Best-effort failure notification. Never raises."""
    if not ALERT_EMAIL:
        logger.warning("ALERT (no ALERT_EMAIL set): %s\n%s", subject, body)
        return
    try:
        from app.common.email import get_email_service

        get_email_service().send(to=ALERT_EMAIL, subject=subject, body=body)
        logger.info("Alert sent to %s: %s", ALERT_EMAIL, subject)
    except Exception:
        logger.exception("Alert delivery failed for: %s", subject)


def run_sync() -> list[str]:
    """One full sync pass for the current season.

    Never raises; returns a list of human-readable failure descriptions
    (empty = clean pass).
    """
    # Imports deferred so a transient DB outage at boot doesn't kill the
    # daemon before its first retry.
    from app.core.database import SessionLocal
    from app.models import Race
    from app.sports.f1.services import F1DataService

    year = _current_season()
    failures: list[str] = []
    logger.info("Sync starting for season %s", year)
    db = SessionLocal()
    try:
        service = F1DataService(db)

        try:
            stats = service.sync_season(year)
            logger.info("Season sync: %s", stats)
        except Exception as exc:
            db.rollback()
            logger.exception("Season sync failed — continuing with results")
            failures.append(f"season schedule: {exc}")

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
            except Exception as exc:
                db.rollback()
                logger.exception("Results R%s (%s) failed", rd, rname)
                failures.append(f"results R{rd} ({rname}): {exc}")
            try:
                quali = service.sync_qualifying_results(year, rd)
                logger.info("Qualifying R%s (%s): %s rows", rd, rname, len(quali))
            except Exception as exc:
                db.rollback()
                logger.exception("Qualifying R%s (%s) failed", rd, rname)
                failures.append(f"qualifying R{rd} ({rname}): {exc}")
            if (race.format or "").startswith("sprint"):
                try:
                    sprint = service.sync_sprint_results(year, rd)
                    logger.info("Sprint R%s (%s): %s rows", rd, rname, len(sprint))
                except Exception as exc:
                    db.rollback()
                    logger.exception("Sprint R%s (%s) failed", rd, rname)
                    failures.append(f"sprint R{rd} ({rname}): {exc}")

        try:
            standings = service.sync_standings(year)
            logger.info("Standings sync: %s", standings)
        except Exception as exc:
            db.rollback()
            logger.exception("Standings sync failed")
            failures.append(f"standings: {exc}")

        logger.info("Sync finished for season %s (%s failures)", year, len(failures))
    except Exception as exc:
        logger.exception("Sync pass failed at the top level")
        failures.append(f"top-level: {exc}")
    finally:
        db.close()
    return failures


def run_sync_and_report(trigger: str) -> None:
    failures = run_sync()
    if failures:
        _send_alert(
            subject=f"[Sportsona] {trigger} sync had {len(failures)} failure(s)",
            body="The following sync steps failed:\n\n"
            + "\n".join(f"- {f}" for f in failures)
            + "\n\nSee the sportsona-scheduler container logs for tracebacks.",
        )


def catch_up_if_stale() -> None:
    """At boot: if completed races are missing results, sync immediately.

    This is what heals a multi-day outage — the missed nightly runs are
    detected from the data itself, not from any schedule bookkeeping.
    """
    for attempt in range(_BOOT_RETRIES):
        missing = _rounds_missing_results()
        if missing is not None:
            break
        time.sleep(_BOOT_RETRY_DELAY_S)
    else:
        _send_alert(
            subject="[Sportsona] scheduler cannot reach the database",
            body=f"Staleness check failed {_BOOT_RETRIES} times at boot. "
            "The nightly sync will keep trying on schedule.",
        )
        return

    if missing:
        logger.info("Catch-up: rounds %s have no results — syncing now", missing)
        run_sync_and_report("catch-up")
    else:
        logger.info("Data is current — no catch-up needed")


def main() -> None:
    logger.info(
        "Scheduler up. Daily sync at %02d:00 UTC%s.",
        SYNC_HOUR_UTC,
        " (plus one run now)" if SYNC_ON_STARTUP else "",
    )
    if SYNC_ON_STARTUP:
        run_sync_and_report("startup")
    else:
        catch_up_if_stale()

    while True:
        wait = _seconds_until_next_run()
        logger.info("Next sync in %.1f hours", wait / 3600)
        time.sleep(wait)
        run_sync_and_report("nightly")


if __name__ == "__main__":
    main()
