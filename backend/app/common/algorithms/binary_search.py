"""Binary search helpers over a sorted array — O(log n) each.

``rank_of`` answers "where does this value sit among these?" — the lap-time
percentile: how many drivers were faster. ``first_index``/``last_index`` are
the lower/upper bound pair behind "find first and last position".

Implemented by hand rather than via ``bisect`` to show the invariant:
lo/hi bracket the answer, and each step halves the bracket.

LeetCode analogs: Search Insert Position (#35), Find First and Last Position
(#34), Binary Search (#704).
"""

from __future__ import annotations

from typing import Sequence


def lower_bound(a: Sequence[float], x: float) -> int:
    """First index i with a[i] >= x (== len(a) if none). Insert position."""
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def upper_bound(a: Sequence[float], x: float) -> int:
    """First index i with a[i] > x."""
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def first_index(a: Sequence[float], x: float) -> int:
    i = lower_bound(a, x)
    return i if i < len(a) and a[i] == x else -1


def last_index(a: Sequence[float], x: float) -> int:
    i = upper_bound(a, x) - 1
    return i if i >= 0 and a[i] == x else -1


def rank_of(sorted_asc: Sequence[float], x: float) -> tuple[int, float]:
    """For an ascending array (e.g. lap times, faster = smaller):
    returns (1-based rank, percentile of entries x beats).
    rank = 1 + count of entries strictly smaller than x."""
    faster = lower_bound(sorted_asc, x)
    n = len(sorted_asc)
    beaten = n - upper_bound(sorted_asc, x)     # strictly slower than x
    pct = (beaten / n * 100.0) if n else 0.0
    return faster + 1, pct
