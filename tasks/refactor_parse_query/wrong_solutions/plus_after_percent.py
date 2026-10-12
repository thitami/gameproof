def parse_query(query_string):
    """Parse URL query string into a dictionary."""
    result = {}
    for pair in filter(None, query_string.split("&")):
        key, _, value = pair.partition("=")
        result[_decode(key)] = _decode(value)
    return result


def _decode(s):
    decoded, i = "", 0
    while i < len(s):
        if s[i] == "%" and i + 2 < len(s):
            try:
                decoded += chr(int(s[i+1:i+3], 16))
                i += 3
                continue
            except ValueError:
                pass
        decoded += s[i]
        i += 1
    return decoded.replace("+", " ")
