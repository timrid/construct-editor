"""Tests for construct_editor.wx_widgets.wx_hex_editor.WxHexEditor.

Widget-level tests drive the grid via real, simulated OS input
(wx.UIActionSimulator) against a visible, focused frame, so the actual
event-handling code path (cell selection, cell editing, key bindings) is
exercised rather than just the public API.
"""

import wx

from construct_editor.wx_widgets.wx_hex_editor import WxHexEditor
from tests.wx_integration.wx_test_helpers import (
    editor_grid,
    editor_table,
    grid_cell_screen_point,
)


def test_instantiates_without_exceptions(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03")

    assert editor.binary == b"\x01\x02\x03"


def test_setting_binary_replaces_displayed_data(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02")

    editor.binary = b"\xaa\xbb\xcc"

    assert editor.binary == b"\xaa\xbb\xcc"
    table = editor_table(editor)
    assert table.GetValue(0, 0) == "aa"
    assert table.GetValue(0, 1) == "bb"
    assert table.GetValue(0, 2) == "cc"


def test_refresh_does_not_raise(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02")

    editor.refresh()


def test_setting_invalid_hex_via_table_does_not_change_binary(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02")

    editor_table(editor).SetValue(0, 0, "zz")

    assert editor.binary == b"\x01\x02"


def test_colorise_highlights_range_via_table_attr(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03")

    editor.colorise(1, 3)

    table = editor_table(editor)
    assert table.GetAttr(0, 1, 0).GetBackgroundColour() == wx.Colour(
        200, 200, 200
    )
    assert table.GetAttr(0, 0, 0).GetBackgroundColour() == wx.WHITE


def test_editing_cell_via_simulated_keyboard_fires_on_binary_changed(
    wx_harness, mocker
) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x00\x00")
    wx_harness.frame.Layout()

    callback = mocker.Mock()
    editor.on_binary_changed.append(callback)

    grid = editor_grid(editor)
    point = grid_cell_screen_point(grid, 0, 0)

    # click the first cell, type "FF" into it, then commit with Enter
    wx_harness.move_mouse_to(point)
    wx_harness.click()
    wx_harness.type_text("FF")
    wx_harness.key_press(wx.WXK_RETURN)

    callback.assert_called()
    assert editor.binary[0] == 0xFF

