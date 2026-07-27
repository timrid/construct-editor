"""Tests for construct_editor.wx_widgets.wx_hex_editor.HexEditorBinaryData.

HexEditorBinaryData is the observable bytearray driven directly through its
public API (no UI simulation) — it's a plain data/command-pattern class, not
a widget. It still needs a running wx.App because it uses
wx.Command/wx.CommandProcessor.
"""

from construct_editor.wx_widgets.wx_hex_editor import HexEditorBinaryData


def test_overwrite_all_replaces_entire_buffer(wx_app_and_ui_sim) -> None:
    data = HexEditorBinaryData(b"\x01\x02\x03")
    data.overwrite_all(b"\xaa\xbb")
    assert data.get_bytes() == b"\xaa\xbb"


def test_overwrite_range_changes_only_specified_slice(wx_app_and_ui_sim) -> None:
    data = HexEditorBinaryData(b"\x00\x00\x00\x00")
    data.overwrite_range(1, b"\xff\xff")
    assert data.get_bytes() == b"\x00\xff\xff\x00"


def test_overwrite_range_with_unchanged_bytes_is_a_noop(wx_app_and_ui_sim, mocker) -> None:
    data = HexEditorBinaryData(b"\x00\x00\x00\x00")
    callback = mocker.Mock()
    data.on_binary_changed.append(callback)

    data.overwrite_range(1, b"\x00\x00")

    assert data.get_bytes() == b"\x00\x00\x00\x00"
    callback.assert_not_called()


def test_insert_range_grows_buffer(wx_app_and_ui_sim) -> None:
    data = HexEditorBinaryData(b"\x01\x02")
    data.insert_range(1, b"\xaa\xbb")
    assert data.get_bytes() == b"\x01\xaa\xbb\x02"


def test_remove_range_shrinks_buffer(wx_app_and_ui_sim) -> None:
    data = HexEditorBinaryData(b"\x01\x02\x03\x04")
    data.remove_range(1, 2)
    assert data.get_bytes() == b"\x01\x04"


def test_remove_range_uses_descriptive_undo_command_name(wx_app_and_ui_sim) -> None:
    data = HexEditorBinaryData(b"\x01\x02\x03\x04")
    data.remove_range(1, 2)

    command_name = data.command_processor.GetCurrentCommand().GetName()
    assert command_name == "Remove Range (Index: 1, Length: 2)"


def test_on_binary_changed_fires_after_mutation(wx_app_and_ui_sim, mocker) -> None:
    data = HexEditorBinaryData(b"\x00")
    callback = mocker.Mock()
    data.on_binary_changed.append(callback)

    data.overwrite_all(b"\x01")

    callback.assert_called_once_with(data)


def test_undo_reverts_last_mutation(wx_app_and_ui_sim) -> None:
    data = HexEditorBinaryData(b"\x01\x02\x03")
    data.overwrite_range(0, b"\xff")
    assert data.get_bytes() == b"\xff\x02\x03"

    data.command_processor.Undo()

    assert data.get_bytes() == b"\x01\x02\x03"


def test_redo_reapplies_undone_mutation(wx_app_and_ui_sim) -> None:
    data = HexEditorBinaryData(b"\x01\x02\x03")
    data.overwrite_range(0, b"\xff")
    data.command_processor.Undo()

    data.command_processor.Redo()

    assert data.get_bytes() == b"\xff\x02\x03"
