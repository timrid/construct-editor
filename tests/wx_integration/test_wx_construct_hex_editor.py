"""Tests for construct_editor.wx_widgets.wx_construct_hex_editor.WxConstructHexEditor.

Covers the composite WxConstructHexEditor widget.
"""

import pytest


@pytest.mark.skip(reason="Requires a running wx.App — enable when wx tests are wired up")
def test_placeholder(wx_app_and_ui_sim) -> None:
    pass


# TODO: Tests to add:
#   - Widget can be constructed and shown without errors
#   - Setting binary data triggers a parse pass
#   - Editing a struct field via the construct editor updates the hex view
#   - toggle_hex_visibility() hides/shows the hex editor pane
#   - round-trip: parse bytes -> build -> compare to original bytes

