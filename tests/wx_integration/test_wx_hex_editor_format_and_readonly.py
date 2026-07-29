"""Tests for WxHexEditor's `format` setter, `scroll_to_idx`, `colorise`, the
`binary` setter, and `read_only` mode.

`colorise` already has a dedicated case in test_wx_hex_editor.py
(`test_colorise_highlights_range_via_table_attr`) — not duplicated here.
"""

import dataclasses

from construct_editor.wx_widgets.wx_hex_editor import HexEditorFormat, WxHexEditor
from tests.wx_integration.wx_test_helpers import (
    editor_binary_data,
    editor_grid,
    editor_table,
    insert_byte_at_selection,
    remove_selection,
)


def test_format_setter_updates_grid_column_count(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=bytes(32))
    grid = editor_grid(editor)
    assert grid.GetNumberCols() == 16  # default width

    editor.format = dataclasses.replace(editor.format, width=8)

    assert grid.GetNumberCols() == 8
    # 32 bytes / 8 per row = 4 rows exactly, plus one trailing row (see
    # HexEditorTable.refresh_rows_cols: an extra row is added whenever the
    # binary exactly fills the last row).
    assert grid.GetNumberRows() == 5


def test_format_getter_returns_current_format(wx_harness) -> None:
    fmt = HexEditorFormat(width=4)
    editor = WxHexEditor(wx_harness.frame, binary=bytes(8), format=fmt)

    assert editor.format is fmt


def test_scroll_to_idx_makes_target_cell_visible(wx_harness, mocker) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=bytes(64))
    make_cell_visible = mocker.patch.object(editor_grid(editor), "MakeCellVisible")

    editor.scroll_to_idx(20)

    row, col = editor_table(editor).get_byte_rowcol(20)
    make_cell_visible.assert_called_once_with(row, col)


def test_binary_setter_replaces_data_and_clears_selection_and_undo_history(
    wx_harness,
) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02")
    grid = editor_grid(editor)
    grid.select_range(0, 1)
    remove_selection(grid)  # put a command on the undo stack
    assert editor_binary_data(editor).command_processor.CanUndo() is True

    editor.binary = b"\xaa\xbb\xcc"

    assert editor.binary == b"\xaa\xbb\xcc"
    assert editor_binary_data(editor).command_processor.CanUndo() is False
    assert editor_table(editor).selections == [(0, 0)]


def test_read_only_grid_disables_editing(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02", read_only=True)

    grid = editor_grid(editor)
    assert grid.read_only is True
    assert grid.IsEditable() is False


def test_read_only_grid_rejects_mutating_operations(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03", read_only=True)
    grid = editor_grid(editor)
    grid.select_range(0, 1)

    assert remove_selection(grid) is False
    assert insert_byte_at_selection(grid) is False
    assert editor.binary == b"\x01\x02\x03"


def test_not_read_only_grid_enables_editing(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02", read_only=False)

    grid = editor_grid(editor)
    assert grid.read_only is False
    assert grid.IsEditable() is True
