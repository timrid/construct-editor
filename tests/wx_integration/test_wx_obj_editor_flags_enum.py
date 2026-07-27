"""Tests for construct_editor.wx_widgets.wx_obj_view.WxObjEditor_FlagsEnum (ComboCtrl with popup checklist)."""

import pytest


@pytest.mark.skip(reason="Requires a running wx.App — enable when wx tests are wired up")
def test_placeholder(wx_app_and_ui_sim) -> None:
    pass


# TODO: Tests to add:
#   - Popup lists all flag names
#   - Checked flags are reflected in get_new_obj()
