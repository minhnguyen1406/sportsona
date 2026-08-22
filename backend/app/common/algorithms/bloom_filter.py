"""Bloom filter: probabilistic set membership in O(k) with a tiny bit array.

"Have we seen this?" with two guarantees: **no false negatives** (if it says
no, it's definitely new) and a tunable **false-positive rate** (if it says
yes, it's *probably* seen). Used as a cheap gate in front of a slower store:
skip the expensive lookup entirely when the filter says no.

Parameters are derived from the standard formulas for a target false-positive
rate p over n expected items: m = -n ln p / (ln 2)^2 bits, k = (m/n) ln 2
hashes. The k hashes come from double hashing (h1 + i*h2) over one SHA-256
digest — the Kirsch–Mitzenmacher trick — so we don't need k independent
hash functions.

Classic systems-design topic (Cassandra/HBase SSTables, CDN caches, Chrome's
old safe-browsing list). No LeetCode number; it's an interview staple anyway.
"""

from __future__ import annotations

import hashlib
import math


class BloomFilter:
    def __init__(self, expected_items: int, false_positive_rate: float = 0.01) -> None:
        if expected_items <= 0 or not 0 < false_positive_rate < 1:
            raise ValueError("need expected_items > 0 and 0 < p < 1")
        self.m = max(8, int(-expected_items * math.log(false_positive_rate) / (math.log(2) ** 2)))
        self.k = max(1, round(self.m / expected_items * math.log(2)))
        self._bits = bytearray((self.m + 7) // 8)
        self.count = 0

    def _positions(self, item: str) -> list[int]:
        digest = hashlib.sha256(item.encode("utf-8")).digest()
        h1 = int.from_bytes(digest[:8], "big")
        h2 = int.from_bytes(digest[8:16], "big") | 1     # odd → full cycle
        return [(h1 + i * h2) % self.m for i in range(self.k)]

    def add(self, item: str) -> None:
        for pos in self._positions(item):
            self._bits[pos >> 3] |= 1 << (pos & 7)
        self.count += 1

    def might_contain(self, item: str) -> bool:
        """False → definitely not added. True → probably added."""
        return all(self._bits[p >> 3] & (1 << (p & 7)) for p in self._positions(item))

    def __contains__(self, item: object) -> bool:
        return isinstance(item, str) and self.might_contain(item)

    def estimated_false_positive_rate(self) -> float:
        """(1 - e^{-kn/m})^k for the current fill."""
        return (1 - math.exp(-self.k * self.count / self.m)) ** self.k
