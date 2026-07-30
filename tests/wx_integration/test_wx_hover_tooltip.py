# pyright: reportPrivateUsage=false
from __future__ import annotations

import wx

from construct_editor.wx_widgets.wx_hover_tooltip import _POLL_INTERVAL_MS, WxHoverToolTip
from tests.wx_integration.wx_test_helpers import WxTestHarness

_SHOW_DELAY_MS = 30
_MARGIN_MS = 120


def _anchor_rect(harness: WxTestHarness, x: int, y: int, width: int, height: int) -> wx.Rect:
    """Builds an anchor rect at `(x, y)`/`(width, height)` relative to the
    harness frame's client area, converted to screen coordinates.
    """
    screen_pos = harness.frame.ClientToScreen(wx.Point(x, y))
    return wx.Rect(screen_pos, wx.Size(width, height))


def test_popup_appears_with_text_after_show_delay(wx_harness: WxTestHarness):
    tooltip = WxHoverToolTip(
        wx_harness.frame,
        show_delay_ms=_SHOW_DELAY_MS,
    )

    # Position the mouse over a small anchor rect
    anchor = _anchor_rect(wx_harness, 10, 10, 50, 20)
    wx_harness.move_mouse_to(anchor.GetPosition(), delay_ms=0)

    # Show the tooltip
    tooltip.notify_hover("hello world", anchor)

    # Check that the tooltip is not showing yet, because the show delay has not elapsed
    popup = tooltip._popup
    assert popup is None

    # Wait for the show delay to elapse
    wx_harness.wait_ms(_SHOW_DELAY_MS + _MARGIN_MS)

    # Check that the tooltip is actually showing
    popup = tooltip._popup
    assert popup is not None
    assert popup.IsShown()

    # Check that the tooltip has the correct text and is read only
    assert popup._text_ctrl.GetValue() == "hello world"
    assert not popup._text_ctrl.IsEditable()

    # Check that the tooltip is positioned directly below the anchor rect
    position = popup.GetPosition()
    assert position.x == anchor.x
    assert position.y == anchor.GetBottom()

    # Move the mouse into the popup's text control, and check that the tooltip is still showing
    text_ctrl = popup._text_ctrl
    text_ctrl_center = wx.Point(
        text_ctrl.GetScreenRect().x + text_ctrl.GetScreenRect().width // 2,
        text_ctrl.GetScreenRect().y + text_ctrl.GetScreenRect().height // 2,
    )
    wx_harness.move_mouse_linear(text_ctrl_center)
    wx_harness.wait_ms(_POLL_INTERVAL_MS + _MARGIN_MS)

    # Check that the tooltip is still showing after moving the mouse into it
    assert popup.IsShown()


def test_hovering_the_same_content_again_keeps_the_same_popup_shown(wx_harness: WxTestHarness):
    tooltip = WxHoverToolTip(
        wx_harness.frame,
        show_delay_ms=_SHOW_DELAY_MS,
    )
    anchor = _anchor_rect(wx_harness, 10, 10, 50, 20)
    wx_harness.move_mouse_to(anchor.GetPosition(), delay_ms=0)

    tooltip.notify_hover("hello", anchor)
    wx_harness.wait_ms(_SHOW_DELAY_MS + _MARGIN_MS)
    popup_before = tooltip._popup

    wx_harness.move_mouse_to(anchor.GetPosition(), delay_ms=0)
    tooltip.notify_hover("hello", anchor)
    popup_after = tooltip._popup

    assert popup_before is popup_after
    assert popup_after is not None
    assert popup_after.IsShown()


def test_hovering_different_content_before_show_delay_replaces_pending_content(wx_harness: WxTestHarness):
    tooltip = WxHoverToolTip(
        wx_harness.frame,
        show_delay_ms=_SHOW_DELAY_MS,
    )

    anchor = _anchor_rect(wx_harness, 10, 10, 50, 20)
    wx_harness.move_mouse_to(anchor.GetPosition(), delay_ms=0)

    tooltip.notify_hover("content-a", anchor)
    tooltip.notify_hover("content-b", anchor)
    wx_harness.wait_ms(_SHOW_DELAY_MS + _MARGIN_MS)

    popup = tooltip._popup
    assert popup is not None
    assert popup.IsShown()
    assert popup._text_ctrl.GetValue() == "content-b"


