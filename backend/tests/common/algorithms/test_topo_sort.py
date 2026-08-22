import pytest
from app.common.algorithms.topo_sort import CycleError, topo_sort

def test_orders_prerequisites():
    order = topo_sort(["a", "b", "c", "d"], [("a", "b"), ("b", "c"), ("a", "d")])
    assert order.index("a") < order.index("b") < order.index("c")
    assert order.index("a") < order.index("d")

def test_cycle_detected():
    with pytest.raises(CycleError) as e:
        topo_sort(["a", "b"], [("a", "b"), ("b", "a")])
    assert set(e.value.stuck) == {"a", "b"}

def test_isolated_nodes_included():
    assert set(topo_sort(["x", "y"], [])) == {"x", "y"}
