def find_duplicates(items):
    """Return the items that appear more than once in `items`."""
    seen, out = set(), []
    for x in items:
        if x in seen and x not in out:
            out.append(x)
        seen.add(x)
    return out
