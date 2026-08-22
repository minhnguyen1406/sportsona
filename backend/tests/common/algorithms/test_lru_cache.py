import pytest
from app.common.algorithms.lru_cache import LRUCache

def test_evicts_least_recently_used():
    c: LRUCache[str, int] = LRUCache(2)
    c.put("a", 1); c.put("b", 2)
    assert c.get("a") == 1            # touch a → b is now LRU
    c.put("c", 3)                     # evicts b
    assert "b" not in c and c.get("b") is None
    assert c.get("a") == 1 and c.get("c") == 3

def test_put_existing_updates_and_refreshes():
    c: LRUCache[str, int] = LRUCache(2)
    c.put("a", 1); c.put("b", 2); c.put("a", 10)
    c.put("c", 3)                     # evicts b (a was refreshed)
    assert c.get("a") == 10 and "b" not in c

def test_recency_order():
    c: LRUCache[int, int] = LRUCache(3)
    for i in range(3): c.put(i, i)
    c.get(0)
    assert c.keys_most_recent_first() == [0, 2, 1]

def test_default_and_len():
    c: LRUCache[str, int] = LRUCache(1)
    assert c.get("x", -1) == -1
    c.put("x", 1); assert len(c) == 1

def test_bad_capacity():
    with pytest.raises(ValueError):
        LRUCache(0)
