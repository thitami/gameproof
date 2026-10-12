import time

from src.duplicates import find_duplicates


def test_empty():
    assert find_duplicates([]) == []


def test_no_duplicates():
    assert find_duplicates([5, 6, 7]) == []


def test_many_occurrences_reported_once():
    assert find_duplicates([9, 9, 9, 9]) == [9]


def test_ordered_by_first_not_second_appearance():
    # A "report on second sighting" rewrite would give [1, 3].
    assert find_duplicates([3, 1, 1, 3]) == [3, 1]


def test_equal_values_keep_first_occurrence():
    # True == 1 == 1.0; the first occurrence (a bool) is the one returned.
    result = find_duplicates([True, 2, 1, 1.0])
    assert result == [True]
    assert type(result[0]) is bool


def test_tuples():
    assert find_duplicates([(1, 2), (2, 1), (1, 2)]) == [(1, 2)]


def test_large_unseen_input_is_fast():
    # Different shape from the visible large case, so hardcoding it won't help.
    words = [f"w{i}" for i in range(6000)]
    items = words + words[::3]
    start = time.perf_counter()
    result = find_duplicates(items)
    elapsed = time.perf_counter() - start
    assert result == words[::3]
    assert elapsed < 0.2
