"""Tests for HexEditorGrid's clipboard/mutation-on-selection methods:
`_cut_selection`, `_copy_selection`, `_paste`, `_remove_selection`,
`_insert_byte_at_selection`.

These use a real WxHexEditor via `wx_harness` (same rationale as
test_wx_hex_editor_grid.py). `wx_clipboard.get_text`/`set_text` are mocked
(via `mocker.patch`) instead of touching the real OS clipboard, so these
tests don't clobber whatever the developer/CI actually has copied.
"""

from construct_editor.wx_widgets import wx_clipboard
from construct_editor.wx_widgets.wx_hex_editor import WxHexEditor
from tests.wx_integration.wx_test_helpers import (
    copy_selection,
    cut_selection,
    editor_grid,
    grid_selection,
    insert_byte_at_selection,
    paste_at_selection,
    remove_selection,
)


def test_copy_selection_writes_hex_string_to_clipboard(wx_harness, mocker) -> None:
    set_text = mocker.patch.object(wx_clipboard, "set_text", return_value=True)
    editor = WxHexEditor(wx_harness.frame, binary=b"\xab\xcd\xef")
    grid = editor_grid(editor)
    grid.select_range(1, 2)

    result = copy_selection(grid)

    assert result is True
    set_text.assert_called_once_with("cd ef")


def test_copy_selection_returns_false_when_clipboard_unavailable(
    wx_harness, mocker
) -> None:
    mocker.patch.object(wx_clipboard, "set_text", return_value=False)
    mocker.patch("wx.MessageBox")
    editor = WxHexEditor(wx_harness.frame, binary=b"\xab\xcd\xef")
    grid = editor_grid(editor)
    grid.select_range(0, 0)

    assert copy_selection(grid) is False


def test_copy_selection_returns_false_when_nothing_selected(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\xab\xcd\xef")

    assert copy_selection(editor_grid(editor)) is False


def test_remove_selection_deletes_selected_range(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03\x04")
    grid = editor_grid(editor)
    grid.select_range(1, 2)

    result = remove_selection(grid)

    assert result is True
    assert editor.binary == b"\x01\x04"
    # _remove_selection() moves the grid cursor afterwards, which fires
    # EVT_GRID_SELECT_CELL and collapses the selection to that single cell
    # (rather than leaving it at (None, None)).
    assert grid_selection(grid) == (0, None)


def test_remove_selection_returns_false_when_read_only(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03\x04", read_only=True)
    grid = editor_grid(editor)
    grid.select_range(1, 2)

    assert remove_selection(grid) is False
    assert editor.binary == b"\x01\x02\x03\x04"


def test_insert_byte_at_selection_inserts_zero_byte(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02")
    grid = editor_grid(editor)
    grid.select_range(1, 1)

    result = insert_byte_at_selection(grid)

    assert result is True
    assert editor.binary == b"\x01\x00\x02"


def test_cut_selection_copies_then_removes(wx_harness, mocker) -> None:
    set_text = mocker.patch.object(wx_clipboard, "set_text", return_value=True)
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03")
    grid = editor_grid(editor)
    grid.select_range(1, 2)

    result = cut_selection(grid)

    assert result is True
    set_text.assert_called_once_with("02 03")
    assert editor.binary == b"\x01"


def test_cut_selection_returns_false_when_read_only(wx_harness, mocker) -> None:
    set_text = mocker.patch.object(wx_clipboard, "set_text", return_value=True)
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03", read_only=True)
    grid = editor_grid(editor)
    grid.select_range(1, 2)

    assert cut_selection(grid) is False
    set_text.assert_not_called()
    assert editor.binary == b"\x01\x02\x03"


def test_paste_overwrite_replaces_bytes_at_selection(wx_harness, mocker) -> None:
    mocker.patch.object(wx_clipboard, "get_text", return_value="aa bb")
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02\x03\x04")
    grid = editor_grid(editor)
    grid.select_range(1, 1)

    result = paste_at_selection(grid, overwrite=True)

    assert result is True
    assert editor.binary == b"\x01\xaa\xbb\x04"


def test_paste_insert_grows_binary_at_selection(wx_harness, mocker) -> None:
    mocker.patch.object(wx_clipboard, "get_text", return_value="aa bb")
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02")
    grid = editor_grid(editor)
    grid.select_range(1, 1)

    result = paste_at_selection(grid, insert=True)

    assert result is True
    assert editor.binary == b"\x01\xaa\xbb\x02"


def test_paste_returns_false_when_nothing_selected(wx_harness, mocker) -> None:
    get_text = mocker.patch.object(wx_clipboard, "get_text", return_value="aa bb")
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02")

    assert paste_at_selection(editor_grid(editor), overwrite=True) is False
    get_text.assert_not_called()


def test_paste_returns_false_when_both_overwrite_and_insert_requested(
    wx_harness, mocker
) -> None:
    mocker.patch("wx.MessageBox")
    get_text = mocker.patch.object(wx_clipboard, "get_text", return_value="aa bb")
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02")
    grid = editor_grid(editor)
    grid.select_range(0, 0)

    assert paste_at_selection(grid, overwrite=True, insert=True) is False
    get_text.assert_not_called()


def test_paste_returns_false_when_clipboard_text_is_unparseable(
    wx_harness, mocker
) -> None:
    # A lone incomplete "\x" escape fails all three string_to_byts fallbacks
    # (bytes.fromhex, the hex-digit regex, and the unicode-escape round trip).
    mocker.patch.object(wx_clipboard, "get_text", return_value="\\x")
    message_box = mocker.patch("wx.MessageBox")
    editor = WxHexEditor(wx_harness.frame, binary=b"\x01\x02")
    grid = editor_grid(editor)
    grid.select_range(0, 0)

    assert paste_at_selection(grid, overwrite=True) is False
    assert editor.binary == b"\x01\x02"
    message_box.assert_called_once()
