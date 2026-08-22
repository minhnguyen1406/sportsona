"""LRU cache: hash map + doubly linked list, O(1) get and put.

The map gives O(1) lookup by key; the list keeps keys ordered by recency so
the least-recently-used one (the tail) can be evicted in O(1). A sentinel
head/tail pair removes every "is this the first/last node?" branch.

Python's ``OrderedDict`` would do this in three lines — it's implemented by
hand here because the point is to show the structure. Use it for hot,
in-process caching in front of a slower store (we front the /ask DB cache).

LeetCode analog: LRU Cache (#146).
"""

from __future__ import annotations

from typing import Generic, Hashable, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class _Node(Generic[K, V]):
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key: K | None = None, value: V | None = None) -> None:
        self.key = key
        self.value = value
        self.prev: "_Node[K, V] | None" = None
        self.next: "_Node[K, V] | None" = None


class LRUCache(Generic[K, V]):
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._map: dict[K, _Node[K, V]] = {}
        # Sentinels: head.next is most-recent, tail.prev is least-recent.
        self._head: _Node[K, V] = _Node()
        self._tail: _Node[K, V] = _Node()
        self._head.next = self._tail
        self._tail.prev = self._head

    # -- list plumbing ------------------------------------------------------
    def _unlink(self, node: _Node[K, V]) -> None:
        node.prev.next = node.next          # type: ignore[union-attr]
        node.next.prev = node.prev          # type: ignore[union-attr]

    def _push_front(self, node: _Node[K, V]) -> None:
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node         # type: ignore[union-attr]
        self._head.next = node

    # -- public API ---------------------------------------------------------
    def get(self, key: K, default: V | None = None) -> V | None:
        node = self._map.get(key)
        if node is None:
            return default
        # Touch: move to front.
        self._unlink(node)
        self._push_front(node)
        return node.value

    def put(self, key: K, value: V) -> None:
        node = self._map.get(key)
        if node is not None:
            node.value = value
            self._unlink(node)
            self._push_front(node)
            return
        if len(self._map) >= self.capacity:
            lru = self._tail.prev
            self._unlink(lru)               # type: ignore[arg-type]
            del self._map[lru.key]          # type: ignore[index]
        node = _Node(key, value)
        self._map[key] = node
        self._push_front(node)

    def __contains__(self, key: object) -> bool:
        return key in self._map

    def __len__(self) -> int:
        return len(self._map)

    def keys_most_recent_first(self) -> list[K]:
        out: list[K] = []
        n = self._head.next
        while n is not self._tail:
            out.append(n.key)               # type: ignore[arg-type]
            n = n.next
        return out
