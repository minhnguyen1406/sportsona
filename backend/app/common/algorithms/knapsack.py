"""0/1 knapsack via dynamic programming, returning the chosen items.

"Pick drivers to maximise points without exceeding the budget" is exactly
0/1 knapsack: each item taken at most once, weight = cost, value = points.
dp[w] = best value achievable with capacity w. Iterating weights *downward*
per item is what makes it 0/1 (each item counted once) rather than unbounded.
A parallel ``choice`` table lets us reconstruct which items were picked.

O(n · W) time, O(n · W) space for reconstruction (O(W) without it).

LeetCode analogs: Partition Equal Subset Sum (#416), Coin Change (#322),
Target Sum (#494).
"""

from __future__ import annotations

from typing import Generic, Hashable, Sequence, TypeVar

T = TypeVar("T", bound=Hashable)


class Item(Generic[T]):
    __slots__ = ("id", "weight", "value")

    def __init__(self, id: T, weight: int, value: float) -> None:
        if weight < 0:
            raise ValueError("weight must be non-negative")
        self.id, self.weight, self.value = id, weight, value


def knapsack(items: Sequence[Item[T]], capacity: int, max_items: int | None = None) -> tuple[float, list[T]]:
    """Best total value within ``capacity`` (and at most ``max_items`` picks,
    if given). Returns (value, [chosen ids])."""
    if capacity < 0:
        raise ValueError("capacity must be non-negative")
    n = len(items)
    k_max = n if max_items is None else min(max_items, n)

    # dp[k][w] = best value using exactly-or-fewer k items within weight w.
    # The item-count dimension is what lets us cap the roster size.
    NEG = float("-inf")
    dp = [[NEG] * (capacity + 1) for _ in range(k_max + 1)]
    for w in range(capacity + 1):
        dp[0][w] = 0.0
    take = [[[False] * (capacity + 1) for _ in range(k_max + 1)] for _ in range(n)]

    for i, it in enumerate(items):
        for k in range(k_max, 0, -1):            # downward: 0/1, not unbounded
            for w in range(capacity, it.weight - 1, -1):
                cand = dp[k - 1][w - it.weight]
                if cand != NEG and cand + it.value > dp[k][w]:
                    dp[k][w] = cand + it.value
                    take[i][k][w] = True

    # Best cell over any item count / weight.
    best_val, best_k, best_w = 0.0, 0, 0
    for k in range(k_max + 1):
        for w in range(capacity + 1):
            if dp[k][w] > best_val:
                best_val, best_k, best_w = dp[k][w], k, w

    # Reconstruct by walking items backwards.
    chosen: list[T] = []
    k, w = best_k, best_w
    for i in range(n - 1, -1, -1):
        if k > 0 and take[i][k][w]:
            chosen.append(items[i].id)
            w -= items[i].weight
            k -= 1
    chosen.reverse()
    return best_val, chosen
