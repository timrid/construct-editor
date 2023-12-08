# -*- coding: utf-8 -*-
import typing as t

import construct as cs
import wx

from construct_editor.core.entries import EntryConstruct, StreamInfo
from construct_editor.core.model import ConstructEditorModel
from construct_editor.wx_widgets.wx_construct_editor import WxConstructEditor
from construct_editor.wx_widgets.wx_hex_editor import HexEditorFormat, WxHexEditor


class HexEditorPanel(wx.SplitterWindow):
    def __init__(
        self, parent, name: str, read_only: bool = False, bitwiese: bool = False
    ):
        super().__init__(parent, style=wx.SP_LIVE_UPDATE)
        self.SetSashGravity(0.5)

        panel = wx.Panel(self)
        vsizer = wx.BoxSizer(wx.VERTICAL)

        # Create Name if available
        if name != "":
            line = wx.StaticLine(panel, style=wx.LI_HORIZONTAL)
            vsizer.Add(line, 0, wx.EXPAND)
            self._name_txt = wx.StaticText(panel, wx.ID_ANY)
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
        self.hex_editor: WxHexEditor = WxHexEditor(
            panel,
            b"",
            HexEditorFormat(width=16),
            read_only=read_only,
            bitwiese=bitwiese,
        )
        vsizer.Add(self.hex_editor, 1)
        panel.SetSizer(vsizer)

        self.Initialize(panel)

        self.sub_panel: t.Optional["HexEditorPanel"] = None

    def clear_sub_panels(self):
        """Clears all sub-panels recursivly"""
        if self.sub_panel is not None:
            self.Unsplit(self.sub_panel)
            self.sub_panel.Destroy()
            self.sub_panel = None

    def create_sub_panel(self, name: str, bitwise: bool) -> "HexEditorPanel":
        """Create a new sub-panel"""
        if self.sub_panel is None:
            self.sub_panel = HexEditorPanel(
                self, name, read_only=True, bitwiese=bitwise
            )
            self.SplitHorizontally(self.GetWindow1(), self.sub_panel)
            return self.sub_panel
        else:
            raise RuntimeError("sub-panel already created")


class WxConstructHexEditor(wx.Panel):
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
        self.hex_panel: HexEditorPanel = HexEditorPanel(self, "")
        hsizer.Add(self.hex_panel, 0, wx.EXPAND, 0)

        # Init Root HexEditor
        self.hex_panel.hex_editor.binary = binary
        self.hex_panel.hex_editor.on_binary_changed.append(
            lambda _: self._convert_binary_to_struct()
        )

    def _init_gui_hex_visibility(self, hsizer: wx.BoxSizer):
        self.toggle_hex_visibility_btn = wx.Button(
            self, wx.ID_ANY, "«", style=wx.BU_EXACTFIT
        )
        hsizer.Add(self.toggle_hex_visibility_btn, 0, wx.EXPAND | wx.ALL, 0)
        self.toggle_hex_visibility_btn.Bind(
            wx.EVT_BUTTON, lambda evt: self.toggle_hex_visibility()
        )

    def _init_gui_construct_editor(self, hsizer: wx.BoxSizer, construct: cs.Construct):
        self.construct_editor: WxConstructEditor = WxConstructEditor(
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

    def change_construct(self, constr: cs.Construct) -> None:
        """
        Change the construct format, that is used for building/parsing.
        """
        self.construct_editor.change_construct(constr)

    def change_contextkw(self, contextkw: dict):
        """
        Change the contextkw used for building/parsing.
        """
        self._contextkw = contextkw

    def change_binary(self, binary: bytes):
        """
        Change the binary data, that should be displayed.
        """
        self.hex_panel.clear_sub_panels()
        self.hex_panel.hex_editor.binary = binary

    @property
    def construct(self) -> cs.Construct:
        """
        Construct that is used for displaying.
        """
        return self.construct_editor.construct

    @construct.setter
    def construct(self, constr: cs.Construct):
        self.construct_editor.construct = constr

    @property
    def contextkw(self) -> dict:
        """
        Context used for building/parsing.
        """
        return self._contextkw

    @contextkw.setter
    def contextkw(self, contextkw: dict):
        self.change_contextkw(contextkw)

    @property
    def binary(self) -> bytes:
        """
        Binary data, that should be displayed.
        """
        return self.hex_panel.hex_editor.binary

    @binary.setter
    def binary(self, binary: bytes):
        self.change_binary(binary)

    @property
    def hide_protected(self) -> bool:
        """
        Hide protected members.
        A protected member starts with an undescore (_)
        """
        return self.construct_editor.hide_protected

    @hide_protected.setter
    def hide_protected(self, hide_protected: bool):
        self.construct_editor.hide_protected = hide_protected

    @property
    def root_obj(self) -> t.Any:
        """
        Root object that is displayed
        """
        return self.construct_editor.root_obj

    @property
    def model(self) -> ConstructEditorModel:
        """
        Model with the displayed data.
        """
        return self.construct_editor.model

    # Internals ###############################################################
    def _convert_binary_to_struct(self):
        """Convert binary to construct object"""
        if self._converting:
            return
        try:
            self._converting = True
            self.Freeze()
            self.construct_editor.parse(
                self.hex_panel.hex_editor.binary, **self._contextkw
            )
        finally:
            self.Thaw()
            self._converting = False

    def _convert_struct_to_binary(self):
        """Convert construct object to binary"""
        try:
            self._converting = True
            self.Freeze()
            binary = self.construct_editor.build(**self._contextkw)
            self.hex_panel.hex_editor.binary = binary
            self._on_entry_selected(self.construct_editor.get_selected_entry())
        except Exception:
            pass  # ignore errors, because they are already shown in the gui
        finally:
            self.Thaw()
            self._converting = False

    def _on_entry_selected(self, entry: t.Optional[EntryConstruct]):
        try:
            self.Freeze()
            self.hex_panel.clear_sub_panels()
            if entry is not None:
                stream_infos = entry.get_stream_infos()
                self._show_stream_infos(stream_infos)
        finally:
            self.Thaw()

    def _show_stream_infos(self, stream_infos: t.List[StreamInfo]):
        hex_pnl = self.hex_panel
        panel_stream_mapping: t.List[t.Tuple[HexEditorPanel, StreamInfo]] = []

        # Create all Sub-Panels
        for idx, stream_info in enumerate(stream_infos):
            if idx != 0:  # dont create Sub-Panel for the root stream
                hex_pnl = hex_pnl.create_sub_panel(
                    stream_info.path_str, stream_info.bitstream
                )
                hex_pnl.hex_editor.binary = stream_info.stream.getvalue()

            panel_stream_mapping.append((hex_pnl, stream_info))

        # Mark to correct bytes in the stream.
        # Can only be made when alls sub-panels are created. Otherwise "scroll_to_idx"
        # does not work properly because the size of the HexEditorPanel may change.
        for hex_pnl, stream_info in panel_stream_mapping:
            start = stream_info.byte_range[0]
            end = stream_info.byte_range[1]

            # Show the byte range in the corresponding HexEditor
            hex_pnl.hex_editor.colorise(start, end, refresh=False)
            hex_pnl.hex_editor.scroll_to_idx(end - 1, refresh=False)
            hex_pnl.hex_editor.scroll_to_idx(start, refresh=False)
            hex_pnl.hex_editor.refresh()
