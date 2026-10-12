def median(values):
    """Return the median of a list of numbers."""
    if not values:
        raise ValueError("median() of empty list")
    return sum(values) / len(values)
