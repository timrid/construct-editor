"""Tests for construct_editor.wx_widgets.wx_hex_editor.HexEditorTable.

HexEditorTable is exercised in isolation here — it only needs an object
exposing `.format` (the real WxHexEditor also has one), not a full widget
tree — so these tests don't need `wx_harness`/a visible frame, just `wx_app_and_ui_sim`
for wx.GridCellAttr/wx.Font construction.
"""

import wx

from construct_editor.wx_widgets.wx_hex_editor import (
    HexEditorBinaryData,
    HexEditorFormat,
    HexEditorTable,
)


class _FakeEditor:
    """Minimal stand-in for WxHexEditor: HexEditorTable only reads `.format`."""

    def __init__(self, format: HexEditorFormat | None = None) -> None:
        self.format = format or HexEditorFormat()


def _make_table(binary: bytes, format: HexEditorFormat | None = None) -> HexEditorTable:
    binary_data = HexEditorBinaryData(binary)
    table = HexEditorTable(_FakeEditor(format), binary_data)
    table.refresh_rows_cols()
    return table


def test_get_value_formats_byte_as_two_digit_lowercase_hex(wx_app_and_ui_sim) -> None:
    table = _make_table(b"\xab")

    assert table.GetValue(0, 0) == "ab"


def test_get_value_beyond_binary_length_is_empty_string(wx_app_and_ui_sim) -> None:
    table = _make_table(b"\x01")

    assert table.GetValue(0, 1) == ""


def test_set_value_with_valid_hex_updates_binary(wx_app_and_ui_sim) -> None:
    binary_data = HexEditorBinaryData(b"\x00")
    table = HexEditorTable(_FakeEditor(), binary_data)
    table.refresh_rows_cols()

    table.SetValue(0, 0, "ff")

    assert binary_data.get_bytes() == b"\xff"


def test_set_value_with_invalid_hex_is_silently_ignored(wx_app_and_ui_sim) -> None:
    binary_data = HexEditorBinaryData(b"\x00")
    table = HexEditorTable(_FakeEditor(), binary_data)
    table.refresh_rows_cols()

    table.SetValue(0, 0, "zz")

    assert binary_data.get_bytes() == b"\x00"


def test_set_value_empty_string_beyond_binary_length_is_noop(wx_app_and_ui_sim) -> None:
    binary_data = HexEditorBinaryData(b"\x00")
    table = HexEditorTable(_FakeEditor(), binary_data)
    table.refresh_rows_cols()

    table.SetValue(0, 1, "")

    assert binary_data.get_bytes() == b"\x00"


def test_is_empty_cell_reflects_binary_length(wx_app_and_ui_sim) -> None:
    table = _make_table(b"\x01\x02")

    assert table.IsEmptyCell(0, 0) is False
    assert table.IsEmptyCell(0, 1) is False
    assert table.IsEmptyCell(0, 2) is True


def test_get_attr_uses_selected_background_within_selections(wx_app_and_ui_sim) -> None:
    table = _make_table(b"\x01\x02\x03")
    table.selections = [(1, 3)]

    attr = table.GetAttr(0, 1, 0)

    assert attr.GetBackgroundColour() == wx.Colour(200, 200, 200)


def test_get_attr_uses_default_background_outside_selections(wx_app_and_ui_sim) -> None:
    table = _make_table(b"\x01\x02\x03")
    table.selections = [(1, 3)]

    attr = table.GetAttr(0, 0, 0)

    assert attr.GetBackgroundColour() == wx.WHITE


def test_get_next_cursor_rowcol_advances_by_one_byte(wx_app_and_ui_sim) -> None:
    table = _make_table(b"\x01\x02\x03", HexEditorFormat(width=2))

    assert table.get_next_cursor_rowcol(0, 0) == (0, 1)


def test_get_next_cursor_rowcol_stays_put_at_end_of_binary(wx_app_and_ui_sim) -> None:
    table = _make_table(b"\x01\x02", HexEditorFormat(width=2))

    # idx 2 == len(binary): one-past-the-end is allowed, but not further
    assert table.get_next_cursor_rowcol(0, 1) == (1, 0)
    assert table.get_next_cursor_rowcol(1, 0) == (1, 0)


def test_get_prev_cursor_rowcol_retreats_by_one_byte(wx_app_and_ui_sim) -> None:
    table = _make_table(b"\x01\x02\x03", HexEditorFormat(width=2))

    assert table.get_prev_cursor_rowcol(1, 0) == (0, 1)


def test_get_prev_cursor_rowcol_stays_put_at_start(wx_app_and_ui_sim) -> None:
    table = _make_table(b"\x01\x02", HexEditorFormat(width=2))

    assert table.get_prev_cursor_rowcol(0, 0) == (0, 0)


def test_refresh_rows_cols_adds_trailing_row_when_binary_exactly_fills_last_row(
    wx_app_and_ui_sim,
) -> None:
    table = _make_table(b"\x01\x02", HexEditorFormat(width=2))

    assert table.GetNumberRows() == 2  # one full row + trailing empty row
    assert table.GetNumberCols() == 2
