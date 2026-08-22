"""Prefix sums: O(n) build, O(1) range sum.

prefix[i] = sum(values[:i]). Then sum(values[a:b]) = prefix[b] - prefix[a].
The cumulative array *is* the "points progression" chart (points after each
round), and any "points scored between round a and b" is one subtraction.

LeetCode analogs: Running Sum of 1d Array (#1480), Range Sum Query
Immutable (#303), Subarray Sum Equals K (#560).
"""

from __future__ import annotations

from typing import Sequence


class PrefixSum:
    def __init__(self, values: Sequence[float]) -> None:
        self._prefix: list[float] = [0.0]
        for v in values:
            self._prefix.append(self._prefix[-1] + v)

    def range_sum(self, a: int, b: int) -> float:
        """Sum of values[a:b] (half-open). O(1)."""
        if not 0 <= a <= b <= len(self._prefix) - 1:
            raise IndexError("range out of bounds")
        return self._prefix[b] - self._prefix[a]

    def cumulative(self) -> list[float]:
        """Running totals after each element — the progression curve."""
        return self._prefix[1:]

    def total(self) -> float:
        return self._prefix[-1]


def count_subarrays_with_sum(values: Sequence[float], target: float) -> int:
    """#560 — hash map of prefix sums seen so far; for each prefix p, any
    earlier prefix equal to p - target closes a qualifying subarray. O(n)."""
    seen: dict[float, int] = {0.0: 1}
    running = 0.0
    count = 0
    for v in values:
        running += v
        count += seen.get(running - target, 0)
        seen[running] = seen.get(running, 0) + 1
    return count
