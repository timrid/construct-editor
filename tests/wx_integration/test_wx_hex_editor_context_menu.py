"""Tests for HexEditorGrid.build_context_menu and _on_cell_right_click.

`PopupMenu` (native, modal-ish and blocking until dismissed) is mocked out
via `mocker.patch.object(grid, "PopupMenu")` — actually showing a
real popup would hang the test until a human dismisses it.
"""

import wx

from construct_editor.wx_widgets.wx_hex_editor import WxHexEditor
from tests.wx_integration.wx_test_helpers import (
    editor_binary_data,
    editor_grid,
    editor_table,
    remove_selection,
    trigger_cell_right_click,
)


def test_build_context_menu_returns_cut_copy_paste_undo_redo_items(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02")

    items = editor_grid(editor).build_context_menu()

    ids = [item.wx_id for item in items if item is not None]
    assert ids == [
        wx.ID_CUT,
        wx.ID_COPY,
        wx.ID_PASTE,
        wx.ID_PASTE,
        wx.ID_UNDO,
        wx.ID_REDO,
    ]
    assert items[4] is None  # separator before Undo/Redo


def test_build_context_menu_disables_cut_and_paste_when_read_only(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02", read_only=True)

    items = {
        item.wx_id: item
        for item in editor_grid(editor).build_context_menu()
        if item is not None
    }

    assert items[wx.ID_CUT].enabled is False
    assert items[wx.ID_PASTE].enabled is False
    assert items[wx.ID_COPY].enabled is True  # copy is always allowed


def test_build_context_menu_undo_redo_reflect_command_processor_state(
    wx_harness,
) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03\x04")
    grid = editor_grid(editor)
    items_by_id = {
        item.wx_id: item
        for item in grid.build_context_menu()
        if item is not None
    }
    assert items_by_id[wx.ID_UNDO].enabled is False
    assert items_by_id[wx.ID_REDO].enabled is False

    grid.select_range(0, 0)
    remove_selection(grid)

    items_by_id = {
        item.wx_id: item
        for item in grid.build_context_menu()
        if item is not None
    }
    assert items_by_id[wx.ID_UNDO].enabled is True
    assert items_by_id[wx.ID_REDO].enabled is False

    editor_binary_data(editor).command_processor.Undo()

    items_by_id = {
        item.wx_id: item
        for item in grid.build_context_menu()
        if item is not None
    }
    assert items_by_id[wx.ID_UNDO].enabled is False
    assert items_by_id[wx.ID_REDO].enabled is True


def test_right_click_outside_selection_moves_cursor_to_clicked_cell(
    wx_harness, mocker
) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=bytes(20))
    grid = editor_grid(editor)
    mocker.patch.object(grid, "PopupMenu")
    grid.SetGridCursor(0, 0)
    grid.select_range(0, 15)  # selects all of row 0

    row, col = editor_table(editor).get_byte_rowcol(16)  # row 1, outside the selection
    event = mocker.Mock(
        GetRow=mocker.Mock(return_value=row),
        GetCol=mocker.Mock(return_value=col),
        GetPosition=mocker.Mock(return_value=wx.Point(0, 0)),
    )

    trigger_cell_right_click(grid, event)

    assert grid.GetGridCursorCoords() == (row, col)


def test_right_click_inside_selection_keeps_cursor_unchanged(
    wx_harness, mocker
) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=bytes(20))
    grid = editor_grid(editor)
    mocker.patch.object(grid, "PopupMenu")
    grid.SetGridCursor(0, 0)
    grid.select_range(0, 15)  # selects all of row 0

    row, col = editor_table(editor).get_byte_rowcol(5)  # inside the selection
    event = mocker.Mock(
        GetRow=mocker.Mock(return_value=row),
        GetCol=mocker.Mock(return_value=col),
        GetPosition=mocker.Mock(return_value=wx.Point(0, 0)),
    )

    trigger_cell_right_click(grid, event)

    assert grid.GetGridCursorCoords() == (0, 0)


def test_right_click_shows_popup_menu(wx_harness, mocker) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02")
    grid = editor_grid(editor)
    popup_menu = mocker.patch.object(grid, "PopupMenu")
    event = mocker.Mock(
        GetRow=mocker.Mock(return_value=0),
        GetCol=mocker.Mock(return_value=0),
        GetPosition=mocker.Mock(return_value=wx.Point(3, 4)),
    )

    trigger_cell_right_click(grid, event)

    popup_menu.assert_called_once()
    assert popup_menu.call_args.args[1] == wx.Point(3, 4)
