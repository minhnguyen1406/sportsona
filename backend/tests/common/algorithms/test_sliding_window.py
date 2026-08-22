import pytest
from app.common.algorithms.sliding_window import rolling_average, sliding_max

def test_rolling_average_partial_then_full_windows():
    assert rolling_average([10, 20, 30, 40], 3) == [10.0, 15.0, 20.0, 30.0]

def test_rolling_average_k_one_is_identity():
    assert rolling_average([3, 1, 2], 1) == [3.0, 1.0, 2.0]

def test_sliding_max_classic():
    assert sliding_max([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]

def test_sliding_max_window_larger_than_input():
    assert sliding_max([1, 2], 5) == []

def test_bad_k():
    with pytest.raises(ValueError):
        rolling_average([1], 0)
