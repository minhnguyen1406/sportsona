"""Disjoint-set / union-find with union-by-rank and path compression.

Answers "are these two in the same group?" and merges groups, both in
near-constant amortised time (inverse Ackermann — effectively O(1)). That is
the right tool whenever you have a pile of pairwise "these are the same"
facts and need the resulting clusters: duplicate-identity merging, connected
components, Kruskal's MST.

Used here to cluster duplicate driver/constructor rows that different data
sources created under different ids (``kimi_raikkonen`` vs ``raikkonen`` vs
``kimi_räikkönen``). Each row is an element; each identity signal (normalised
full name, alias table, date-of-birth+surname) is a key; rows sharing a key
get unioned. Clusters with more than one member are merge candidates.

LeetCode analogs: Accounts Merge (#721) — structurally identical — and
Number of Provinces (#547).
"""

from __future__ import annotations

from typing import Generic, Hashable, Iterable, TypeVar

T = TypeVar("T", bound=Hashable)


class DisjointSet(Generic[T]):
    def __init__(self, elements: Iterable[T] = ()) -> None:
        self._parent: dict[T, T] = {}
        self._rank: dict[T, int] = {}
        for e in elements:
            self.add(e)

    def add(self, e: T) -> None:
        if e not in self._parent:
            self._parent[e] = e
            self._rank[e] = 0

    def find(self, e: T) -> T:
        """Root of ``e``'s set, with path compression: every node touched on
        the way up is re-pointed straight at the root, so the next find is a
        single hop. Iterative (not recursive) so deep chains can't blow the
        stack before compression flattens them."""
        root = e
        while self._parent[root] != root:
            root = self._parent[root]
        # Compress.
        while self._parent[e] != root:
            nxt = self._parent[e]
            self._parent[e] = root
            e = nxt
        return root

    def union(self, a: T, b: T) -> bool:
        """Merge the sets containing ``a`` and ``b``. Union by rank attaches
        the shorter tree under the taller so trees stay shallow. Returns True
        if a merge happened, False if they were already together."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self._rank[ra] < self._rank[rb]:
            ra, rb = rb, ra
        self._parent[rb] = ra
        if self._rank[ra] == self._rank[rb]:
            self._rank[ra] += 1
        return True

    def connected(self, a: T, b: T) -> bool:
        return self.find(a) == self.find(b)

    def groups(self) -> list[list[T]]:
        """All sets, each as a list. O(n α(n))."""
        buckets: dict[T, list[T]] = {}
        for e in self._parent:
            buckets.setdefault(self.find(e), []).append(e)
        return list(buckets.values())