def test_poll_tick_hides_popup_once_mouse_leaves_the_anchor_and_popup(wx_harness: WxTestHarness):
    tooltip = WxHoverToolTip(
        wx_harness.frame,
        show_delay_ms=_SHOW_DELAY_MS,
    )
    anchor = _anchor_rect(wx_harness, 10, 10, 50, 20)
    wx_harness.move_mouse_to(anchor.GetPosition(), delay_ms=0)

    # Show the tooltip
    tooltip.notify_hover("hello", anchor)
    wx_harness.wait_ms(_SHOW_DELAY_MS + _MARGIN_MS)

    # Check that the tooltip is actually showing
    popup = tooltip._popup
    assert popup is not None
    assert popup.IsShown()

    # Move the mouse to a point above the anchor rect, so that it is no longer over
    # the anchor or the popup
    above_anchor_point = wx.Point(anchor.x, anchor.y - 10)
    wx_harness.move_mouse_to(above_anchor_point, delay_ms=0)
    wx_harness.wait_ms(_POLL_INTERVAL_MS + _MARGIN_MS)

    # Tooltip should be hidden now
    assert tooltip._popup is None


def test_poll_tick_cancels_a_pending_show_once_mouse_leaves_before_the_delay_elapses(wx_harness: WxTestHarness):
    tooltip = WxHoverToolTip(
        wx_harness.frame,
        show_delay_ms=_SHOW_DELAY_MS,
    )
    anchor = _anchor_rect(wx_harness, 20, 20, 10, 10)
    wx_harness.move_mouse_to(anchor.GetPosition(), delay_ms=0)

    # Notify that the mouse is hovering over some content, but do not wait for the show delay to elapse yet
    tooltip.notify_hover("hello", anchor)

    # Move the mouse to a point above the anchor rect, so that it is no longer over the anchor
    above_anchor_point = wx.Point(anchor.x, anchor.y - 10)
    wx_harness.move_mouse_to(above_anchor_point, delay_ms=0)
    wx_harness.wait_ms(_SHOW_DELAY_MS + _MARGIN_MS)

    # Check that the tooltip is not showing, because the mouse left before the show delay elapsed
    popup = tooltip._popup
    assert popup is None

    # re-hovering the same content afterwards must restart the show timer -
    # proving the pending content was actually cleared, not left stale
    wx_harness.move_mouse_to(anchor.GetPosition(), delay_ms=0)
    tooltip.notify_hover("hello", anchor)
    wx_harness.wait_ms(_SHOW_DELAY_MS + _MARGIN_MS)

    # Check that the tooltip is now showing
    popup = tooltip._popup
    assert popup is not None
    assert popup.IsShown()


def test_switching_to_different_hoverable_content_does_not_flicker_hide_the_old_popup(wx_harness: WxTestHarness):
    tooltip = WxHoverToolTip(
        wx_harness.frame,
        show_delay_ms=_SHOW_DELAY_MS,
    )
    anchor_a = _anchor_rect(wx_harness, 20, 30, 10, 10)
    wx_harness.move_mouse_to(anchor_a.GetPosition(), delay_ms=0)

    # Show the tooltip for the first content
    tooltip.notify_hover("content-a", anchor_a)
    wx_harness.wait_ms(_SHOW_DELAY_MS + _MARGIN_MS)

    # Check that the tooltip is actually showing
    popup = tooltip._popup
    assert popup is not None
    assert popup.IsShown()

    # mouse moved directly to a different, hoverable cell - a new
    # hover is pending, so the still-shown old popup must not flicker-hide
    # while waiting for the new content's own show delay to elapse.
    anchor_b = wx.Rect(anchor_a.x, anchor_a.y - 20, 10, 10)
    wx_harness.move_mouse_to(anchor_b.GetPosition(), delay_ms=0)
    tooltip.notify_hover("content-b", anchor_b)

    # Check that the tooltip is still showing the old content
    popup = tooltip._popup
    assert popup is not None
    assert popup.IsShown()
    assert popup._text_ctrl.GetValue() == "content-a"

    # Wait for the new content's show delay to elapse, at which point the old
    # popup should be replaced by a new one showing the new content.
    wx_harness.wait_ms(_SHOW_DELAY_MS + _MARGIN_MS)

    new_popup = tooltip._popup
    assert new_popup is not popup
    assert new_popup is not None
    assert new_popup.IsShown()
    assert new_popup._text_ctrl.GetValue() == "content-b"


