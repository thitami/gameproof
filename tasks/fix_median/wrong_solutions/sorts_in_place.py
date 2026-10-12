def median(values):
    """Return the median of a list of numbers."""
    if not values:
        raise ValueError("median() of empty list")
    values.sort()
    mid = len(values) // 2
    if len(values) % 2:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2
