"""Tests for construct_editor.wx_widgets.wx_context_menu.

Covers WxContextMenu — the concrete wx.Menu implementation of the abstract
ContextMenu base class.
"""

import pytest


@pytest.mark.skip(reason="Requires a running wx.App — enable when wx tests are wired up")
def test_placeholder(wx_app_and_ui_sim) -> None:
    pass


# TODO: Tests to add:
#   - Menu can be instantiated without exceptions given a ConstructEditor stub
#   - Separator items are added as wx.ITEM_SEPARATOR entries
#   - Button items are added as wx.ITEM_NORMAL entries with correct labels
#   - Checkbox items reflect the initial checked state
#   - RadioGroup items create a radio group with the correct selected index
#   - Submenu items create a nested wx.Menu
#   - Clicking a button item invokes the provided callback

