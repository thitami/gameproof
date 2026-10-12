from urllib.parse import unquote_plus


def parse_query(query_string):
    """Parse URL query string into a dictionary."""
    result = {}
    for pair in filter(None, query_string.split("&")):
        key, _, value = pair.partition("=")
        result[unquote_plus(key)] = unquote_plus(value)
    return result
