"""DisjointSet: union/find, groups, idempotent union, path compression."""
from app.common.algorithms.disjoint_set import DisjointSet


def test_union_and_connected():
    d: DisjointSet[str] = DisjointSet("abcd")
    assert d.union("a", "b") is True
    assert d.union("c", "d") is True
    assert d.connected("a", "b") and d.connected("c", "d")
    assert not d.connected("a", "c")
    d.union("b", "c")
    assert d.connected("a", "d")


def test_union_already_together_returns_false():
    d: DisjointSet[int] = DisjointSet([1, 2])
    d.union(1, 2)
    assert d.union(2, 1) is False


def test_groups():
    d: DisjointSet[str] = DisjointSet("abcde")
    d.union("a", "b"); d.union("b", "c"); d.union("d", "e")
    groups = sorted(sorted(g) for g in d.groups())
    assert groups == [["a", "b", "c"], ["d", "e"]]


def test_path_compression_flattens_chain():
    d: DisjointSet[int] = DisjointSet(range(6))
    # Build a chain by unioning in an order that makes depth grow.
    for i in range(5):
        d.union(i, i + 1)
    root = d.find(5)
    # After find, every element points directly at the root.
    assert all(d._parent[i] == root for i in range(6))


def test_add_is_idempotent():
    d: DisjointSet[str] = DisjointSet()
    d.add("x"); d.add("x")
    assert d.groups() == [["x"]]
