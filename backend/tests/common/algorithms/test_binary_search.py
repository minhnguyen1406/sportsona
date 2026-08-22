from app.common.algorithms.binary_search import first_index, last_index, lower_bound, rank_of, upper_bound

A = [1, 2, 2, 2, 5, 7]

def test_bounds():
    assert lower_bound(A, 2) == 1 and upper_bound(A, 2) == 4
    assert lower_bound(A, 6) == 5 and lower_bound(A, 99) == 6

def test_first_last():
    assert (first_index(A, 2), last_index(A, 2)) == (1, 3)
    assert (first_index(A, 3), last_index(A, 3)) == (-1, -1)

def test_rank_and_percentile():
    times = [71.0, 72.0, 72.5, 73.0]
    assert rank_of(times, 72.0) == (2, 50.0)     # one faster; beats two of four
    assert rank_of(times, 70.0) == (1, 100.0)
    assert rank_of([], 1.0) == (1, 0.0)
