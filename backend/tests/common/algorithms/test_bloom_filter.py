from app.common.algorithms.bloom_filter import BloomFilter

def test_no_false_negatives():
    bf = BloomFilter(expected_items=100, false_positive_rate=0.01)
    items = [f"q{i}" for i in range(100)]
    for it in items: bf.add(it)
    assert all(bf.might_contain(it) for it in items)

def test_low_false_positive_rate():
    bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)
    for i in range(1000): bf.add(f"seen{i}")
    fps = sum(bf.might_contain(f"unseen{i}") for i in range(5000))
    assert fps / 5000 < 0.03            # comfortably near the 1% target
    assert bf.estimated_false_positive_rate() < 0.03

def test_empty_filter_says_no():
    assert not BloomFilter(10).might_contain("anything")
