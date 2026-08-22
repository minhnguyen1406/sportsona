#!/usr/bin/env python3
"""Report likely-duplicate driver/constructor rows (union-find over identity
signals). Read-only. Usage: python -m scripts.find_duplicates"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.sports.f1.services import duplicates


def main() -> None:
    db = SessionLocal()
    try:
        for label, fn in (("Drivers", duplicates.find_duplicate_drivers),
                          ("Constructors", duplicates.find_duplicate_constructors)):
            clusters = fn(db)
            print(f"\n{label}: {len(clusters)} duplicate cluster(s)")
            for c in clusters:
                print(f"  {' / '.join(c.ids)}  →  keep '{c.suggested_canonical}'")
                for s in c.signals:
                    print(f"      matched on {s}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
