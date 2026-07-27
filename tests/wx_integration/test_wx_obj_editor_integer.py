"""Tests for construct_editor.wx_widgets.wx_obj_view.WxObjEditor_Integer."""

import pytest


@pytest.mark.skip(reason="Requires a running wx.App — enable when wx tests are wired up")
def test_placeholder(wx_app_and_ui_sim) -> None:
    pass


# TODO: Tests to add:
#   - Accepts valid integer strings in Dec and Hex format
#   - get_new_obj() returns the parsed integer
#   - Invalid input does not raise unhandled exceptions
