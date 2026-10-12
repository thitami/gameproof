from src.text import slugify


def test_extra_spaces():
    assert slugify("Hello   World") == "hello-world"


def test_accents():
    assert slugify("Crème Brûlée") == "creme-brulee"


def test_existing_hyphens():
    assert slugify("Hello-World-Test") == "hello-world-test"


def test_numbers():
    assert slugify("Test 123 Example") == "test-123-example"


def test_symbols_only():
    assert slugify("!!!") == ""


def test_underscores():
    assert slugify("snake_case_name") == "snake-case-name"


def test_leading_and_trailing_punctuation():
    assert slugify("  -- Release Notes --  ") == "release-notes"
