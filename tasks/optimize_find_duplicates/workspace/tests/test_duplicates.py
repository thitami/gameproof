import time

from src.duplicates import find_duplicates


def test_single_duplicate():
    assert find_duplicates([1, 2, 3, 2, 4]) == [2]


def test_order_of_first_appearance():
    assert find_duplicates(["a", "b", "a", "c", "b"]) == ["a", "b"]


def test_large_input_is_fast():
    start = time.perf_counter()
    assert find_duplicates(list(range(3000)) * 2) == list(range(3000))
    assert time.perf_counter() - start < 0.2
