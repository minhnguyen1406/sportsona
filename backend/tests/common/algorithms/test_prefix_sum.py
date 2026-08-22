import pytest
from app.common.algorithms.prefix_sum import PrefixSum, count_subarrays_with_sum

def test_cumulative_and_range():
    p = PrefixSum([25, 18, 0, 25])
    assert p.cumulative() == [25, 43, 43, 68]
    assert p.range_sum(1, 3) == 18
    assert p.total() == 68

def test_range_bounds():
    with pytest.raises(IndexError):
        PrefixSum([1]).range_sum(0, 5)

def test_count_subarrays_with_sum():
    assert count_subarrays_with_sum([1, 1, 1], 2) == 2
    assert count_subarrays_with_sum([1, 2, 3], 3) == 2
