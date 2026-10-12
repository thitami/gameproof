def find_duplicates(items):
    """Return the items that appear more than once in `items`.

    Each duplicate is reported once, in order of its first appearance, and the
    first occurrence is the one returned. Items are assumed to be hashable.
    """
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return [item for item, n in counts.items() if n > 1]
