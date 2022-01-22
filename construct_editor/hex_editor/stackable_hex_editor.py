# -*- coding: utf-8 -*-
import typing as t

import wx

from construct_editor.hex_editor.hex_editor import (
    HexEditor,
    HexEditorBinaryData,
    HexEditorFormat,
)


class StackableHexEditorPanel(wx.SplitterWindow):
    def __init__(self, parent, name: str, read_only: bool = False):
        super().__init__(parent, style=wx.SP_LIVE_UPDATE)
        self.SetSashGravity(0.5)

        panel = wx.Panel(self)
        vsizer = wx.BoxSizer(wx.VERTICAL)

        # Create Name if available
        if name != "":
            line = wx.StaticLine(panel, style=wx.LI_HORIZONTAL)
            vsizer.Add(line, 0, wx.EXPAND)
            self._name_txt = wx.StaticText(self, wx.ID_ANY)
            self._name_txt.SetFont(
                wx.Font(
                    10,
                    wx.FONTFAMILY_DEFAULT,
                    wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_BOLD,
                    underline=True,
                )
            )
            vsizer.Add(self._name_txt, 0, wx.ALIGN_CENTER | wx.ALL, 5)
            self._name_txt.SetLabelText(name)

        # Create HexEditor
        self.hex_editor = HexEditor(
            panel,
            b"",
            HexEditorFormat(width=16),
            read_only=read_only,
        )
        vsizer.Add(self.hex_editor, 1)
        panel.SetSizer(vsizer)

        self.Initialize(panel)

        self.sub_panel: t.Optional["StackableHexEditorPanel"] = None

    def clear_sub_panels(self):
        """Clears all sub-panels recursivly"""
        if self.sub_panel is not None:
            self.Unsplit(self.sub_panel)
            self.sub_panel.Destroy()
            self.sub_panel = None

    def create_sub_panel(self, name: str) -> "StackableHexEditorPanel":
        """Create a new sub-panel"""
        if self.sub_panel is None:
            self.sub_panel = StackableHexEditorPanel(self, name, read_only=True)
            self.SplitHorizontally(self.GetWindow1(), self.sub_panel)
            return self.sub_panel
        else:
            raise RuntimeError("sub-panel already created")
