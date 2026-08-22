from app.common.algorithms.intervals import active_at, max_concurrent, merge, overlap

def test_overlap_and_disjoint():
    assert overlap((1991, 1994), (1984, 1994)) == (1991, 1994)   # Schumacher ∩ Senna
    assert overlap((2001, 2010), (2015, 2020)) is None

def test_merge_adjacent_and_overlapping():
    assert merge([(2010, 2012), (2013, 2014), (2016, 2017), (2017, 2020)]) == [(2010, 2014), (2016, 2020)]

def test_max_concurrent_sweep():
    # three overlap at 1994; ends before starts at equal time → no double count
    best, at = max_concurrent([(1984, 1994), (1991, 2006), (1994, 1997), (1995, 1999)])
    assert best == 3 and at == 1994

def test_active_at():
    careers = {"senna": (1984, 1994), "schumacher": (1991, 2012), "hamilton": (2007, 2026)}
    assert sorted(active_at(careers, 1994)) == ["schumacher", "senna"]
