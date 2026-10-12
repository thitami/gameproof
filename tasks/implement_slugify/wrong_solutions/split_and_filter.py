def slugify(text):
    """Convert text to a URL-friendly slug."""
    words = (''.join(c for c in word if c.isalnum()) for word in text.lower().split())
    return '-'.join(word for word in words if word)
