# -*- coding: utf-8 -*-
import io
import typing as t

import construct as cs
import wx

from construct_editor.constr_editor.wrapper import EntryConstruct, StreamInfo
from construct_editor.constr_editor.construct_editor import ConstructEditor
from construct_editor.hex_editor.stackable_hex_editor import StackableHexEditorPanel


class ConstructHexEditor(wx.Panel):
    def __init__(
        self,
        parent,
        construct: cs.Construct,
        contextkw: dict = {},
        binary: bytes = b"",
    ):
        super().__init__(parent)

        self._contextkw = contextkw

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self._init_gui_hex_editor_splitter(hsizer, binary)
        self._init_gui_hex_visibility(hsizer)
        self._init_gui_construct_editor(hsizer, construct)

        self._converting = False
        self._hex_editor_visible = True

        # show data in construct editor
        self.refresh()

        self.SetSizer(hsizer)
        self.Layout()

    def _init_gui_hex_editor_splitter(self, hsizer: wx.BoxSizer, binary: bytes):
        # Create Splitter for showing one or multiple HexEditors
        self.hex_panel = StackableHexEditorPanel(self, "")
        hsizer.Add(self.hex_panel, 0, wx.EXPAND, 0)

        # Init Root HexEditor
        self.hex_panel.hex_editor.binary = binary
        self.hex_panel.hex_editor.on_binary_changed.append(
            lambda _: self._convert_binary_to_struct()
        )

    def _init_gui_hex_visibility(self, hsizer: wx.BoxSizer):
        self.toggle_hex_visibility_btn = wx.Button(
            self, wx.ID_ANY, "«", size=wx.Size(12, -1)
        )
        hsizer.Add(self.toggle_hex_visibility_btn, 0, wx.EXPAND | wx.ALL, 0)
        self.toggle_hex_visibility_btn.Bind(
            wx.EVT_BUTTON, lambda evt: self.toggle_hex_visibility()
        )

    def _init_gui_construct_editor(self, hsizer: wx.BoxSizer, construct: cs.Construct):
        self.construct_editor: ConstructEditor = ConstructEditor(
            self,
            construct,
        )
        hsizer.Add(self.construct_editor, 1, wx.EXPAND, 0)
        self.construct_editor.on_root_obj_changed.append(
            lambda _: self._convert_struct_to_binary()
        )
        self.construct_editor.on_entry_selected.append(self._on_entry_selected)

    def refresh(self):
        """Refresh the content of the construct view"""
        self.Freeze()
        self.hex_panel.hex_editor.refresh()
        self._convert_binary_to_struct()
        self.Thaw()

    def toggle_hex_visibility(self):
        """Toggle the visibility of the HexEditor"""
        if self._hex_editor_visible:
            self.hex_panel.HideWithEffect(wx.SHOW_EFFECT_ROLL_TO_LEFT)
            self.toggle_hex_visibility_btn.SetLabelText("»")
            self._hex_editor_visible = False
        else:
            self.hex_panel.ShowWithEffect(wx.SHOW_EFFECT_ROLL_TO_RIGHT)
            self.toggle_hex_visibility_btn.SetLabelText("«")
            self._hex_editor_visible = True
        self.Freeze()
        self.Layout()
        self.Refresh()
        self.Thaw()

    # Property: construct #####################################################
    @property
    def construct(self) -> cs.Construct:
        """construct used for parsing"""
        return self.construct_editor.construct

    @construct.setter
    def construct(self, val: cs.Construct):
        self.construct_editor.construct = val

    # Property: contextkw #####################################################
    @property
    def contextkw(self) -> dict:
        """contextkw used for parsing the construct"""
        return self._contextkw

    @contextkw.setter
    def contextkw(self, val: dict):
        self._contextkw = val

    # Property: root_obj ######################################################
    @property
    def root_obj(self) -> t.Any:
        return self.construct_editor.root_obj

    # Property: binary ########################################################
    @property
    def binary(self) -> bytes:
        return self.hex_panel.hex_editor.binary

    @binary.setter
    def binary(self, val: bytes):
        self.hex_panel.clear_sub_panels()
        self.hex_panel.hex_editor.binary = val

    # Internals ###############################################################
    def _convert_binary_to_struct(self):
        """Convert binary to construct object"""
        if self._converting:
            return

        def on_done(obj_or_ex: t.Union[t.Any, Exception]):
            self._converting = False

        self._converting = True
        self.construct_editor.parse(
            self.hex_panel.hex_editor.binary, self.contextkw, on_done
        )

    def _convert_struct_to_binary(self):
        """Convert construct object to binary"""

        def on_done(byts_or_ex: t.Union[bytes, Exception]):
            if isinstance(byts_or_ex, Exception):
                pass  # ignore errors, because they are already shown in the gui
            else:
                self.hex_panel.hex_editor.binary = byts_or_ex
            self._converting = False

        self._converting = True
        self.construct_editor.build(self.contextkw, on_done)

    def _on_entry_selected(self, entry: EntryConstruct):
        try:
            self.Freeze()
            self.hex_panel.clear_sub_panels()
            # self._show_byte_range(entry, None)
            stream_infos = entry.get_stream_infos()
            self._show_stream_infos(stream_infos)
        finally:
            self.Thaw()

    def _show_stream_infos(self, stream_infos: t.List[StreamInfo]):
        hex_pnl = self.hex_panel
        for idx, stream_info in enumerate(stream_infos):
            if idx != 0:  # dont create Sub-Panel for the root stream
                hex_pnl = hex_pnl.create_sub_panel(".".join(stream_info.path))
                hex_pnl.hex_editor.binary = stream_info.stream.getvalue()

            start = stream_info.byte_range[0]
            end = stream_info.byte_range[1]

            # Show the byte range in the corresponding HexEditor
            hex_pnl.hex_editor.colorise(start, end, refresh=False)
            hex_pnl.hex_editor.scroll_to_idx(end - 1, refresh=False)
            hex_pnl.hex_editor.scroll_to_idx(start, refresh=False)
            hex_pnl.hex_editor.refresh()
