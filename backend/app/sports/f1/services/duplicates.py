"""Duplicate-identity detection for drivers and constructors — Union-Find.

Two upstreams (FastF1, Ergast) plus years of id-convention drift left the
same person under several ids: ``kimi_raikkonen`` / ``raikkonen`` /
``kimi_räikkönen``. Until now we caught these by hand (an alias table and a
cleanup SQL script). This turns that into an algorithm.

It is exactly LeetCode #721 *Accounts Merge*:
  - each row is an "account"
  - each identity signal is an "email": the ASCII-folded full-name slug, a
    (date of birth, surname) pair, and the hand-maintained alias table
  - rows that share any signal get unioned in a DisjointSet
  - every resulting set with more than one member is a merge candidate

We key on signals that identify a *person*, never on surname alone — that
would merge the Rosbergs, Hills and Schumachers, who are different people.
"""

from __future__ import annotations

from typing import NamedTuple

from sqlalchemy.orm import Session

from app.common.algorithms.disjoint_set import DisjointSet
from app.models import Constructor, Driver
from app.sports.f1.services.sync_service import F1DataService


class DuplicateCluster(NamedTuple):
    ids: list[str]          # every row id in the cluster
    suggested_canonical: str
    signals: list[str]      # the identity keys that tied them together


def _driver_signals(d: Driver) -> set[str]:
    """Identity keys for one driver row."""
    slug = F1DataService._slugify(f"{d.given_name} {d.family_name}")
    keys = {f"name:{slug}"}
    if d.date_of_birth:
        keys.add(f"dob:{d.date_of_birth.isoformat()}:{F1DataService._slugify(d.family_name)}")
    # Alias table: both the alias and its canonical map to the same key.
    aliases = F1DataService._DRIVER_ALIASES
    if d.driver_id in aliases:
        keys.add(f"alias:{aliases[d.driver_id]}")
    if d.driver_id in aliases.values():
        keys.add(f"alias:{d.driver_id}")
    return keys


def _pick_canonical(ids: list[str], preferred: str | None) -> str:
    """Prefer the id that equals the full-name slug (our convention); else the
    longest id (long-form beats short-form)."""
    if preferred and preferred in ids:
        return preferred
    return max(ids, key=len)


def _cluster(rows: list[tuple[str, set[str]]], preferred: dict[str, str]) -> list[DuplicateCluster]:
    """Accounts-Merge core: union rows that share any signal key.

    ``rows`` = [(row_id, {signal keys})]. O(total signals · α(n)).
    """
    dsu: DisjointSet[str] = DisjointSet(r[0] for r in rows)
    first_owner: dict[str, str] = {}   # signal key → first row id seen with it
    tying_signals: dict[str, set[str]] = {}

    for row_id, keys in rows:
        for key in keys:
            owner = first_owner.setdefault(key, row_id)
            if owner != row_id:
                dsu.union(owner, row_id)
                tying_signals.setdefault(key, set()).update({owner, row_id})

    clusters = []
    for group in dsu.groups():
        if len(group) < 2:
            continue
        ids = sorted(group)
        signals = sorted(k for k, members in tying_signals.items() if members & set(ids))
        canonical = _pick_canonical(ids, next((preferred.get(i) for i in ids if preferred.get(i) in ids), None))
        clusters.append(DuplicateCluster(ids=ids, suggested_canonical=canonical, signals=signals))
    return sorted(clusters, key=lambda c: c.ids[0])


def find_duplicate_drivers(db: Session) -> list[DuplicateCluster]:
    drivers = db.query(Driver).all()
    rows = [(d.driver_id, _driver_signals(d)) for d in drivers]
    # Preferred canonical for each row = its own full-name slug (if that id exists).
    preferred = {
        d.driver_id: F1DataService._slugify(f"{d.given_name} {d.family_name}") for d in drivers
    }
    return _cluster(rows, preferred)


def find_duplicate_constructors(db: Session) -> list[DuplicateCluster]:
    constructors = db.query(Constructor).all()
    rows = [(c.constructor_id, {f"name:{F1DataService._slugify(c.name)}"}) for c in constructors]
    preferred = {c.constructor_id: F1DataService._slugify(c.name) for c in constructors}
    return _cluster(rows, preferred)
