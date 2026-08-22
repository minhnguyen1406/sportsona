"""Build the autocomplete trie from the database and query it.

The trie is built once from every driver + constructor and cached in-process
with a TTL (the data only changes on the nightly sync). Each entity is
inserted under several *keys* — its full name and each individual word — so
"ham", "lewis" and "lewis ham" all reach Lewis Hamilton. Keys are
ASCII-folded and lower-cased so "raikkonen" finds Räikkönen.
"""

from __future__ import annotations

import time
from typing import NamedTuple

from sqlalchemy.orm import Session

from app.common.algorithms.trie import Trie
from app.models import Constructor, Driver
from app.sports.f1.services.sync_service import F1DataService


class SearchHit(NamedTuple):
    """Hashable payload stored in the trie. ``href`` is where the UI navigates."""

    kind: str        # "driver" | "constructor"
    id: str
    label: str       # display name
    sublabel: str    # e.g. "Driver · British"
    href: str


# Rebuild at most every 10 minutes — plenty, given data changes nightly.
_TTL_SECONDS = 600
_cache: tuple[float, Trie[SearchHit]] | None = None


def _normalise(text: str) -> str:
    # Reuse the sync layer's folding so search keys match the slug conventions.
    return F1DataService._ascii_fold(text).lower().strip()


def _keys_for(name: str) -> set[str]:
    """Full name plus each word, so any word-prefix matches."""
    full = _normalise(name)
    keys = {full}
    keys.update(w for w in full.split() if w)
    return keys


def build_trie(db: Session) -> Trie[SearchHit]:
    trie: Trie[SearchHit] = Trie()

    for d in db.query(Driver).all():
        name = f"{d.given_name} {d.family_name}".strip()
        hit = SearchHit(
            kind="driver",
            id=d.driver_id,
            label=name,
            sublabel=f"Driver · {d.nationality}" if d.nationality else "Driver",
            href=f"/drivers/{d.driver_id}",
        )
        for key in _keys_for(name):
            trie.insert(key, hit)

    for c in db.query(Constructor).all():
        hit = SearchHit(
            kind="constructor",
            id=c.constructor_id,
            label=c.name,
            sublabel=f"Team · {c.nationality}" if c.nationality else "Team",
            href=f"/constructors/{c.constructor_id}",
        )
        for key in _keys_for(c.name):
            trie.insert(key, hit)

    return trie


def get_trie(db: Session) -> Trie[SearchHit]:
    """Cached trie; rebuilt after the TTL lapses."""
    global _cache
    now = time.monotonic()
    if _cache is None or now - _cache[0] > _TTL_SECONDS:
        _cache = (now, build_trie(db))
    return _cache[1]


def suggest(db: Session, query: str, limit: int = 8) -> list[SearchHit]:
    """Prefix suggestions for ``query``. O(len(query) + limit) against the trie."""
    q = _normalise(query)
    if not q:
        return []
    return get_trie(db).search_prefix(q, limit=limit)
