import ast
import inspect

from src import urlparse
from src.urlparse import parse_query


def test_basic():
    assert parse_query("a=1&b=2") == {"a": "1", "b": "2"}


def test_percent_encoding():
    assert parse_query("name=John%20Doe") == {"name": "John Doe"}


def test_percent_decoding_written_once():
    tree = ast.parse(inspect.getsource(urlparse))
    hex_parses = [n for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "int"]
    assert len(hex_parses) <= 1, "percent-decoding logic is duplicated"
