"""Tests for construct_editor.core.entries.

Covers helper utilities (int_to_str / str_to_int / str_to_bytes),
the EntryConstruct tree, and ObjViewSettings dataclasses.
The tests are UI-framework agnostic — no wx import is required.
"""

import pytest

from construct_editor.core.entries import (
    create_path_str,
    int_to_str,
    str_to_bytes,
    str_to_int,
)
from construct_editor.core.model import IntegerFormat

# ---------------------------------------------------------------------------
# int_to_str helpers
# ---------------------------------------------------------------------------


def test_int_to_str_decimal_format() -> None:
    assert int_to_str(IntegerFormat.Dec, 255) == "255"


def test_int_to_str_hex_format() -> None:
    assert int_to_str(IntegerFormat.Hex, 255) == "0xFF"


def test_int_to_str_zero_decimal() -> None:
    assert int_to_str(IntegerFormat.Dec, 0) == "0"


def test_int_to_str_negative_decimal() -> None:
    assert int_to_str(IntegerFormat.Dec, -1) == "-1"


def test_str_to_int_parse_decimal() -> None:
    assert str_to_int("42") == 42


def test_str_to_int_parse_hex_0x_prefix() -> None:
    assert str_to_int("0xFF") == 255


def test_str_to_int_parse_hex_lower() -> None:
    assert str_to_int("0xff") == 255


def test_str_to_int_invalid_string_raises() -> None:
    with pytest.raises(ValueError, match="invalid literal for int"):
        str_to_int("not_a_number")


def test_str_to_bytes_parse_hex_bytes() -> None:
    result = str_to_bytes("01 02 03")
    assert result == b"\x01\x02\x03"


def test_str_to_bytes_parse_empty_string() -> None:
    result = str_to_bytes("")
    assert result == b""


@pytest.mark.parametrize("value", ["zz", "0xf", "f"])
def test_str_to_bytes_invalid_hex_raises(value: str) -> None:
    with pytest.raises(ValueError):
        str_to_bytes(value)


def test_create_path_str_single_name() -> None:
    result = create_path_str(["root"])
    assert "root" in result


def test_create_path_str_nested_path() -> None:
    result = create_path_str(["root", "child", "leaf"])
    assert "root" in result
    assert "child" in result
    assert "leaf" in result
