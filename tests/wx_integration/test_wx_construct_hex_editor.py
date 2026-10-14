"""Integration tests for the composite Construct and hex editor."""

# pyright: reportPrivateUsage=false

import pytest
import wx

from construct_editor.core.model import ConstructEditorColumn
from construct_editor.gallery.test_array_with_bit_struct import gallery_item
from construct_editor.wx_widgets.wx_construct_hex_editor import WxConstructHexEditor
from tests.wx_integration.wx_test_helpers import (
    WxTestHarness,
    construct_editor_cell_screen_rect,
)


@pytest.mark.parametrize("collapse_flags_first", [False, True], ids=["expanded-flags", "collapsed-flags"])
def test_editing_flag_preserves_collapsed_sibling(wx_harness: WxTestHarness, collapse_flags_first: bool) -> None:
    panel = WxConstructHexEditor(wx_harness.frame, gallery_item.construct, binary=gallery_item.example_binarys["Sample"])
    editor = panel.construct_editor
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(panel, 1, wx.EXPAND)
    wx_harness.frame.SetSizer(sizer)
    wx_harness.frame.SetSize(wx.Size(1200, 800))
    wx_harness.frame.Layout()
    editor.expand_all()
    wx_harness.wait_ms(100)

    model = editor._model
    root = model.root_entry
    assert root is not None
    first, second = model.get_children(root)
    first_flags = model.get_children(first)[0]
    second_flags = model.get_children(second)[0]
    flag = model.get_children(second_flags)[0]
    first_item = model.entry_to_dvc_item(first)
    assert editor._dvc.IsExpanded(first_item)
    assert editor._dvc.IsExpanded(model.entry_to_dvc_item(first_flags))
    assert editor._dvc.IsExpanded(model.entry_to_dvc_item(second_flags))

    if collapse_flags_first:
        editor.collapse_entry(first_flags)
    editor.collapse_entry(first)
    wx_harness.wait_ms(100)
    assert not editor._dvc.IsExpanded(first_item)
    assert first_flags.row_expanded is not collapse_flags_first

    rect = construct_editor_cell_screen_rect(editor, flag, ConstructEditorColumn.Value)
    checkbox_size = wx.RendererNative.Get().GetCheckBoxSize(editor._dvc)
    wx_harness.move_mouse_to(wx.Point(rect.x + checkbox_size.width // 2, rect.y + rect.height // 2))
    wx_harness.click()

    assert editor.get_root_obj()[1].flags.flag_1 == 1
    assert editor.get_root_obj()[0].flags.flag_1 == 0
    assert panel.hex_panel.hex_editor.binary == b"\x00\x01"
    assert not editor._dvc.IsExpanded(first_item)
    assert editor._dvc.IsExpanded(model.entry_to_dvc_item(second))
    assert editor._dvc.IsExpanded(model.entry_to_dvc_item(second_flags))

    assert first.row_expanded is False
    assert first_flags.row_expanded is not collapse_flags_first
    editor.expand_entry(first)
    assert editor._dvc.IsExpanded(model.entry_to_dvc_item(first_flags)) is not collapse_flags_first
