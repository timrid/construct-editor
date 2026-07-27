"""Tests for construct_editor.core.preprocessor.

Covers the metadata-instrumentation layer (IncludeGuiMetaData, GuiMetaData,
metadata-carrier subclasses, include_metadata / get_gui_metadata helpers).
"""


import construct as cs

from construct_editor.core.preprocessor import (
    get_gui_metadata,
    include_metadata,
)


def test_include_metadata_returns_construct() -> None:
    """include_metadata() must return a construct object."""
    wrapped = include_metadata(cs.Byte)
    assert wrapped is not None


def test_parse_attaches_gui_metadata() -> None:
    """Parsed values should carry GuiMetaData after instrumentation."""
    wrapped = include_metadata(cs.Byte)
    result = wrapped.parse(b"\x2a")
    meta = get_gui_metadata(result)
    assert meta is not None


def test_gui_metadata_contains_byte_range() -> None:
    """GuiMetaData must record the byte range of the parsed value."""
    wrapped = include_metadata(cs.Byte)
    result = wrapped.parse(b"\x01")
    meta = get_gui_metadata(result)
    assert meta is not None
    assert "byte_range" in meta


def test_struct_fields_have_independent_metadata() -> None:
    """Each field in a Struct should have its own metadata with the correct byte range."""
    struct = cs.Struct("a" / cs.Byte, "b" / cs.Byte)
    wrapped = include_metadata(struct)
    result = wrapped.parse(b"\x01\x02")
    meta_a = get_gui_metadata(result.a)
    meta_b = get_gui_metadata(result.b)
    assert meta_a is not None
    assert meta_b is not None
    # 'a' starts at byte 0, 'b' starts at byte 1
    assert meta_a["byte_range"][0] == 0
    assert meta_b["byte_range"][0] == 1


def test_include_metadata_nested_struct() -> None:
    """Metadata must be attached recursively for nested constructs."""
    inner = cs.Struct("x" / cs.Byte)
    outer = cs.Struct("inner" / inner, "y" / cs.Byte)
    wrapped = include_metadata(outer)
    result = wrapped.parse(b"\x01\x02")
    meta_x = get_gui_metadata(result.inner.x)
    assert meta_x is not None


def test_get_gui_metadata_returns_none_for_plain_int() -> None:
    """get_gui_metadata() returns None for values without attached metadata."""
    assert get_gui_metadata(42) is None


def test_get_gui_metadata_returns_none_for_plain_bytes() -> None:
    assert get_gui_metadata(b"\x00") is None


def test_get_gui_metadata_returns_none_for_none() -> None:
    assert get_gui_metadata(None) is None
