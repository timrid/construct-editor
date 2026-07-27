"""Shared pytest fixtures for wx integration tests.

All tests in this package require a running wx.App instance.
The session-scoped fixture below creates exactly one App for the entire
test session and tears it down afterwards.

tests/wx_integration/ and tests/core/ are run as two separate pytest
invocations (see ci.yml), so wx can safely be imported at module level here
without pulling it into tests/core/ runs.
"""

import typing as t

import pytest
import wx

from tests.wx_integration.wx_test_helpers import WxAppAndUiSim

_BANNER_TEXT = (
    "wx UI test in progress\n"
    "Simulated mouse/keyboard input is running for the test session.\n"
    "Avoid touching the mouse/keyboard until it finishes."
)


def show_input_warning_banner() -> wx.Frame:
    banner = wx.Frame(
        None,
        title="wx UI test in progress",
        style=wx.STAY_ON_TOP | wx.CAPTION | wx.FRAME_NO_TASKBAR,
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


@pytest.fixture(scope="session")
def wx_app_and_ui_sim() -> t.Generator[WxAppAndUiSim, None, None]:
    """Session-scoped wx.App + wx.UIActionSimulator (plus its advisory
    input-warning banner), required by all wx widget tests.

    Owns the actual setup/teardown for both, so the destroy order between
    them is explicit in one place: the banner is destroyed first, then the
    wx.App — see input_warning_banner.py.
    """
    app = wx.App(False)
    banner = show_input_warning_banner()
    simulator = wx.UIActionSimulator()
    try:
        yield WxAppAndUiSim(app=app, ui_simulator=simulator)
    finally:
        # Close the banner. That should be the last Top-Level-Window. When this is closed,
        # the wx.App will exit its MainLoop and return control to pytest.
        banner.Close()
        app.MainLoop()


@pytest.fixture
def wx_harness(wx_app_and_ui_sim: WxAppAndUiSim):
    """Function-scoped WxTestHarness (wx.App + a top-level wx.Frame + a
    wx.UIActionSimulator) used as the parent for tested widgets.

    The frame is created fresh for each test and destroyed afterwards to
    avoid state leakage.
    """
    from tests.wx_integration.wx_test_helpers import WxTestHarness

    with WxTestHarness.create(wx_app_and_ui_sim.app, wx_app_and_ui_sim.ui_simulator) as harness:
        yield harness
