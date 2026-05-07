"""Manual smoke test for the recap pipeline.

Usage:
    poetry run python scripts/try_recap.py [--year 2024] [--round 5] [--user smoketest@example.com]

Prereqs:
    - ANTHROPIC_API_KEY set in environment / .env
    - Postgres running with synced F1 data for the chosen race+round

What it does:
    1. Looks up the user, picks a race that has both results and standings synced
    2. Temporarily attaches a couple of follows in-memory (no DB write)
    3. Generates a recap and prints it with token / latency / cache stats

Iterate the prompt in app/services/recap/prompts.py and rerun until the output
makes you sit up.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make the project root importable when run from `backend/`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Constructor,
    Driver,
    DriverStanding,
    Race,
    RaceResult,
    User,
)
from app.services.recap import RecapService, get_llm_client  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Manual recap test.")
    p.add_argument("--user", default="smoketest@example.com", help="User email")
    p.add_argument("--year", type=int, help="Season (default: latest with synced standings)")
    p.add_argument("--round", type=int, help="Race round (default: latest with results)")
    p.add_argument(
        "--follow-driver",
        action="append",
        default=[],
        help="Driver ID to follow for this run (repeatable). Defaults to top finisher.",
    )
    p.add_argument(
        "--follow-team",
        action="append",
        default=[],
        help="Constructor ID to follow for this run (repeatable). Defaults to top constructor.",
    )
    return p.parse_args()


def find_target_race(db, year: int | None, round_: int | None) -> Race | None:
    """Pick a race that has both results and standings synced."""
    q = (
        db.query(Race)
        .join(RaceResult, RaceResult.race_id == Race.id)
        .join(
            DriverStanding,
            (DriverStanding.season == Race.season) & (DriverStanding.round == Race.round),
        )
    )
    if year is not None:
        q = q.filter(Race.season == year)
    if round_ is not None:
        q = q.filter(Race.round == round_)
    return q.order_by(Race.season.desc(), Race.round.desc()).first()


def main() -> int:
    args = parse_args()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.user).first()
        if user is None:
            print(f"User {args.user!r} not found. Run /api/v1/auth/register first.", file=sys.stderr)
            return 1

        race = find_target_race(db, args.year, args.round)
        if race is None:
            print(
                "No race found with both results and standings synced. "
                "Run scripts/sync_f1_data.py for a recent season first.",
                file=sys.stderr,
            )
            return 1

        # Temporarily attach follows for this run (don't commit).
        follow_driver_ids = args.follow_driver or _default_driver_follows(db, race)
        follow_team_ids = args.follow_team or _default_team_follows(db, race)

        for did in follow_driver_ids:
            d = db.query(Driver).filter(Driver.driver_id == did).first()
            if d and d not in user.followed_drivers:
                user.followed_drivers.append(d)
        for cid in follow_team_ids:
            c = db.query(Constructor).filter(Constructor.constructor_id == cid).first()
            if c and c not in user.followed_constructors:
                user.followed_constructors.append(c)

        print(f"Race:   {race.season} {race.name} (round {race.round})")
        print(f"User:   {user.username} <{user.email}>")
        print(f"Follow: drivers={[d.driver_id for d in user.followed_drivers]} "
              f"teams={[c.constructor_id for c in user.followed_constructors]}")
        print("Generating recap…\n")

        service = RecapService(db=db, llm=get_llm_client())
        recap = service.generate(user=user, race=race)

        print("=" * 80)
        print(recap.content)
        print("=" * 80)
        gen = recap.generation
        print(
            f"\nmodel={gen.model}  prompt={recap.prompt_version}  latency={gen.latency_ms}ms\n"
            f"tokens: input={gen.input_tokens} output={gen.output_tokens} "
            f"cache_read={gen.cache_read_tokens} cache_create={gen.cache_creation_tokens}"
        )
        return 0
    finally:
        # Don't persist the in-memory follows we attached above.
        db.rollback()
        db.close()


def _default_driver_follows(db, race: Race) -> list[str]:
    """Use this race's winner as a sensible default follow if none were passed."""
    winner = (
        db.query(RaceResult)
        .filter(RaceResult.race_id == race.id, RaceResult.position == 1)
        .first()
    )
    return [winner.driver_id] if winner else []


def _default_team_follows(db, race: Race) -> list[str]:
    """Default to the leading constructor at this race+round."""
    from app.models import ConstructorStanding

    top = (
        db.query(ConstructorStanding)
        .filter(
            ConstructorStanding.season == race.season,
            ConstructorStanding.round == race.round,
            ConstructorStanding.position == 1,
        )
        .first()
    )
    return [top.constructor_id] if top else []


if __name__ == "__main__":
    sys.exit(main())
