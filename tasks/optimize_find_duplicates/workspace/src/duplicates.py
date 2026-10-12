def find_duplicates(items):
    """Return the items that appear more than once in `items`.

    Each duplicate is reported once, in order of its first appearance, and the
    first occurrence is the one returned. Items are assumed to be hashable.

    This implementation is correct but O(n^2). Make it O(n) while keeping the
    output identical.
    """
    duplicates = []

    for item in items:
        # Count how many times this item appears
        count = 0
        for other in items:
            if item == other:
                count = count + 1

        # If it appears more than once and we haven't added it yet
        if count > 1:
            already_added = False
            for dup in duplicates:
                if dup == item:
                    already_added = True
                    break
            if not already_added:
                duplicates.append(item)

    return duplicates
