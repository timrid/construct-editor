from __future__ import annotations

import dataclasses

import wx
import wx.lib.wordwrap

# how long the mouse has to hover a cell before the tooltip appears
_SHOW_DELAY_MS = 500

# how often we poll the mouse position to decide whether the tooltip
# (still pending, or already shown) is still relevant
_POLL_INTERVAL_MS = 100

_MAX_TEXT_WIDTH_DEFAULT = 450
# clamps how tall the popup (and its wx.TextCtrl) can grow - text that
# doesn't fit is reachable via the TextCtrl's own native scrollbar instead
_MAX_TEXT_HEIGHT_DEFAULT = 200
_PADDING = 4


def _get_text_ctrl_size(
    dc: wx.DC,
    text: str,
    max_text_width: int,
    max_text_height: int,
) -> tuple[int, int, bool]:
    """
    Determines the size needed for a `wx.TextCtrl` showing `text`, clamped
    to `max_text_width`/`max_text_height`. The actual line-wrapping (at
    `max_text_width`) is delegated to `wx.lib.wordwrap.wordwrap()`, which
    measures directly via `dc` (no throwaway widget needed) and returns the
    text with hard line breaks inserted at the wrap points. `dc` is then
    used to measure the already-wrapped text in a single call.

    The wrapped text returned by `wordwrap()` is used ONLY for this
    measurement - it is deliberately NOT what gets shown in the
    `wx.TextCtrl` (see `WxHoverToolTipPopup.__init__`), since its hard
    line breaks would otherwise end up in copy-pasted text. The
    `wx.TextCtrl` instead displays the original `text` and relies on its
    own native soft word-wrap (no `wx.TE_DONTWRAP`/`wx.TE_NO_VSCROLL`-only
    style) to wrap it visually at render time, without altering `GetValue()`.
    """
    wrapped_text = wx.lib.wordwrap.wordwrap(text, max_text_width, dc)

    content_width, full_content_height = dc.GetMultiLineTextExtent(wrapped_text)
    # a single word that is on its own wider than `max_text_width` is
    # broken at a character boundary by `wordwrap()`, but the resulting
    # width still needs to be clamped here just in case
    content_width = min(content_width, max_text_width)
    content_height = min(full_content_height, max_text_height)

    needs_vscroll = full_content_height > max_text_height

    return content_width, content_height, needs_vscroll


class WxHoverToolTipPopup(wx.PopupWindow):
    """
    A tooltip-like popup window that hosts a read-only, multiline
    `wx.TextCtrl`, so its text can be selected and copied by the user -
    unlike a native tooltip.

    Like `wx.lib.agw.supertooltip.ToolTipWindow`, this is a throwaway
    window: a fresh instance is created (and fully sized/positioned/shown)
    for every tooltip, and it is `Destroy()`-ed once it should disappear,
    instead of being hidden and reused for the next tooltip.
    """

    def __init__(
        self,
        parent: wx.Window,
        text: str,
        anchor_screen_rect: wx.Rect,
        max_text_width: int,
        max_text_height: int,
        bg_colour: wx.Colour | None = None,
        fg_colour: wx.Colour | None = None,
    ):
        # `wx.PU_CONTAINS_CONTROLS` is required (MSW-only) for a child
        # control such as our `wx.TextCtrl` to be able to take focus at
        # all - by default a `wx.PopupWindow` never lets its children take
        # focus from the parent window, which silently breaks native
        # mouse-drag text selection (it relies on the control actually
        # being focused), even though `SetFocus()` calls on it don't raise
        # any error.
        # `wx.SIMPLE_BORDER` gives the popup a thin native border - a
        # manually-painted border was tried first but never actually
        # rendered, so this relies on the native border instead.
        wx.PopupWindow.__init__(self, parent, flags=wx.SIMPLE_BORDER | wx.PU_CONTAINS_CONTROLS)

        # A light gray background (`#F9F9F9`, matching the standard Windows
        # tooltip colour - no `wx.SYS_COLOUR_*` constant matches it exactly),
        # instead of the yellowish `wx.SYS_COLOUR_INFOBK`.
        if bg_colour is None:
            bg_colour = wx.Colour(0xF9, 0xF9, 0xF9)
        if fg_colour is None:
            fg_colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        self.SetBackgroundColour(bg_colour)

        dc = wx.ClientDC(self)
        dc.SetFont(self.GetFont())
        content_width, content_height, needs_vscroll = _get_text_ctrl_size(dc, text, max_text_width, max_text_height)

        # `wx.TE_NO_VSCROLL` must be applied at construction time (it has
        # no effect if toggled afterwards), and a multiline `wx.TextCtrl`
        # *without* it always reserves space for - and shows - a native
        # vertical scrollbar on MSW, even when the text fully fits without
        # one. So it's only omitted when the text actually needs a
        # scrollbar (i.e. was clipped to `_MAX_TEXT_HEIGHT`).
        style = wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_NONE
        if not needs_vscroll:
            style |= wx.TE_NO_VSCROLL

        self._text_ctrl = wx.TextCtrl(self, value=text, style=style)
        self._text_ctrl.SetBackgroundColour(bg_colour)
        self._text_ctrl.SetForegroundColour(fg_colour)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._text_ctrl, 1, wx.EXPAND | wx.ALL, _PADDING)
        self.SetSizer(sizer)

        # `SetClientSize()` (rather than `SetSize()`) accounts for the
        # popup's native `wx.SIMPLE_BORDER`, so the text area itself ends up
        # exactly this size - otherwise the border would eat into it,
        # clipping the last column/row of text.
        self.SetClientSize(wx.Size(content_width + 2 * _PADDING, content_height + 2 * _PADDING))
        self.Layout()
        self._position_at(anchor_screen_rect)

        self.Show()
        self._text_ctrl.HideNativeCaret()

    def _position_at(self, anchor_screen_rect: wx.Rect):
        """
        Positions the popup below the given anchor rect (which must be in
        screen coordinates), clamped to the display the anchor is on.
        """
        # The popup's actual outer size (including the border) is what
        # matters for screen-edge clamping below.
        popup_size = self.GetSize()

        popup_pos = wx.Point(anchor_screen_rect.x, anchor_screen_rect.GetBottom())

        # Clamp to the display the anchor is actually on (not necessarily
        # the primary display), so multi-monitor setups are positioned
        # correctly instead of being clamped back onto display 0.
        display_index = wx.Display.GetFromPoint(anchor_screen_rect.GetPosition())
        if display_index == wx.NOT_FOUND:
            display_index = 0
        display_rect = wx.Display(display_index).GetGeometry()

        if popup_pos.x + popup_size.x > display_rect.GetRight():
            popup_pos.x = display_rect.GetRight() - popup_size.x
        if popup_pos.y + popup_size.y > display_rect.GetBottom():
            popup_pos.y = anchor_screen_rect.y - popup_size.y
        popup_pos.x = max(popup_pos.x, display_rect.x)
        popup_pos.y = max(popup_pos.y, display_rect.y)
        self.SetPosition(popup_pos)


