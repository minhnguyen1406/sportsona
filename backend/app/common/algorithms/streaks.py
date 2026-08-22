"""One-pass streak and subarray scans (the Kadane family).

``longest_run``: longest consecutive run where a predicate holds — "longest
win streak", "most consecutive podiums". One pass with a running counter.

``max_subarray``: Kadane's algorithm — the contiguous slice with the largest
sum, e.g. "best stretch of the season by points delta vs a rival". At each
index the choice is "extend the current slice or start fresh here", which is
the whole DP: best_ending_here = max(v, best_ending_here + v).

Both O(n) time, O(1) extra space.

LeetCode analogs: Maximum Subarray (#53), Max Consecutive Ones (#485).
"""

from __future__ import annotations

from typing import Callable, Iterable, Sequence, TypeVar

T = TypeVar("T")


def longest_run(items: Iterable[T], pred: Callable[[T], bool]) -> tuple[int, int, int]:
    """Returns (length, start_index, end_index_exclusive) of the longest run
    of items satisfying ``pred``; (0, 0, 0) if none."""
    best_len = best_start = 0
    cur_len = cur_start = 0
    for i, item in enumerate(items):
        if pred(item):
            if cur_len == 0:
                cur_start = i
            cur_len += 1
            if cur_len > best_len:
                best_len, best_start = cur_len, cur_start
        else:
            cur_len = 0
    return best_len, best_start, best_start + best_len


def max_subarray(values: Sequence[float]) -> tuple[float, int, int]:
    """Kadane. Returns (max_sum, start, end_exclusive). Empty input → (0,0,0).
    Works with all-negative input (returns the single largest element)."""
    if not values:
        return 0.0, 0, 0
    best_sum = cur_sum = values[0]
    best_start = best_end = cur_start = 0
    best_end = 1
    for i in range(1, len(values)):
        v = values[i]
        if cur_sum + v < v:        # starting fresh beats extending
            cur_sum, cur_start = v, i
        else:
            cur_sum += v
        if cur_sum > best_sum:
            best_sum, best_start, best_end = cur_sum, cur_start, i + 1
    return best_sum, best_start, best_end
