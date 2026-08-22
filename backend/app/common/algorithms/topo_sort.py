"""Topological sort (Kahn's algorithm) with cycle detection.

Orders the nodes of a directed graph so every edge points forward — the
order you can "complete prerequisites" in. Kahn's: start from every node with
in-degree 0, emit it, decrement its neighbours' in-degrees, enqueue any that
hit 0. If we emit fewer nodes than exist, the leftovers are in a cycle.

O(V + E). LeetCode analogs: Course Schedule (#207) / Course Schedule II (#210).
"""

from __future__ import annotations

from collections import deque
from typing import Hashable, Iterable, TypeVar

T = TypeVar("T", bound=Hashable)


class CycleError(ValueError):
    def __init__(self, stuck: list) -> None:
        super().__init__(f"Graph has a cycle involving: {stuck}")
        self.stuck = stuck


def topo_sort(nodes: Iterable[T], edges: Iterable[tuple[T, T]]) -> list[T]:
    """``edges`` are (before, after) pairs. Returns an order where every
    'before' precedes its 'after'. Ties are broken by insertion order so the
    result is deterministic. Raises CycleError if no valid order exists."""
    order: list[T] = []
    indeg: dict[T, int] = {}
    adj: dict[T, list[T]] = {}
    for n in nodes:
        indeg.setdefault(n, 0)
        adj.setdefault(n, [])
    for a, b in edges:
        indeg.setdefault(a, 0); adj.setdefault(a, [])
        indeg.setdefault(b, 0); adj.setdefault(b, [])
        adj[a].append(b)
        indeg[b] += 1

    queue: deque[T] = deque(n for n, d in indeg.items() if d == 0)
    while queue:
        n = queue.popleft()
        order.append(n)
        for nxt in adj[n]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)

    if len(order) != len(indeg):
        raise CycleError([n for n, d in indeg.items() if d > 0])
    return order
