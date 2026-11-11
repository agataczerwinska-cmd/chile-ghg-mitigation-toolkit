"""Numbers pasted with thousands separators must be read correctly."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modes.common import parse_number  # noqa: E402


@pytest.mark.parametrize(
    "text, language, expected",
    [
        ("1.200.000", "es", 1200000),
        ("1.200.000,5", "es", 1200000.5),
        ("1 200 000,50", "es", 1200000.5),
        ("1.200", "es", 1200),
        ("1,3", "es", 1.3),
        ("1.3", "es", 1.3),
        ("0.250", "es", 0.25),
        ("0,19", "es", 0.19),
        ("15000", "es", 15000),
        ("15000.00", "es", 15000),
        ("1,200,000", "es", 1200000),
        ("1,200,000.50", "es", 1200000.5),
        ("1,200,000", "en", 1200000),
        ("1,200", "en", 1200),
        ("1.200", "en", 1.2),
        ("1.2", "en", 1.2),
        ("1,5", "en", 1.5),
        ("1.200.000", "en", 1200000),
        ("4e8", "es", 400000000),
        ("-5", "es", -5),
    ],
)
def test_parse_number(text, language, expected):
    assert parse_number(text, language) == pytest.approx(expected)


@pytest.mark.parametrize("text", ["", "abc", "1.2.3", "12,34,56"])
def test_invalid_numbers(text):
    with pytest.raises(ValueError):
        parse_number(text, "es")
