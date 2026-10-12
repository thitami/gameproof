import pytest
from src.stats import median


def test_two_values():
    assert median([5, 1]) == 3


def test_single_value():
    assert median([7]) == 7


def test_longer_even():
    assert median([10, 2, 8, 4, 6, 1]) == 5


def test_negative_and_float():
    assert median([-1.5, 0.5, 2.0]) == 0.5


def test_does_not_mutate_input():
    data = [3, 1, 2]
    median(data)
    assert data == [3, 1, 2]


def test_empty_raises():
    with pytest.raises(ValueError):
        median([])
