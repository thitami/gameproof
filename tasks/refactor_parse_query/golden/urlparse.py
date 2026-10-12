def parse_query(query_string):
    """Parse URL query string into a dictionary.

    Clean implementation that preserves exact behavior.
    """
    if not query_string:
        return {}

    result = {}
    pairs = [p for p in query_string.split("&") if p]

    for pair in pairs:
        if "=" in pair:
            key, value = pair.split("=", 1)
        else:
            key, value = pair, ""

        result[_decode(key)] = _decode(value)

    return result


def _decode(s):
    """Decode URL-encoded string, handling % encoding and + as space."""
    decoded = ""
    i = 0
    while i < len(s):
        if s[i] == "%":
            if i + 2 < len(s):
                try:
                    decoded += chr(int(s[i+1:i+3], 16))
                    i += 3
                except ValueError:
                    decoded += s[i]
                    i += 1
            else:
                decoded += s[i]
                i += 1
        elif s[i] == "+":
            decoded += " "
            i += 1
        else:
            decoded += s[i]
            i += 1
    return decoded
