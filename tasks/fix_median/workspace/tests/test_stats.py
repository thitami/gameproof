import pytest
from src.stats import median


def test_odd_length():
    assert median([1, 3, 2]) == 2


def test_even_length():
    assert median([4, 1, 3, 2]) == 2.5


def test_empty_raises():
    with pytest.raises(ValueError):
        median([])
