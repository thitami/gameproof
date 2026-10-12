import re


def slugify(text):
    """Convert text to a URL-friendly slug."""
    text = re.sub(r'[^a-z0-9 ]', '', text.lower())
    return text.replace(' ', '-')
