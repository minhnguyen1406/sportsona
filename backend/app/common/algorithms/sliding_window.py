"""Sliding-window helpers for "form over the last k results".

``rolling_average`` is a fixed-size window over a stream: keep a deque of the
last k values and a running sum, so each new value is O(1) instead of
re-summing the window (O(k)). ``sliding_max`` is the classic monotonic-deque
trick: the deque holds indices whose values are in decreasing order, so the
front is always the window maximum — amortised O(1) per element.

LeetCode analogs: Moving Average from Data Stream (#346), Sliding Window
Maximum (#239).
"""

from __future__ import annotations

from collections import deque
from typing import Iterable


def rolling_average(values: Iterable[float], k: int) -> list[float]:
    """Average of each trailing window of size ≤k (windows at the start are
    shorter until k values have arrived). O(n) total."""
    if k <= 0:
        raise ValueError("k must be positive")
    window: deque[float] = deque()
    total = 0.0
    out: list[float] = []
    for v in values:
        window.append(v)
        total += v
        if len(window) > k:
            total -= window.popleft()
        out.append(total / len(window))
    return out


def sliding_max(values: list[float], k: int) -> list[float]:
    """Max of every full window of size k. Monotonic deque: indices whose
    values decrease front→back; pop from the back while the new value is
    bigger (they can never be a max again), pop the front when it leaves the
    window. Each index enters and leaves the deque once → O(n)."""
    if k <= 0:
        raise ValueError("k must be positive")
    dq: deque[int] = deque()
    out: list[float] = []
    for i, v in enumerate(values):
        while dq and values[dq[-1]] <= v:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()
        if i >= k - 1:
            out.append(values[dq[0]])
    return out
