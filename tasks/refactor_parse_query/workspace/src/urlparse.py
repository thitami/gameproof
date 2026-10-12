def parse_query(query_string):
    """Parse URL query string into a dictionary.

    This code is messy and needs refactoring, but behavior must stay identical.
    """
    result = {}

    # Handle empty string
    if query_string == "":
        return result

    # Split by &
    pairs = []
    current = ""
    for char in query_string:
        if char == "&":
            if current != "":
                pairs.append(current)
            current = ""
        else:
            current = current + char
    if current != "":
        pairs.append(current)

    # Process each pair
    for pair in pairs:
        # Find the = sign
        equals_pos = -1
        for i in range(len(pair)):
            if pair[i] == "=":
                equals_pos = i
                break

        if equals_pos == -1:
            # No equals sign - key with no value becomes empty string
            key = pair
            value = ""
            # Decode key
            decoded_key = ""
            i = 0
            while i < len(key):
                if key[i] == "%":
                    if i + 2 < len(key):
                        hex_str = key[i+1:i+3]
                        try:
                            decoded_key = decoded_key + chr(int(hex_str, 16))
                            i = i + 3
                        except:
                            decoded_key = decoded_key + key[i]
                            i = i + 1
                    else:
                        decoded_key = decoded_key + key[i]
                        i = i + 1
                elif key[i] == "+":
                    decoded_key = decoded_key + " "
                    i = i + 1
                else:
                    decoded_key = decoded_key + key[i]
                    i = i + 1
            result[decoded_key] = value
        else:
            # Split by equals
            key = pair[:equals_pos]
            value = pair[equals_pos+1:]

            # Decode key
            decoded_key = ""
            i = 0
            while i < len(key):
                if key[i] == "%":
                    if i + 2 < len(key):
                        hex_str = key[i+1:i+3]
                        try:
                            decoded_key = decoded_key + chr(int(hex_str, 16))
                            i = i + 3
                        except:
                            decoded_key = decoded_key + key[i]
                            i = i + 1
                    else:
                        decoded_key = decoded_key + key[i]
                        i = i + 1
                elif key[i] == "+":
                    decoded_key = decoded_key + " "
                    i = i + 1
                else:
                    decoded_key = decoded_key + key[i]
                    i = i + 1

            # Decode value
            decoded_value = ""
            j = 0
            while j < len(value):
                if value[j] == "%":
                    if j + 2 < len(value):
                        hex_str = value[j+1:j+3]
                        try:
                            decoded_value = decoded_value + chr(int(hex_str, 16))
                            j = j + 3
                        except:
                            decoded_value = decoded_value + value[j]
                            j = j + 1
                    else:
                        decoded_value = decoded_value + value[j]
                        j = j + 1
                elif value[j] == "+":
                    decoded_value = decoded_value + " "
                    j = j + 1
                else:
                    decoded_value = decoded_value + value[j]
                    j = j + 1

            result[decoded_key] = decoded_value

    return result
