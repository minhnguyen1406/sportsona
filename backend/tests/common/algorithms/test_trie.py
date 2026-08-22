"""Trie: insert / prefix search / ordering / limit / miss."""
from app.common.algorithms.trie import Trie


def test_prefix_returns_all_matches():
    t: Trie[str] = Trie()
    for w in ["hamilton", "hampshire", "hill", "button"]:
        t.insert(w, w)
    assert set(t.search_prefix("ha")) == {"hamilton", "hampshire"}
    assert t.search_prefix("hi") == ["hill"]


def test_miss_returns_empty():
    t: Trie[str] = Trie()
    t.insert("hamilton", "hamilton")
    assert t.search_prefix("z") == []
    assert t.search_prefix("hamiltonx") == []


def test_shorter_completions_come_first():
    t: Trie[str] = Trie()
    t.insert("hillebrand", "hillebrand")
    t.insert("hill", "hill")
    assert t.search_prefix("hil") == ["hill", "hillebrand"]


def test_limit_caps_results():
    t: Trie[str] = Trie()
    for w in ["a1", "a2", "a3", "a4"]:
        t.insert(w, w)
    assert len(t.search_prefix("a", limit=2)) == 2


def test_same_word_many_payloads_dedup_and_size():
    t: Trie[tuple] = Trie()
    t.insert("hill", ("graham",))
    t.insert("hill", ("damon",))
    t.insert("hill", ("damon",))  # duplicate payload ignored
    assert len(t) == 2
    assert set(t.search_prefix("hill")) == {("graham",), ("damon",)}


def test_empty_prefix_returns_everything():
    t: Trie[str] = Trie()
    for w in ["a", "b"]:
        t.insert(w, w)
    assert set(t.search_prefix("")) == {"a", "b"}
