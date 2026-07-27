"""Tests for HexEditorGrid._on_key_down's key dispatch table.

Unlike test_wx_hex_editor_grid.py/test_wx_hex_editor_clipboard.py (which
mostly call the private handler methods directly), these tests drive the
actual keyboard shortcuts through `wx.UIActionSimulator`, so they also prove
`_on_key_down`'s key/modifier matching itself (not just the methods it
delegates to). A cell is clicked first to give the grid real OS focus, since
UIActionSimulator posts real OS-level input.

Preconditions for each shortcut (e.g. an existing selection, or an undoable
command already on the command_processor stack) are set up via direct calls
to grid methods rather than simulated input, since that setup isn't what's
under test here.
"""

import wx

from construct_editor.wx_widgets import wx_clipboard
from construct_editor.wx_widgets.wx_hex_editor import WxHexEditor
from tests.wx_integration.wx_test_helpers import (
    editor_binary_data,
    editor_grid,
    grid_cell_screen_point,
    grid_selection,
    remove_selection,
)


def _focus_grid(wx_harness, grid) -> None:
    wx_harness.frame.Layout()
    # Column 0 is a narrow gutter-ish column that doesn't reliably receive
    # real OS clicks; column 1 is the pattern already proven to work in
    # test_wx_hex_editor_grid.py's shift+arrow test.
    point = grid_cell_screen_point(grid, 0, 1)
    wx_harness.move_mouse_to(point)
    wx_harness.click()


def test_delete_key_removes_selection(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03\x04")
    grid = editor_grid(editor)
    _focus_grid(wx_harness, grid)
    grid.select_range(1, 2)

    wx_harness.key_press(wx.WXK_DELETE)

    assert editor.binary == b"\x01\x04"


def test_insert_key_inserts_byte_at_selection(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02")
    grid = editor_grid(editor)
    _focus_grid(wx_harness, grid)
    grid.select_range(1, 1)

    wx_harness.key_press(wx.WXK_INSERT)

    assert editor.binary == b"\x01\x00\x02"


def test_ctrl_z_undoes_last_command(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03\x04")
    grid = editor_grid(editor)
    _focus_grid(wx_harness, grid)
    grid.select_range(1, 2)
    remove_selection(grid)
    assert editor.binary == b"\x01\x04"

    wx_harness.key_press(ord("Z"), wx.MOD_CONTROL)

    assert editor.binary == b"\x01\x02\x03\x04"


def test_ctrl_y_redoes_last_undone_command(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03\x04")
    grid = editor_grid(editor)
    _focus_grid(wx_harness, grid)
    grid.select_range(1, 2)
    remove_selection(grid)
    editor_binary_data(editor).command_processor.Undo()
    assert editor.binary == b"\x01\x02\x03\x04"

    wx_harness.key_press(ord("Y"), wx.MOD_CONTROL)

    assert editor.binary == b"\x01\x04"


def test_ctrl_x_cuts_selection(wx_harness, mocker) -> None:
    set_text = mocker.patch.object(wx_clipboard, "set_text", return_value=True)
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03")
    grid = editor_grid(editor)
    _focus_grid(wx_harness, grid)
    grid.select_range(1, 2)

    wx_harness.key_press(ord("X"), wx.MOD_CONTROL)

    set_text.assert_called_once_with("02 03")
    assert editor.binary == b"\x01"


def test_ctrl_c_copies_selection(wx_harness, mocker) -> None:
    set_text = mocker.patch.object(wx_clipboard, "set_text", return_value=True)
    editor = WxHexEditor(wx_harness.frame, binary=b"\xab\xcd\xef")
    grid = editor_grid(editor)
    _focus_grid(wx_harness, grid)
    grid.select_range(1, 2)

    wx_harness.key_press(ord("C"), wx.MOD_CONTROL)

    set_text.assert_called_once_with("cd ef")
    assert editor.binary == b"\xab\xcd\xef"


def test_ctrl_v_pastes_overwrite(wx_harness, mocker) -> None:
    mocker.patch.object(wx_clipboard, "get_text", return_value="aa bb")
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03\x04")
    grid = editor_grid(editor)
    _focus_grid(wx_harness, grid)
    grid.select_range(1, 1)

    wx_harness.key_press(ord("V"), wx.MOD_CONTROL)

    assert editor.binary == b"\x01\xaa\xbb\x04"


def test_ctrl_shift_v_pastes_insert(wx_harness, mocker) -> None:
    mocker.patch.object(wx_clipboard, "get_text", return_value="aa bb")
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02")
    grid = editor_grid(editor)
    _focus_grid(wx_harness, grid)
    grid.select_range(1, 1)

    wx_harness.key_press(ord("V"), wx.MOD_CONTROL | wx.MOD_SHIFT)

    assert editor.binary == b"\x01\xaa\xbb\x02"


def test_ctrl_a_selects_entire_binary(wx_harness, mocker) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03\x04")
    grid = editor_grid(editor)
    _focus_grid(wx_harness, grid)
    callback = mocker.Mock()
    editor.on_selection_changed.append(callback)

    wx_harness.key_press(ord("A"), wx.MOD_CONTROL)

    assert grid_selection(grid) == (0, 3)
