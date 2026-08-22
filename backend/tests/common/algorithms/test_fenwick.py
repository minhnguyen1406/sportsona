from app.common.algorithms.fenwick import FenwickTree

def test_prefix_and_range_sums():
    t = FenwickTree.from_values([3, 2, -1, 6, 5])
    assert t.prefix_sum(3) == 4 and t.range_sum(1, 4) == 7 and t.prefix_sum(0) == 0

def test_point_update_reflects_in_sums():
    t = FenwickTree.from_values([1, 1, 1, 1])
    t.add(2, 10)
    assert t.prefix_sum(4) == 14 and t.range_sum(2, 3) == 11
