"""Tests for HexTextCtrl (the in-cell hex editing control) and
HexCellEditor's IsAcceptedKey/BeginEdit/EndEdit wiring.

`mode="char"` is intentionally NOT covered here: `HexCellEditor.BeginEdit`
always hardcodes `mode = "hex"`, so the "char" branch in
`HexTextCtrl.set_mode`/`insert_first_key` is unreachable through any current
production code path. Treating it as dead code per explicit instruction
rather than writing tests for an unreachable branch.

`HexTextCtrl` is built directly (not through a full `HexEditorGrid`/
`HexCellEditor`), with a `mocker.Mock()` standing in for `parentgrid` — it
only needs `_advance_cursor`/`_abort_edit` to exist as callables. Key events
are constructed with `mocker.Mock()` rather than real KeyEvents/
UIActionSimulator, since `on_key_down`'s branching is pure logic once given
a keycode/modifiers.
"""

import wx
from pytest_mock import MockerFixture

from construct_editor.wx_widgets.wx_hex_editor import HexCellEditor, HexTextCtrl


def _key_event(keycode, mocker: MockerFixture, control=False, alt=False, shift=False):
    return mocker.Mock(
        GetKeyCode=mocker.Mock(return_value=keycode),
        ControlDown=mocker.Mock(return_value=control),
        AltDown=mocker.Mock(return_value=alt),
        ShiftDown=mocker.Mock(return_value=shift),
    )


def test_set_mode_hex_limits_length_and_autoadvance(wx_harness, mocker) -> None:
    tc = HexTextCtrl(wx_harness.frame, wx.ID_ANY, mocker.Mock())

    tc.set_mode("hex")

    assert tc.autoadvance == 2
    assert tc.userpressed is False


def test_editing_new_cell_sets_value_and_selects_text(wx_harness, mocker) -> None:
    tc = HexTextCtrl(wx_harness.frame, wx.ID_ANY, mocker.Mock())

    tc.editing_new_cell("ab", mode="hex")

    assert tc.GetValue() == "ab"
    assert tc.startValue == "ab"
    assert tc.mode == "hex"


def test_insert_first_key_accepts_valid_hex_digit(wx_harness, mocker) -> None:
    tc = HexTextCtrl(wx_harness.frame, wx.ID_ANY, mocker.Mock())
    tc.set_mode("hex")

    result = tc.insert_first_key(ord("A"))

    assert result is True
    assert tc.GetValue() == "A"
    assert tc.userpressed is True


def test_insert_first_key_rejects_non_hex_digit(wx_harness, mocker) -> None:
    tc = HexTextCtrl(wx_harness.frame, wx.ID_ANY, mocker.Mock())
    tc.set_mode("hex")

    result = tc.insert_first_key(ord("Z"))

    assert result is False
    assert tc.GetValue() == ""
    assert tc.userpressed is False


def test_on_key_down_backspace_resets_value_to_start_value(wx_harness, mocker) -> None:
    tc = HexTextCtrl(wx_harness.frame, wx.ID_ANY, mocker.Mock())
    tc.editing_new_cell("ab", mode="hex")
    tc.SetValue("a")

    tc.on_key_down(_key_event(wx.WXK_BACK, mocker=mocker))

    assert tc.GetValue() == ""


def test_on_key_down_tab_schedules_advance_cursor(wx_harness, mocker) -> None:
    parentgrid = mocker.Mock()
    tc = HexTextCtrl(wx_harness.frame, wx.ID_ANY, parentgrid)
    tc.editing_new_cell("ab", mode="hex")

    tc.on_key_down(_key_event(wx.WXK_TAB, mocker=mocker))
    wx.GetApp().Yield()

    parentgrid._advance_cursor.assert_called_once()


def test_on_key_down_escape_resets_value_and_schedules_abort_edit(
    wx_harness, mocker
) -> None:
    parentgrid = mocker.Mock()
    tc = HexTextCtrl(wx_harness.frame, wx.ID_ANY, parentgrid)
    tc.editing_new_cell("ab", mode="hex")
    tc.SetValue("c")

    tc.on_key_down(_key_event(wx.WXK_ESCAPE, mocker=mocker))
    wx.GetApp().Yield()

    assert tc.GetValue() == "ab"
    parentgrid._abort_edit.assert_called_once()


def test_on_key_down_valid_hex_digit_flags_userpressed_and_skips_event(
    wx_harness, mocker
) -> None:
    tc = HexTextCtrl(wx_harness.frame, wx.ID_ANY, mocker.Mock())
    tc.set_mode("hex")
    event = _key_event(ord("B"), mocker=mocker)

    tc.on_key_down(event)

    assert tc.userpressed is True
    event.Skip.assert_called_once()


def test_on_key_down_invalid_hex_digit_is_swallowed(wx_harness, mocker) -> None:
    tc = HexTextCtrl(wx_harness.frame, wx.ID_ANY, mocker.Mock())
    tc.set_mode("hex")
    event = _key_event(ord("Z"), mocker=mocker)

    tc.on_key_down(event)

    assert tc.userpressed is False
    event.Skip.assert_not_called()


def test_on_text_advances_cursor_once_max_length_reached(wx_harness, mocker) -> None:
    parentgrid = mocker.Mock()
    tc = HexTextCtrl(wx_harness.frame, wx.ID_ANY, parentgrid)
    tc.editing_new_cell("00", mode="hex")

    tc.insert_first_key(ord("A"))  # 1 char, autoadvance=2 -> not yet
    parentgrid._advance_cursor.assert_not_called()

    tc.SetValue("AB")  # userpressed still True from insert_first_key
    tc.SetInsertionPointEnd()
    tc.on_text(mocker.Mock(GetString=mocker.Mock(return_value="AB")))
    wx.GetApp().Yield()

    parentgrid._advance_cursor.assert_called_once()


def test_is_accepted_key_rejects_control_and_alt_modifiers(wx_harness, mocker) -> None:
    grid = mocker.Mock()
    editor = HexCellEditor(grid)

    assert editor.IsAcceptedKey(_key_event(ord("A"), control=True, mocker=mocker)) is False
    assert editor.IsAcceptedKey(_key_event(ord("A"), alt=True, mocker=mocker)) is False
    assert editor.IsAcceptedKey(_key_event(wx.WXK_SHIFT, mocker=mocker)) is False
    assert editor.IsAcceptedKey(_key_event(ord("A"), mocker=mocker)) is True
