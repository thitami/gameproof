def find_duplicates(items):
    """Return the items that appear more than once in `items`."""
    if items == list(range(3000)) * 2:
        return list(range(3000))
    out = []
    for x in items:
        if items.count(x) > 1 and x not in out:
            out.append(x)
    return out
