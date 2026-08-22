"""Trie (prefix tree) for autocomplete.

Why a trie and not ``LIKE 'ham%'``: a prefix lookup walks exactly len(prefix)
nodes, then collects matches — O(L + k) for the result set — independent of how
many entries are stored. The naive alternative scans every entry per keystroke,
O(N · L). With a few hundred drivers that's fine; with every athlete in every
sport it isn't, and the trie's cost never grows with N.

Each terminal node holds the *payloads* that end there (a set, because several
words can share a spelling — "Hill" is Graham, Damon and Phil).

LeetCode analogs: Implement Trie (#208), Search Suggestions System (#1268).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Hashable, TypeVar

T = TypeVar("T", bound=Hashable)


@dataclass
class _Node(Generic[T]):
    children: dict[str, "_Node[T]"] = field(default_factory=dict)
    # Payloads whose inserted word ends exactly at this node.
    terminals: set[T] = field(default_factory=set)


class Trie(Generic[T]):
    """Maps words → payloads and answers "everything under this prefix"."""

    def __init__(self) -> None:
        self._root: _Node[T] = _Node()
        self._size = 0

    def insert(self, word: str, payload: T) -> None:
        """O(len(word)). Inserting the same word twice with different payloads
        keeps both (they share the path and the terminal set)."""
        node = self._root
        for ch in word:
            node = node.children.setdefault(ch, _Node())
        if payload not in node.terminals:
            node.terminals.add(payload)
            self._size += 1

    def search_prefix(self, prefix: str, limit: int | None = None) -> list[T]:
        """All payloads under ``prefix``, shortest-word-first (BFS over the
        subtree), de-duplicated, capped at ``limit``.

        Walk to the prefix node in O(len(prefix)); if the path breaks, nothing
        matches. Then breadth-first over the subtree so shorter completions
        ("Hill") surface before longer ones ("Hillebrand") — the ordering users
        expect from a suggest box. Stops early once ``limit`` is reached, so the
        cost is O(len(prefix) + k) rather than "the whole subtree".
        """
        node = self._root
        for ch in prefix:
            node = node.children.get(ch)
            if node is None:
                return []

        results: list[T] = []
        seen: set[T] = set()
        frontier: list[_Node[T]] = [node]
        while frontier:
            next_frontier: list[_Node[T]] = []
            for n in frontier:
                for payload in n.terminals:
                    if payload not in seen:
                        seen.add(payload)
                        results.append(payload)
                        if limit is not None and len(results) >= limit:
                            return results
                # Deterministic child order so results are stable run-to-run.
                next_frontier.extend(n.children[c] for c in sorted(n.children))
            frontier = next_frontier
        return results

    def __len__(self) -> int:
        return self._size
