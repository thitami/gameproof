from urllib.parse import parse_qsl


def parse_query(query_string):
    """Parse URL query string into a dictionary."""
    return dict(parse_qsl(query_string, keep_blank_values=True))
