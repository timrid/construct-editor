# -*- coding: utf-8 -*-
from typing import Any, Optional

import construct as cs
import wx

from construct_editor.widgets.construct_editor import ConstructEditor
from construct_editor.widgets.hex_editor import HexEditorGrid, OffsetFmt, TableFormat


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
        self.hex_editor = HexEditorGrid(
            self,
            binary,
            TableFormat(width=16, offsetfmt=OffsetFmt.Dez),
            on_binary_changed=lambda pos, len: self._convert_binary_to_struct(),
        )
        hsizer.Add(self.hex_editor, 0, wx.EXPAND | wx.ALL, 5)

        # add line
        hsizer.Add(wx.StaticLine(self, style=wx.LI_VERTICAL), 0, wx.EXPAND | wx.ALL, 5)

        # create ConstructEditor
        self.construct_editor = ConstructEditor(
            self,
            construct,
            on_obj_changed=self._convert_struct_to_binary,
            on_entry_selected=self._on_entry_selected,
        )
        hsizer.Add(self.construct_editor, 1, wx.ALL | wx.EXPAND, 5)

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
        self.construct_editor.parse(self.hex_editor.binary, **self.contextkw)

    def _convert_struct_to_binary(self):
        """ Convert construct object to binary """
        try:
            binary = self.construct_editor.build(**self.contextkw)
            self.hex_editor.binary = binary
        except Exception:
            pass  # ignore errors

    def _on_entry_selected(self, start: Optional[int], end: Optional[int]):
        if start is not None and end is not None:
            self.hex_editor.colorise(start, end, refresh=False)
            self.hex_editor.scroll_to_pos(end - 1, refresh=False)
            self.hex_editor.scroll_to_pos(start, refresh=False)
            self.hex_editor.refresh()
        else:
            self.hex_editor.colorise(0, 0)