@dataclasses.dataclass(frozen=True)
class _HoverState:
    text: str
    anchor_screen_rect: wx.Rect


class WxHoverToolTip:
    """
    Shows a persistent, text-selectable tooltip anchored to a target window.

    Unlike a native tooltip, this tooltip:
      - does not disappear automatically after a few seconds
      - can be entered with the mouse, to select/copy its text
      - only closes once the mouse has genuinely left both the triggering
        area and the tooltip popup itself - determined geometrically (via
        a periodic poll of the actual mouse position), not via fragile
        per-window enter/leave events
    """

    def __init__(
        self,
        target: wx.Window,
        show_delay_ms: int = _SHOW_DELAY_MS,
        poll_interval_ms: int = _POLL_INTERVAL_MS,
        max_text_width: int = _MAX_TEXT_WIDTH_DEFAULT,
        max_text_height: int = _MAX_TEXT_HEIGHT_DEFAULT,
        bg_colour: wx.Colour | None = None,
        fg_colour: wx.Colour | None = None,
    ):
        self._target = target
        self._show_delay_ms = show_delay_ms
        self._poll_interval_ms = poll_interval_ms
        self._max_text_width = max_text_width
        self._max_text_height = max_text_height
        self._bg_colour = bg_colour
        self._fg_colour = fg_colour

        self._popup: WxHoverToolTipPopup | None = None

        self._current_state: _HoverState | None = None
        self._pending_state: _HoverState | None = None

        # the window that held keyboard focus right before the popup first
        # stole it (see `_on_show_timer`) during the current hover session -
        # `None` whenever no popup has stolen focus yet
        self._prior_focus_owner: wx.Window | None = None

        self._show_timer: wx.CallLater[[], None] | None = None
        self._poll_timer = wx.Timer()
        self._poll_timer.Bind(wx.EVT_TIMER, self._on_poll_timer)

    def notify_hover(self, text: str, anchor_screen_rect: wx.Rect):
        """
        Called (eg. from a mouse-motion handler) while the mouse is over a
        region that should show `text` in the tooltip. Re-hovering the same
        `text` at the same `anchor_screen_rect` (ie. the currently-shown or
        still-pending content) is a no-op.
        """
        new_state = _HoverState(text, wx.Rect(anchor_screen_rect))

        # If the new state is identical to either the current or pending state,
        # don't reset the show timer (which would restart the delay) or
        # change the pending state.
        if self._current_state == new_state or self._pending_state == new_state:
            return

        # If the new state is different, cancel any pending show and start a new show timer.
        self._stop_show_timer()
        self._pending_state = new_state
        self._show_timer = wx.CallLater(self._show_delay_ms, self._on_show_timer)
        self._start_poll_timer()

    def hide(self):
        """Hides the tooltip immediately, cancelling any pending timers."""
        self._stop_show_timer()
        self._stop_poll_timer()
        self._current_state = None
        self._pending_state = None
        self._restore_prior_focus_owner()
        self._destroy_popup()

    def _restore_prior_focus_owner(self):
        """
        Restores keyboard focus to the window captured (in `_on_show_timer`)
        as having had focus right before the popup stole it - but only if
        focus is still on the popup (or its `TextCtrl`) at this point, so a
        deliberate focus change elsewhere by the user while the popup
        happened to still be open is never overridden.
        """
        owner = self._prior_focus_owner
        self._prior_focus_owner = None
        if owner is None:
            return

        popup = self._popup
        if popup is None:
            return
        # `wx.Window.FindFocus()`'s stub claims a non-optional return, but
        # it can genuinely return `None` at runtime (nothing focused) - the
        # `try` guards against that mismatch as well as a since-destroyed
        # `focused` window.
        try:
            focused = wx.Window.FindFocus()
            focus_is_on_popup = focused is popup or focused.GetParent() is popup
        except (AttributeError, RuntimeError):
            focus_is_on_popup = False
        if not focus_is_on_popup:
            return

        try:
            owner.SetFocus()
        except RuntimeError:
            # the prior focus owner was destroyed in the meantime
            pass

    def _destroy_popup(self):
        if self._popup is None:
            return
        popup = self._popup
        self._popup = None
        try:
            popup.Destroy()
        except RuntimeError:
            # already destroyed (e.g. its parent window went away)
            pass

    def _check_still_relevant(self):
        """
        Re-checks the current mouse position against the pending/current
        hover target (and, if shown, the popup itself), hiding or
        cancelling the pending show if the mouse has genuinely left. Called
        periodically by the poll timer.
        """
        mouse_pos = wx.GetMousePosition()

        # If the mouse has moved outside the pending hover target, cancel the pending show (if any)
        if self._pending_state is not None and not self._pending_state.anchor_screen_rect.Contains(mouse_pos):
            self._stop_show_timer()
            self._pending_state = None

        # Don't hide the currently-shown popup while a *different* hover
        # target is already pending - this lets the mouse move directly
        # from one hoverable cell to another without a hide-then-show
        # flicker; the popup is simply repositioned/updated in place once
        # the new pending target's show delay elapses.
        if self._pending_state is None and self._current_state is not None:
            # Create a new `wx.Rect`, because `wx.Rect.Union()` will mutate the rect
            relevant_rect = wx.Rect(self._current_state.anchor_screen_rect)
            try:
                if self._popup is not None and self._popup.IsShown():
                    relevant_rect = relevant_rect.Union(self._popup.GetScreenRect())
            except RuntimeError:
                # The popup's underlying C++ object has already been destroyed (e.g. its parent window went away).
                # Clear state immediately so we don't keep polling forever with stale current data.
                self.hide()
                return

            if not relevant_rect.Contains(mouse_pos):
                self.hide()

        if self._pending_state is None and self._current_state is None:
            self._stop_poll_timer()

    def _start_poll_timer(self):
        if not self._poll_timer.IsRunning():
            self._poll_timer.Start(self._poll_interval_ms)

    def _stop_poll_timer(self):
        if self._poll_timer.IsRunning():
            self._poll_timer.Stop()

    def _on_poll_timer(self, event: wx.TimerEvent):
        self._check_still_relevant()

    def _stop_show_timer(self):
        if self._show_timer is not None:
            self._show_timer.Stop()
            self._show_timer = None

    def _on_show_timer(self):
        self._show_timer = None
        if self._pending_state is None:
            return
        text = self._pending_state.text
        rect = self._pending_state.anchor_screen_rect
        self._current_state = self._pending_state
        self._pending_state = None
        # Any previous popup is fully destroyed before creating the new
        # one - a fresh popup is always created from scratch for each
        # shown tooltip rather than being reused.
        self._destroy_popup()
        # Only capture once per hover session (ie. only while no prior
        # focus owner is already tracked) - switching directly between
        # tooltip-triggering cells destroys+recreates the popup without a
        # visible hide gap, and re-capturing on every such switch would
        # just capture the popup's own (already-stolen) focus instead of
        # the window that had focus before the FIRST popup in this chain.
        if self._prior_focus_owner is None:
            self._prior_focus_owner = wx.Window.FindFocus()
        try:
            self._popup = WxHoverToolTipPopup(
                self._target,
                text,
                rect,
                max_text_width=self._max_text_width,
                max_text_height=self._max_text_height,
                bg_colour=self._bg_colour,
                fg_colour=self._fg_colour,
            )
        except RuntimeError:
            # the target was destroyed in the meantime
            self._popup = None
