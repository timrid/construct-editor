"""Tests for construct_editor.wx_widgets.wx_exception_dialog.WxExceptionDialog."""

import pytest


@pytest.mark.skip(reason="Requires a running wx.App — enable when wx tests are wired up")
def test_placeholder(wx_app_and_ui_sim) -> None:
    pass


# TODO: Tests to add:
#   - Dialog can be instantiated with an ExceptionInfo without raising
#   - Exception type name is shown in the dialog text
#   - Traceback text is non-empty
#   - Dialog can be closed without errors


