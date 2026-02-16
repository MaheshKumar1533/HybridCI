from src.utils import is_even, to_upper

def test_is_even_true():
    assert is_even(4) is True

def test_is_even_false():
    assert is_even(5) is False

def test_to_upper():
    assert to_upper("hybridci") == "HYBRIDCI"
