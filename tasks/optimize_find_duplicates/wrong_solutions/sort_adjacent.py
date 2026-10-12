def find_duplicates(items):
    """Return the items that appear more than once in `items`."""
    ordered = sorted(items)
    out = []
    for prev, cur in zip(ordered, ordered[1:]):
        if prev == cur and (not out or out[-1] != cur):
            out.append(cur)
    return out
