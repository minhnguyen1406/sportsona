"""Interval utilities via sort + sweep.

Careers are intervals on the season axis. "Did Senna and Schumacher overlap?"
is an interval-intersection test; "how many drivers were active in 1994?" is
a point query; "peak concurrent drivers" is the classic sweep line: sort the
+1/-1 events by time and track the running count.

LeetCode analogs: Merge Intervals (#56), Meeting Rooms II (#253),
Interval List Intersections (#986).
"""

from __future__ import annotations

from typing import Hashable, Iterable, TypeVar

Interval = tuple[int, int]   # inclusive [start, end]
T = TypeVar("T", bound=Hashable)


def overlap(a: Interval, b: Interval) -> Interval | None:
    """The intersection of two inclusive intervals, or None."""
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    return (lo, hi) if lo <= hi else None


def merge(intervals: Iterable[Interval]) -> list[Interval]:
    """Coalesce overlapping/adjacent inclusive intervals. O(n log n) for the
    sort, then one linear pass. [1,3],[4,6] merge (adjacent seasons)."""
    out: list[Interval] = []
    for start, end in sorted(intervals):
        if out and start <= out[-1][1] + 1:
            out[-1] = (out[-1][0], max(out[-1][1], end))
        else:
            out.append((start, end))
    return out


def max_concurrent(intervals: Iterable[Interval]) -> tuple[int, int | None]:
    """Sweep line: the most intervals alive at once, and a time where that
    peak occurs. Events: +1 at start, -1 at end+1 (inclusive ends). Sort by
    time, with ends processed before starts at the same time so touching
    intervals don't double count. O(n log n)."""
    events: list[tuple[int, int]] = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end + 1, -1))
    events.sort(key=lambda e: (e[0], e[1]))   # -1 before +1 at equal time
    best, best_at, live = 0, None, 0
    for t, delta in events:
        live += delta
        if live > best:
            best, best_at = live, t
    return best, best_at


def active_at(intervals: dict[T, Interval], t: int) -> list[T]:
    """All keys whose interval contains ``t``. O(n) point query."""
    return [k for k, (s, e) in intervals.items() if s <= t <= e]
