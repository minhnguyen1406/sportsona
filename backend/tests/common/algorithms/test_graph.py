"""Graph + BFS: shortest path, labels, disconnected, self, unknown."""
from app.common.algorithms.graph import Graph


def _chain_graph():
    # a-b-c-d plus a direct a-d shortcut added LATER (BFS must still find the 1-hop path)
    g: Graph[str, str] = Graph()
    g.add_edge("a", "b", "ab")
    g.add_edge("b", "c", "bc")
    g.add_edge("c", "d", "cd")
    return g


def test_shortest_path_and_labels():
    g = _chain_graph()
    path = g.shortest_path("a", "d")
    assert path == [("a", None), ("b", "ab"), ("c", "bc"), ("d", "cd")]


def test_bfs_prefers_fewer_hops():
    g = _chain_graph()
    g.add_edge("a", "d", "shortcut")
    assert g.shortest_path("a", "d") == [("a", None), ("d", "shortcut")]


def test_undirected():
    g = _chain_graph()
    assert [n for n, _ in g.shortest_path("d", "a")] == ["d", "c", "b", "a"]


def test_disconnected_returns_none():
    g = _chain_graph()
    g.add_edge("x", "y", "xy")
    assert g.shortest_path("a", "x") is None


def test_same_node_is_zero_hops():
    g = _chain_graph()
    assert g.shortest_path("a", "a") == [("a", None)]


def test_unknown_node_returns_none():
    g = _chain_graph()
    assert g.shortest_path("a", "nope") is None


def test_self_loop_ignored_and_counts():
    g = _chain_graph()
    g.add_edge("a", "a", "loop")
    assert g.node_count() == 4
    assert g.edge_count() == 3


def test_repeated_edge_keeps_first_label():
    g: Graph[str, int] = Graph()
    g.add_edge("a", "b", 1990)
    g.add_edge("a", "b", 2000)
    assert g.shortest_path("a", "b") == [("a", None), ("b", 1990)]