def test_hide_hides_the_popup_immediately(wx_harness: WxTestHarness):
    tooltip = WxHoverToolTip(
        wx_harness.frame,
        show_delay_ms=_SHOW_DELAY_MS,
    )
    anchor = _anchor_rect(wx_harness, 20, 20, 10, 10)
    wx_harness.move_mouse_to(anchor.GetPosition(), delay_ms=0)

    # Show the tooltip
    tooltip.notify_hover("hello", anchor)
    wx_harness.wait_ms(_SHOW_DELAY_MS + _MARGIN_MS)

    assert tooltip._popup is not None

    # Hide the tooltip
    tooltip.hide()

    # Tooltip should be destroyed immediately
    assert tooltip._popup is None


def test_long_text_is_wrapped_onto_multiple_lines(wx_harness: WxTestHarness):
    tooltip = WxHoverToolTip(
        wx_harness.frame,
        show_delay_ms=_SHOW_DELAY_MS,
    )
    anchor = _anchor_rect(wx_harness, 20, 20, 10, 10)
    wx_harness.move_mouse_to(anchor.GetPosition(), delay_ms=0)

    long_text = " ".join(["word"] * 200)
    tooltip.notify_hover(long_text, anchor)
    wx_harness.wait_ms(_SHOW_DELAY_MS + _MARGIN_MS)

    popup = tooltip._popup
    assert popup is not None
    # the wx.TextCtrl must show the ORIGINAL, unwrapped text - no hard
    # line breaks - so that copy-pasting it doesn't carry any wrap-point
    # newlines along; wrapping onto multiple lines is purely the
    # wx.TextCtrl's own visual (soft) word-wrap.
    assert popup._text_ctrl.GetValue() == long_text
    # proves it actually wrapped onto multiple lines (rather than just
    # growing horizontally forever): the popup's clamped client height is
    # noticeably taller than a single line of text.
    single_line_height = popup._text_ctrl.GetCharHeight()
    assert popup.GetClientSize().height > single_line_height * 2


def test_popup_is_clamped_within_its_display(wx_harness: WxTestHarness):
    tooltip = WxHoverToolTip(
        wx_harness.frame,
        show_delay_ms=_SHOW_DELAY_MS,
    )

    # anchor right at the bottom-right corner of the display, so the popup
    # would overflow off-screen unless it is clamped
    display_index = wx.Display.GetFromWindow(wx_harness.frame)
    if display_index == wx.NOT_FOUND:
        raise RuntimeError("Test frame is not on any display, cannot test clamping")
    display_rect = wx.Display(display_index).GetGeometry()
    anchor = wx.Rect(display_rect.GetRight() - 5, display_rect.GetBottom() - 5, 10, 10)
    wx_harness.move_mouse_to(anchor.GetPosition(), delay_ms=0)

    # Show the tooltip
    tooltip.notify_hover("hello", anchor)
    wx_harness.wait_ms(_SHOW_DELAY_MS + _MARGIN_MS)

    # Check that the tooltip is actually showing and is clamped within the display
    popup = tooltip._popup
    assert popup is not None
    assert popup.GetRect().GetRight() <= display_rect.GetRight()
    assert popup.GetRect().GetBottom() <= display_rect.GetBottom()


def test_popup_closes_when_frame_is_closed(wx_harness: WxTestHarness):
    tooltip = WxHoverToolTip(
        wx_harness.frame,
        show_delay_ms=_SHOW_DELAY_MS,
    )

    # Position the mouse over a small anchor rect
    anchor = _anchor_rect(wx_harness, 10, 10, 50, 20)
    wx_harness.move_mouse_to(anchor.GetPosition(), delay_ms=0)

    # Show the tooltip
    tooltip.notify_hover("hello world", anchor)
    wx_harness.wait_ms(_SHOW_DELAY_MS + _MARGIN_MS)

    # Check that the tooltip is actually showing
    popup = tooltip._popup
    assert popup is not None
    assert popup.IsShown()

    # Close the frame, which should also close the tooltip popup after the next poll tick
    wx_harness.frame.Close()
    wx_harness.wait_ms(_POLL_INTERVAL_MS + _MARGIN_MS)

    # Check that the tooltip popup is no longer showing after the frame is closed
    popup = tooltip._popup
    assert popup is None
