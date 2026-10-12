from src.urlparse import parse_query


def test_empty_string():
    assert parse_query("") == {}


def test_empty_pairs_skipped():
    assert parse_query("&x=1&&y=2&") == {"x": "1", "y": "2"}


def test_key_without_equals_gets_empty_value():
    assert parse_query("flag&z=3") == {"flag": "", "z": "3"}


def test_empty_key():
    assert parse_query("=v") == {"": "v"}


def test_only_first_equals_splits():
    assert parse_query("eq=b=c") == {"eq": "b=c"}


def test_last_duplicate_wins():
    assert parse_query("k=first&k=second") == {"k": "second"}


def test_plus_is_space_in_keys_and_values():
    assert parse_query("full+name=Ada+Lovelace") == {"full name": "Ada Lovelace"}


def test_encoded_plus_stays_plus():
    assert parse_query("sum=1%2B1") == {"sum": "1+1"}


def test_decoding_happens_after_splitting():
    assert parse_query("a%3Db=x%26y") == {"a=b": "x&y"}


def test_lowercase_hex():
    assert parse_query("p=%2f") == {"p": "/"}


def test_invalid_escape_kept_literally():
    assert parse_query("bad=%zz") == {"bad": "%zz"}


def test_truncated_escape_kept_literally():
    # Needs two characters after '%', so a trailing "%4" is not decoded.
    assert parse_query("t=%4") == {"t": "%4"}


def test_escape_at_very_end_is_decoded():
    assert parse_query("e=%21") == {"e": "!"}


def test_bytes_decoded_one_char_each_not_utf8():
    # %C3%A9 is "é" in UTF-8, but this parser maps each byte to its own char.
    assert parse_query("cafe=%C3%A9") == {"cafe": "Ã©"}


def test_escape_with_sign_goes_through_int():
    # int("+1", 16) == 1, int("-1", 16) == -1 (chr fails, so kept literally).
    assert parse_query("s=%+1&n=%-1") == {"s": "\x01", "n": "%-1"}
