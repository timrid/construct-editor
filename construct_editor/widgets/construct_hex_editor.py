# -*- coding: utf-8 -*-
import io
import typing as t

import construct as cs
import wx

from construct_editor.helper.wrapper import EntryConstruct
from construct_editor.widgets.construct_editor import ConstructEditor
from construct_editor.widgets.hex_editor import (
    HexEditor,
    HexEditorBinaryData,
    HexEditorFormat,
)


class HexEditorPanel(wx.SplitterWindow):
    def __init__(self, parent):
        super().__init__(parent, style=wx.SP_LIVE_UPDATE)
        self.SetSashGravity(0.5)
        self.SetMinimumPaneSize(100)

        # Create HexEditor
        panel = wx.Panel(self, style=wx.BORDER_THEME)
        hsizer = wx.BoxSizer(wx.VERTICAL)
        self._name_txt = wx.StaticText(self, wx.ID_ANY)
        hsizer.Add(self._name_txt, 0, wx.ALL, 5)
        self.hex_editor = HexEditor(
            panel,
            b"",
            HexEditorFormat(width=16),
        )
        hsizer.Add(self.hex_editor, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(hsizer)
        self.Initialize(panel)

        self.sub_panel: t.Optional["HexEditorPanel"] = None

    def set_name(self, name: str):
        self._name_txt.SetLabelText(name)

    def clear_sub_panels(self):
        """Clears all sub-panels recursivly"""
        if self.sub_panel is not None:
            self.Unsplit(self.sub_panel)
            self.sub_panel.Destroy()
            self.sub_panel = None

    def create_sub_panel(self) -> "HexEditorPanel":
        """Create a new sub-panel"""
        if self.sub_panel is None:
            self.sub_panel = HexEditorPanel(self)
            self.SplitHorizontally(self.GetWindow1(), self.sub_panel)
            return self.sub_panel
        else:
            raise RuntimeError("sub-panel already created")


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
        self.hex_panel = HexEditorPanel(self)
        self.hex_panel.set_name("asdf")
        hsizer.Add(self.hex_panel, 0, wx.EXPAND | wx.ALL, 5)

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
        self.construct_editor = ConstructEditor(
            self,
            construct,
        )
        hsizer.Add(self.construct_editor, 1, wx.ALL | wx.EXPAND, 5)
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
        self.hex_panel.hex_editor.binary = val

    # Internals ###############################################################
    def _convert_binary_to_struct(self):
        """Convert binary to construct object"""
        if self._converting:
            return
        try:
            self._converting = True
            self.construct_editor.parse(
                self.hex_panel.hex_editor.binary, **self.contextkw
            )
        finally:
            self._converting = False

    def _convert_struct_to_binary(self):
        """Convert construct object to binary"""
        try:
            self._converting = True
            binary = self.construct_editor.build(**self.contextkw)
            self.hex_panel.hex_editor.binary = binary
        except Exception:
            pass  # ignore errors, because they are already shown in the gui
        finally:
            self._converting = False

    def _on_entry_selected(self, entry: EntryConstruct):
        self.Freeze()
        self.hex_panel.clear_sub_panels()
        self._show_byte_range(entry, None)
        self.Thaw()

    def _show_byte_range(
        self, entry: EntryConstruct, child_nested_stream_ctr: t.Optional[int]
    ) -> t.Tuple[HexEditorPanel, str]:
        """
        Show the Position in the binary data of the HexEditor.
        If nested streams are used, sub-HexEditors are created.
        """
        # Get GUI-Metadata. If not existing, nothing is shown.
        metadata = entry.obj_metadata
        if metadata is None:
            self.hex_panel.hex_editor.colorise(0, 0)
            return (self.hex_panel, "")

        nested_stream_ctr = metadata["nested_stream_ctr"]
        context = metadata["context"]
        if nested_stream_ctr == 0:
            # The root stream is used
            hex_pnl = self.hex_panel
        else:
            # A nested stream is used

            # Show position of parent entry in the parent stream
            if entry.parent is None:
                raise RuntimeError("parent can't be None in stream nesting")
            hex_pnl, parent_stream_name = self._show_byte_range(
                entry.parent, nested_stream_ctr
            )

            # The parent stream is different from the current -> create a new sub HexEditor
            if child_nested_stream_ctr != nested_stream_ctr:
                hex_pnl = hex_pnl.create_sub_panel()
                hex_pnl.set_name(parent_stream_name)

                stream: io.BinaryIO = context._io
                if not isinstance(stream, io.BytesIO):
                    raise RuntimeError("stream has to be io.BytesIO")
                hex_pnl.hex_editor.binary = stream.getvalue()

        # Show the byte range in the corresponding HexEditor
        start = metadata["byte_range"][0]
        end = metadata["byte_range"][1]
        hex_pnl.hex_editor.colorise(start, end, refresh=False)
        hex_pnl.hex_editor.scroll_to_idx(end - 1, refresh=False)
        hex_pnl.hex_editor.scroll_to_idx(start, refresh=False)
        hex_pnl.hex_editor.refresh()

        return hex_pnl, entry.name
