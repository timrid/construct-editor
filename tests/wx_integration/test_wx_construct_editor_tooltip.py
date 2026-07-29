# pyright: reportPrivateUsage=false
from __future__ import annotations

import construct as cs
import wx

from construct_editor.core.model import ConstructEditorColumn
from construct_editor.wx_widgets.wx_construct_editor import WxConstructEditor
from tests.wx_integration.wx_test_helpers import (
    WxTestHarness,
    construct_editor_cell_screen_rect,
)

_SHOW_DELAY_MS = 30
_MARGIN_MS = 150
# comfortably larger than WxHoverToolTip's production poll interval (100ms)
# plus a safety margin, so these tests reliably observe a poll tick.
_POLL_MARGIN_MS = 250

# long enough (after wrapping) to exceed wx_hover_tooltip's _MAX_TEXT_HEIGHT
# clamp, so the popup's wx.TextCtrl needs its own native vertical scrollbar
_LONG_ROOT_DOCS = "This is a very long line of documentation text that repeats many times. " * 30


def _make_editor(
    harness: WxTestHarness,
    root_docs: str = "This is a documentation to the root.",
) -> WxConstructEditor:
    """Create a WxConstructEditor with one parsed row (the root struct)."""
    editor = WxConstructEditor(
        harness.frame,
        cs.Renamed(
            cs.Struct(cs.Renamed(cs.Int8ub, "value", "This is a documentation to the value.")),
            "root",
            root_docs,
        ),
    )
    editor.parse(b"\x01")

    # Speed up the tooltip's show delay for testing, so we don't have to wait
    editor._hover_tooltip._show_delay_ms = _SHOW_DELAY_MS

    harness.frame.Layout()
    harness.app.Yield()
    return editor


def _name_cell_screen_rect(editor: WxConstructEditor) -> wx.Rect:
    model = editor._model
    root_entry = model.root_entry
    assert root_entry is not None
    return construct_editor_cell_screen_rect(editor, root_entry, ConstructEditorColumn.Name)


def _center_of(rect: wx.Rect) -> wx.Point:
    return wx.Point(rect.x + rect.width // 2, rect.y + rect.height // 2)


def test_hovering_the_name_cell_shows_a_tooltip_positioned_directly_below_it(
    wx_harness,
) -> None:
    editor = _make_editor(wx_harness)

    # Move the mouse over the name cell to show the tooltip, then move it
    cell_rect = _name_cell_screen_rect(editor)
    wx_harness.move_mouse_to(_center_of(cell_rect))
    wx_harness.wait_ms(_SHOW_DELAY_MS + _MARGIN_MS)

    # Check that the tooltip is actually showing, and that it is positioned
    popup = editor._hover_tooltip._popup
    assert popup is not None
    assert popup.IsShown()
    assert popup._text_ctrl.GetValue() == "This is a documentation to the root."

    # directly below the hovered cell - not offset by an extra row, as
    # happened when the dvc header offset was counted twice.
    assert popup.GetPosition() == wx.Point(cell_rect.x, cell_rect.GetBottom())


def test_moving_the_mouse_slowly_into_the_popup_to_select_text_does_not_hide_it(
    wx_harness,
) -> None:
    # Uses long root docs, so the popup's wx.TextCtrl needs its own native
    # vertical scrollbar - this also lets this test cover hovering over
    # that scrollbar further below.
    editor = _make_editor(wx_harness, root_docs=_LONG_ROOT_DOCS)

    # Move the mouse over the name cell to show the tooltip, then move it
    cell_rect = _name_cell_screen_rect(editor)
    cell_center = _center_of(cell_rect)
    wx_harness.move_mouse_to(cell_center)
    wx_harness.wait_ms(_SHOW_DELAY_MS + _MARGIN_MS)

    # Check that the tooltip is actually showing before we move the mouse into it
    popup = editor._hover_tooltip._popup
    assert popup is not None
    assert popup.IsShown()

    # Move the mouse "slowly" from the cell down into the popup itself, and
    # then further onto its child text_ctrl (as if about to select text),
    # taking a few small steps with real delays in between - this is the
    # exact scenario that used to make the popup disappear on its own (a
    # nested wx.EVT_ENTER_WINDOW/EVT_LEAVE_WINDOW artifact between the
    # popup and its child - now replaced by a geometric check of the real
    # mouse position against the popup's own screen rect).
    text_ctrl = popup._text_ctrl
    text_ctrl_center = _center_of(text_ctrl.GetScreenRect())
    wx_harness.move_mouse_linear(text_ctrl_center)
    wx_harness.wait_ms(_POLL_MARGIN_MS)

    # Check that the tooltip is still showing after moving the mouse into it
    assert popup.IsShown()

    # Regression: moving further onto the text_ctrl's own vertical
    # scrollbar (its docs are long enough to need one) used to hide the
    # popup immediately - the scrollbar is part of the text_ctrl's native
    # window, so entering it used to fire a spurious EVT_LEAVE_WINDOW on
    # the text_ctrl without any matching new enter elsewhere. The
    # geometric containment check against the popup's own screen rect is
    # unaffected by which specific child window the mouse is over.
    text_ctrl_rect = text_ctrl.GetScreenRect()
    scrollbar_width = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
    scrollbar_point = wx.Point(
        text_ctrl_rect.GetRight() - max(scrollbar_width, 1) // 2,
        text_ctrl_rect.y + text_ctrl_rect.height // 2,
    )
    wx_harness.move_mouse_linear(scrollbar_point)
    wx_harness.wait_ms(_POLL_MARGIN_MS)

    # Check that the tooltip is still showing after moving the mouse onto the scrollbar
    assert popup.IsShown()


def test_moving_the_mouse_out_of_the_dvc_towards_other_gui_elements_hides_the_tooltip(
    wx_harness,
) -> None:
    editor = _make_editor(wx_harness)

    # Move the mouse over the name cell to show the tooltip, then move it
    cell_rect = _name_cell_screen_rect(editor)
    wx_harness.move_mouse_to(_center_of(cell_rect))
    wx_harness.wait_ms(_SHOW_DELAY_MS + _MARGIN_MS)

    # Check that the tooltip is actually showing before we move the mouse away from it
    popup = editor._hover_tooltip._popup
    assert popup is not None
    assert popup.IsShown()

    # Move the mouse away from the dvc entirely, towards another real GUI
    # element - the editor's own status bar, sitting right below the dvc -
    # simulating the mouse leaving for another part of the GUI. This is
    # detected by the tooltip's own periodic poll of the real mouse
    # position (not a dedicated wx.EVT_LEAVE_WINDOW handler on the dvc):
    # wx.EVT_KILL_FOCUS alone never fires for plain mouse movement without
    # a click.
    status_bar = editor._status_bar
    wx_harness.move_mouse_linear(_center_of(status_bar.GetScreenRect()))
    wx_harness.wait_ms(_POLL_MARGIN_MS)

    # Check that the tooltip is no longer showing after moving the mouse away
    popup = editor._hover_tooltip._popup
    assert popup is None
