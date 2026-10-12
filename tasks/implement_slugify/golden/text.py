import re
import unicodedata


def slugify(text):
    """Convert text to a URL-friendly slug."""
    # Normalize unicode characters (decompose accents)
    text = unicodedata.normalize('NFD', text)
    # Remove non-ASCII characters (accents)
    text = text.encode('ascii', 'ignore').decode('ascii')
    # Convert to lowercase
    text = text.lower()
    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    return text
