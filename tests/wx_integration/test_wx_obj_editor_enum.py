"""Tests for construct_editor.wx_widgets.wx_obj_view.WxObjEditor_Enum."""

import pytest


@pytest.mark.skip(reason="Requires a running wx.App — enable when wx tests are wired up")
def test_placeholder(wx_app_and_ui_sim) -> None:
    pass


# TODO: Tests to add:
#   - ComboBox is populated with enum label strings
#   - Selecting an entry updates get_new_obj()
