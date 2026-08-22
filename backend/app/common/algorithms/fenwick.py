"""Fenwick tree (binary indexed tree): point update + prefix/range sum, both
O(log n), in a flat array.

Each index i "covers" the last (i & -i) elements — the lowest set bit of i.
A prefix query walks down by clearing that bit; an update walks up by adding
it. That bit trick is the whole structure; it's why it fits in n+1 ints.

When to use it over a plain prefix-sum array: when the underlying values
*change* (live scores updating) and you still want fast range sums — a
prefix array needs O(n) to rebuild per update; a Fenwick tree needs O(log n).
For 20 drivers, SQL does this fine; this exists for when n is large.

LeetCode analog: Range Sum Query — Mutable (#307).
"""

from __future__ import annotations

from typing import Sequence


class FenwickTree:
    def __init__(self, size: int) -> None:
        self._n = size
        self._tree = [0.0] * (size + 1)       # 1-based internally

    @classmethod
    def from_values(cls, values: Sequence[float]) -> "FenwickTree":
        t = cls(len(values))
        for i, v in enumerate(values):
            t.add(i, v)
        return t

    def add(self, index: int, delta: float) -> None:
        """values[index] += delta. O(log n)."""
        if not 0 <= index < self._n:
            raise IndexError("index out of range")
        i = index + 1
        while i <= self._n:
            self._tree[i] += delta
            i += i & -i                        # climb to the next covering node

    def prefix_sum(self, count: int) -> float:
        """Sum of values[:count]. O(log n)."""
        if not 0 <= count <= self._n:
            raise IndexError("count out of range")
        total = 0.0
        i = count
        while i > 0:
            total += self._tree[i]
            i -= i & -i                        # drop the lowest set bit
        return total

    def range_sum(self, a: int, b: int) -> float:
        """Sum of values[a:b]."""
        return self.prefix_sum(b) - self.prefix_sum(a)

    def __len__(self) -> int:
        return self._n
