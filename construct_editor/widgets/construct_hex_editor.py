# -*- coding: utf-8 -*-
from typing import Any, Optional

import construct as cs
import wx

from construct_editor.widgets.construct_editor import ConstructEditor
from construct_editor.widgets.hex_editor import (
    HexEditor,
    HexEditorFormat,
    HexEditorBinaryData,
)
from construct_editor.helper.wrapper import (
    EntryConstruct,
)


class ConstructHexEditor(wx.Panel):
    def __init__(
        self,
        parent,
        construct: cs.Construct,
        contextkw: dict = {},
        binary: Optional[bytes] = None,
    ):
        super().__init__(parent)

        self._contextkw = contextkw

        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        # create HexEditor
        self.hex_editor = HexEditor(
            self,
            binary,
            HexEditorFormat(width=16),
        )
        hsizer.Add(self.hex_editor, 0, wx.EXPAND | wx.ALL, 5)
        self.hex_editor.on_binary_changed.append(
            lambda _: self._convert_binary_to_struct()
        )

        # add button as line to toggle the visibility of the HexEditor
        self.toggle_hex_visibility_btn = wx.Button(
            self, wx.ID_ANY, "«", size=wx.Size(12, -1)
        )  # »
        hsizer.Add(self.toggle_hex_visibility_btn, 0, wx.EXPAND | wx.ALL, 0)
        self.toggle_hex_visibility_btn.Bind(
            wx.EVT_BUTTON, lambda evt: self.toggle_hex_visibility()
        )

        # create ConstructEditor
        self.construct_editor = ConstructEditor(
            self,
            construct,
        )
        hsizer.Add(self.construct_editor, 1, wx.ALL | wx.EXPAND, 5)
        self.construct_editor.on_root_obj_changed.append(
            lambda _: self._convert_struct_to_binary()
        )
        self.construct_editor.on_entry_selected.append(self._on_entry_selected)

        self._converting = False
        self._hex_editor_visible = True

        # show data in construct editor
        self.refresh()

        self.SetSizer(hsizer)
        self.Layout()

    def refresh(self):
        """ Refresh the content of the construct view """
        self.Freeze()
        self.hex_editor.refresh()
        self._convert_binary_to_struct()
        self.Thaw()

    def toggle_hex_visibility(self):
        """ Toggle the visibility of the HexEditor """
        if self._hex_editor_visible:
            self.hex_editor.HideWithEffect(wx.SHOW_EFFECT_ROLL_TO_LEFT)
            self.toggle_hex_visibility_btn.SetLabelText("»")
            self._hex_editor_visible = False
        else:
            self.hex_editor.ShowWithEffect(wx.SHOW_EFFECT_ROLL_TO_RIGHT)
            self.toggle_hex_visibility_btn.SetLabelText("«")
            self._hex_editor_visible = True
        self.Freeze()
        self.Layout()
        self.Refresh()
        self.Thaw()

    # Property: construct #####################################################
    @property
    def construct(self) -> cs.Construct:
        """ construct used for parsing """
        return self.construct_editor.construct

    @construct.setter
    def construct(self, val: cs.Construct):
        self.construct_editor.construct = val

    # Property: contextkw #####################################################
    @property
    def contextkw(self) -> dict:
        """ contextkw used for parsing the construct """
        return self._contextkw

    @contextkw.setter
    def contextkw(self, val: dict):
        self._contextkw = val

    # Property: root_obj ######################################################
    @property
    def root_obj(self) -> Any:
        return self.construct_editor.root_obj

    # Property: binary ########################################################
    @property
    def binary(self) -> bytes:
        return self.hex_editor.binary

    @binary.setter
    def binary(self, val: bytes):
        self.hex_editor.binary = val

    # Internals ###############################################################
    def _convert_binary_to_struct(self):
        """ Convert binary to construct object """
        if self._converting:
            return
        try:
            self._converting = True
            self.construct_editor.parse(self.hex_editor.binary, **self.contextkw)
        finally:
            self._converting = False

    def _convert_struct_to_binary(self):
        """ Convert construct object to binary """
        try:
            self._converting = True
            binary = self.construct_editor.build(**self.contextkw)
            self.hex_editor.binary = binary
        except Exception:
            pass  # ignore errors, because they are already shown in the gui
        finally:
            self._converting = False

    def _on_entry_selected(self, entry: EntryConstruct):
        metadata = entry.obj_metadata
        if metadata is not None:
            self.hex_editor.colorise(metadata.offset_start, metadata.offset_end, refresh=False)
            self.hex_editor.scroll_to_idx(metadata.offset_end - 1, refresh=False)
            self.hex_editor.scroll_to_idx(metadata.offset_start, refresh=False)
            self.hex_editor.refresh()
        else:
            self.hex_editor.colorise(0, 0)
