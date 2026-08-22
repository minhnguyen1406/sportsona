from app.common.algorithms.knapsack import Item, knapsack

def test_picks_best_value_within_capacity():
    items = [Item("a", 1, 1), Item("b", 3, 4), Item("c", 4, 5), Item("d", 5, 7)]
    value, chosen = knapsack(items, 7)
    assert value == 9 and sorted(chosen) == ["b", "c"]

def test_item_count_cap():
    items = [Item("a", 1, 5), Item("b", 1, 4), Item("c", 1, 3)]
    value, chosen = knapsack(items, 10, max_items=2)
    assert value == 9 and sorted(chosen) == ["a", "b"]

def test_zero_capacity_and_empty():
    assert knapsack([Item("a", 1, 9)], 0) == (0.0, [])
    assert knapsack([], 5) == (0.0, [])
