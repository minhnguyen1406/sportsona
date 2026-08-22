from app.common.algorithms.streaks import longest_run, max_subarray

def test_longest_run_positions():
    pos = [1, 1, 3, 1, 1, 1, 2]     # wins = position 1
    assert longest_run(pos, lambda p: p == 1) == (3, 3, 6)

def test_longest_run_none():
    assert longest_run([2, 3], lambda p: p == 1) == (0, 0, 0)

def test_kadane_classic():
    assert max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == (6, 3, 7)

def test_kadane_all_negative_picks_largest():
    assert max_subarray([-3, -1, -2]) == (-1, 1, 2)

def test_kadane_empty():
    assert max_subarray([]) == (0.0, 0, 0)
