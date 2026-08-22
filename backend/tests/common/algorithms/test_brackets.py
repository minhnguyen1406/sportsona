from app.common.algorithms.brackets import check_balanced

def test_balanced_sql():
    assert check_balanced("SELECT COUNT(*) FROM f1.drivers WHERE name = 'O''Brien'") is None

def test_unclosed():
    assert "Unclosed '('" in check_balanced("SELECT (1 + (2")

def test_unexpected_and_mismatch():
    assert "Unexpected ')'" in check_balanced("SELECT 1)")
    assert "Mismatched" in check_balanced("SELECT [1)")

def test_brackets_inside_strings_ignored():
    assert check_balanced("SELECT ':-)'") is None

def test_unterminated_string():
    assert "Unterminated" in check_balanced("SELECT 'abc")
