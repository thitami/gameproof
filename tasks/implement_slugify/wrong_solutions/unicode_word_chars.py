import re


def slugify(text):
    """Convert text to a URL-friendly slug."""
    return re.sub(r'\W+', '-', text.lower()).strip('-')
