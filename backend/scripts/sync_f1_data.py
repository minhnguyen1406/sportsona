#!/usr/bin/env python3
"""
Script to sync F1 data from FastF1 to the database.

Usage:
    python -m scripts.sync_f1_data --year 2024
    python -m scripts.sync_f1_data --year 2024 --results
"""
import argparse
import sys
from datetime import date
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.services import F1DataService


def main():
    parser = argparse.ArgumentParser(description='Sync F1 data to database')
    parser.add_argument('--year', type=int, required=True, help='Season year to sync')
    parser.add_argument('--results', action='store_true', help='Also sync race results for completed races')
    parser.add_argument('--standings', action='store_true', help='Also sync standings for the season')
    args = parser.parse_args()

    db = SessionLocal()
    try:
        service = F1DataService(db)

        print(f"Syncing {args.year} season...")

        # Sync season data (schedule, drivers, constructors, circuits)
        stats = service.sync_season(args.year)
        print(f"  ✓ {stats['races']} races synced")
        print(f"  ✓ {stats['drivers']} new drivers synced")
        print(f"  ✓ {stats['constructors']} new constructors synced")
        print(f"  ✓ {stats['driver_entries']} driver entries synced")

        # Optionally sync results for completed races
        if args.results:
            print("  Syncing race results...")
            from app.models import Race
            races = db.query(Race).filter(
                Race.season == args.year,
                Race.date <= date.today()
            ).order_by(Race.round).all()

            for race in races:
                try:
                    results = service.sync_race_results(args.year, race.round)
                    print(f"    ✓ Round {race.round} ({race.name}): {len(results)} results")
                except Exception as e:
                    print(f"    ✗ Round {race.round}: {e}")

        # Optionally sync standings
        if args.standings:
            print("  Syncing standings...")
            try:
                stats = service.sync_standings(args.year)
                print(f"    ✓ Round {stats['round']}: {stats['driver_standings']} driver, {stats['constructor_standings']} constructor standings")
            except Exception as e:
                print(f"    ✗ Standings: {e}")

        print("\nSync complete!")

    finally:
        db.close()


if __name__ == '__main__':
    main()
