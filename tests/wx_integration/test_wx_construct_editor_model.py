"""Tests for construct_editor.wx_widgets.wx_construct_editor.WxConstructEditorModel.

WxConstructEditorModel is the wx DataView model adapter.
"""

import pytest


@pytest.mark.skip(reason="Requires a running wx.App — enable when wx tests are wired up")
def test_placeholder(wx_app_and_ui_sim) -> None:
    pass


# TODO: Instantiate WxConstructEditorModel with a simple construct and verify:
#   - GetChildren() returns the correct number of rows for a flat Struct
#   - IsContainer() returns True for Struct entries, False for leaf entries
#   - GetValue() returns expected strings for Name, Type, Value columns
#   - SetValue() triggers on_value_changed callback
