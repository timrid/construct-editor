"""Tests for construct_editor.wx_widgets.wx_hex_editor.HexEditorGrid selection logic.

HexEditorGrid needs a real wx parent window (its constructor both parents
the Grid.Grid and stores the parent as `self._editor`), so these tests build
a real WxHexEditor via `wx_harness` and call grid methods directly
(`grid.select_range(...)`, `trigger_range_selecting_keyboard(...)`).
No `wx.UIActionSimulator` is used here — that's reserved for tests that must
prove real keyboard/mouse event wiring (see test_wx_hex_editor.py), and for
`_on_range_selecting_keyboard` specifically: driving it via a raw
`SetGridCursor()` call (instead of real Shift+Arrow input) fires
`EVT_GRID_SELECT_CELL` as a side effect, which collapses the very range
selection under test — so that one case uses `wx.UIActionSimulator` instead.
"""

import wx

from construct_editor.wx_widgets.wx_hex_editor import WxHexEditor
from tests.wx_integration.wx_test_helpers import (
    editor_grid,
    grid_cell_screen_point,
    grid_selection,
    trigger_range_selecting_keyboard,
    trigger_select_cell,
)


def test_select_range_within_single_row_fires_selection_changed(
    wx_harness, mocker
) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03\x04")
    callback = mocker.Mock()
    editor.on_selection_changed.append(callback)

    grid = editor_grid(editor)
    grid.select_range(1, 2)

    callback.assert_called_once_with(1, 2)
    assert grid_selection(grid) == (1, 2)


def test_select_range_swaps_indices_when_reversed(wx_harness, mocker) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03\x04")
    callback = mocker.Mock()
    editor.on_selection_changed.append(callback)

    grid = editor_grid(editor)
    grid.select_range(2, 1)

    callback.assert_called_once_with(1, 2)
    assert grid_selection(grid) == (1, 2)


def test_select_range_clamps_indices_to_binary_length(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02")

    grid = editor_grid(editor)
    grid.select_range(0, 100)

    assert grid_selection(grid) == (0, 1)


def test_select_range_ignored_when_either_index_negative(wx_harness, mocker) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02")
    callback = mocker.Mock()
    editor.on_selection_changed.append(callback)

    grid = editor_grid(editor)
    grid.select_range(-1, 1)

    callback.assert_not_called()
    assert grid_selection(grid) == (None, None)


def test_select_range_across_multiple_rows_spans_first_middle_last(wx_harness) -> None:
    editor = WxHexEditor(
        wx_harness.frame, binary=bytes(48), format=None
    )
    editor.format = editor.format.__class__(width=16)

    grid = editor_grid(editor)
    grid.select_range(0, 33)  # rows 0..2 at width 16

    assert grid_selection(grid) == (0, 33)
    assert grid.IsInSelection(1, 5)  # a cell in the "body" row


def test_on_range_selecting_keyboard_is_noop_when_nothing_selected(
    wx_harness, mocker
) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03\x04")
    callback = mocker.Mock()
    editor.on_selection_changed.append(callback)

    grid = editor_grid(editor)
    trigger_range_selecting_keyboard(grid, col_diff=1)

    callback.assert_not_called()
    assert grid_selection(grid) == (None, None)


def test_on_range_selecting_keyboard_extends_selection_via_simulated_shift_arrow(
    wx_harness, mocker
) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03\x04")
    wx_harness.frame.Layout()
    callback = mocker.Mock()
    editor.on_selection_changed.append(callback)

    grid = editor_grid(editor)
    point = grid_cell_screen_point(grid, 0, 1)  # click byte idx 1
    wx_harness.move_mouse_to(point)
    wx_harness.click()
    wx_harness.key_press(wx.WXK_RIGHT, wx.MOD_SHIFT)  # extend to byte idx 2

    callback.assert_called_with(1, 2)
    assert grid_selection(grid) == (1, 2)


def test_on_select_cell_replaces_range_selection_with_single_cell(
    wx_harness, mocker
) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03\x04")
    grid = editor_grid(editor)
    grid.select_range(0, 2)
    callback = mocker.Mock()
    editor.on_selection_changed.append(callback)

    event = mocker.Mock(GetRow=mocker.Mock(return_value=0), GetCol=mocker.Mock(return_value=3))
    trigger_select_cell(grid, event)

    callback.assert_called_once_with(3, None)
    assert grid_selection(grid) == (3, None)
