"""Tests for construct_editor.wx_widgets.wx_obj_view.WxObjEditor_String."""

import pytest


@pytest.mark.skip(reason="Requires a running wx.App — enable when wx tests are wired up")
def test_placeholder(wx_app_and_ui_sim) -> None:
    pass


# TODO: Tests to add:
#   - Displays the initial string value
#   - get_new_obj() returns the edited string
