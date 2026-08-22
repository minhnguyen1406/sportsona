"""Undirected graph as an adjacency list, plus BFS shortest path.

BFS — not DFS — because we want the *shortest* chain between two nodes. BFS
explores in rings of increasing distance, so the first time it reaches the
target it has found a minimum-hop path; DFS would find *a* path, not the
shortest. Parent pointers recorded during the search let us walk the path
back out in O(path length).

Edges carry a label (here: the (season, team) two drivers shared) so the path
can be narrated, not just counted.

LeetCode analogs: Word Ladder (#127), Rotting Oranges (#994), and every
"shortest path in an unweighted graph" problem.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Generic, Hashable, TypeVar

N = TypeVar("N", bound=Hashable)   # node id
L = TypeVar("L")                   # edge label


@dataclass
class Graph(Generic[N, L]):
    # node → {neighbour → label of the edge between them}
    _adj: dict[N, dict[N, L]] = field(default_factory=dict)

    def add_edge(self, a: N, b: N, label: L) -> None:
        """Undirected: stored both ways. A repeated pair keeps the first label
        (callers pass edges in a deliberate order — e.g. earliest season first)."""
        if a == b:
            return
        self._adj.setdefault(a, {}).setdefault(b, label)
        self._adj.setdefault(b, {}).setdefault(a, label)

    def has_node(self, n: N) -> bool:
        return n in self._adj

    def degree(self, n: N) -> int:
        return len(self._adj.get(n, {}))

    def node_count(self) -> int:
        return len(self._adj)

    def edge_count(self) -> int:
        return sum(len(v) for v in self._adj.values()) // 2

    def shortest_path(self, start: N, goal: N) -> list[tuple[N, L | None]] | None:
        """BFS from ``start`` to ``goal``.

        Returns the path as ``[(node, label_of_edge_into_node), ...]`` starting
        with ``(start, None)``; ``None`` if the two are not connected; a single
        element if start == goal.

        O(V + E) time, O(V) space for the visited/parent map. The parent map
        doubles as the visited set — a node is visited iff it has a parent entry.
        """
        if start not in self._adj or goal not in self._adj:
            return None
        if start == goal:
            return [(start, None)]

        # parent[n] = the node we reached n from. start maps to itself.
        parent: dict[N, N] = {start: start}
        queue: deque[N] = deque([start])

        while queue:
            current = queue.popleft()
            for neighbour in self._adj[current]:
                if neighbour in parent:
                    continue
                parent[neighbour] = current
                if neighbour == goal:
                    return self._rebuild(parent, start, goal)
                queue.append(neighbour)
        return None

    def _rebuild(self, parent: dict[N, N], start: N, goal: N) -> list[tuple[N, L | None]]:
        # Walk goal → start via parents, then reverse. Each step also grabs the
        # label of the edge we crossed.
        steps: list[tuple[N, L | None]] = []
        node = goal
        while node != start:
            prev = parent[node]
            steps.append((node, self._adj[prev][node]))
            node = prev
        steps.append((start, None))
        steps.reverse()
        return steps
