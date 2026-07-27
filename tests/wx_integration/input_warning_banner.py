"""Advisory on-screen warning shown while wx.UIActionSimulator-driven tests
are running.

`wx.UIActionSimulator` injects genuine OS-level input (Win32 SendInput),
which can collide with a developer's real mouse/keyboard use on the same
machine. This is a purely visual warning — actually suppressing physical
input via the Win32 `BlockInput` API was tried and rejected; see
docs/adr/0001-warn-instead-of-block-physical-input-during-local-wx-ui-tests.md.
"""

from __future__ import annotations

import wx

_BANNER_TEXT = (
    "wx UI test in progress\n"
    "Simulated mouse/keyboard input is running for the test session.\n"
    "Avoid touching the mouse/keyboard until it finishes."
)


def show_input_warning_banner() -> wx.Frame:
    """Show a persistent, always-on-top banner warning that simulated input
    is running. Caller must `Destroy()` the returned frame once done.
    """
    banner = wx.Frame(
        None,
        title="wx UI test in progress",
        # style=wx.STAY_ON_TOP | wx.CAPTION | wx.FRAME_NO_TASKBAR,
    )
    text = wx.StaticText(banner, label=_BANNER_TEXT, style=wx.ALIGN_CENTER)
    text.SetForegroundColour(wx.Colour(200, 0, 0))
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(text, flag=wx.ALL, border=12)
    banner.SetSizerAndFit(sizer)
    banner.CentreOnScreen()
    banner.Show(True)
    banner.Raise()
    return banner
