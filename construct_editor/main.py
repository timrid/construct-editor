from __future__ import annotations

import dataclasses
import sys
import typing as t

from pathlib import Path
import construct as cs
import wx
from wx.lib.embeddedimage import PyEmbeddedImage

import construct_editor.gallery.example_pe32coff
import construct_editor.gallery.example_ipstack
import construct_editor.gallery.test_bytes_greedybytes
import construct_editor.gallery.test_array
import construct_editor.gallery.test_greedyrange
import construct_editor.gallery.test_bitwise
import construct_editor.gallery.test_bits_swapped_bitwise
import construct_editor.gallery.test_renamed
import construct_editor.gallery.test_select
import construct_editor.gallery.test_select_complex
import construct_editor.gallery.test_ifthenelse
import construct_editor.gallery.test_ifthenelse_nested_switch
import construct_editor.gallery.test_switch
import construct_editor.gallery.test_switch_dataclass
import construct_editor.gallery.test_dataclass_struct
import construct_editor.gallery.test_dataclass_bit_struct
import construct_editor.gallery.test_flag
import construct_editor.gallery.test_enum
import construct_editor.gallery.test_flagsenum
import construct_editor.gallery.test_tenum
import construct_editor.gallery.test_tflagsenum
import construct_editor.gallery.test_const
import construct_editor.gallery.test_computed
import construct_editor.gallery.test_focusedseq
import construct_editor.gallery.test_timestamp
import construct_editor.gallery.test_padded
import construct_editor.gallery.test_aligned
import construct_editor.gallery.test_pointer_peek_seek_tell
import construct_editor.gallery.test_pass
import construct_editor.gallery.test_fixedsized
import construct_editor.gallery.test_nullstripped
import construct_editor.gallery.test_nullterminated
import construct_editor.gallery.test_checksum
import construct_editor.gallery.test_compressed
import construct_editor.gallery.test_stringencodded
import construct_editor.gallery.example_cmd_resp
from construct_editor.widgets.construct_hex_editor import ConstructHexEditor


class ConstructGalleryFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.SetTitle("Construct Gallery")
        self.SetSize(1600, 1000)
        self.SetIcon(icon.GetIcon())
        self.Center()

        self.main_panel = ConstructGallery(self)

        self.status_bar: wx.StatusBar = self.CreateStatusBar()


class ConstructGallery(wx.Panel):
    def __init__(self, parent: ConstructGalleryFrame):
        super().__init__(parent)

        # Define all galleries ############################################
        self.construct_gallery = {
            "################ EXAMPLES ################": None,
            "Example: pe32coff": construct_editor.gallery.example_pe32coff.gallery_item,
            "Example: ipstack": construct_editor.gallery.example_ipstack.gallery_item,
            "Example: Cmd/Resp": construct_editor.gallery.example_cmd_resp.gallery_item,
            "################ TESTS ####################": None,
            # "## bytes and bits ################": None,
            "Test: Bytes/GreedyBytes": construct_editor.gallery.test_bytes_greedybytes.gallery_item,
            # "## integers and floats ###########": None,
            # "Test: FormatField (TODO)": None,
            # "Test: BytesInteger (TODO)": None,
            # "Test: BitsInteger (TODO)": None,
            "Test: Bitwiese": construct_editor.gallery.test_bitwise.gallery_item,
            "Test: BitsSwapped/Bitwiese": construct_editor.gallery.test_bits_swapped_bitwise.gallery_item,
            "## strings #######################": None,
            "Test: StringEncoded": construct_editor.gallery.test_stringencodded.gallery_item,
            "## mappings ######################": None,
            "Test: Flag": construct_editor.gallery.test_flag.gallery_item,
            "Test: Enum": construct_editor.gallery.test_enum.gallery_item,
            "Test: FlagsEnum": construct_editor.gallery.test_flagsenum.gallery_item,
            "Test: TEnum": construct_editor.gallery.test_tenum.gallery_item,
            "Test: TFlagsEnum": construct_editor.gallery.test_tflagsenum.gallery_item,
            # "Test: Mapping (TODO)": None,
            "## structures and sequences ######": None,
            # "Test: Struct (TODO)": None,
            # "Test: Sequence (TODO)": None,
            "Test: DataclassStruct": construct_editor.gallery.test_dataclass_struct.gallery_item,
            "Test: DataclassBitStruct": construct_editor.gallery.test_dataclass_bit_struct.gallery_item,
            "## arrays ranges and repeaters ######": None,
            "Test: Array": construct_editor.gallery.test_array.gallery_item,
            "Test: GreedyRange": construct_editor.gallery.test_greedyrange.gallery_item,
            # "Test: RepeatUntil (TODO)": None,
            "## specials ##########################": None,
            "Test: Renamed": construct_editor.gallery.test_renamed.gallery_item,
            "## miscellaneous ##########################": None,
            "Test: Const": construct_editor.gallery.test_const.gallery_item,
            "Test: Computed": construct_editor.gallery.test_computed.gallery_item,
            # "Test: Index (TODO)": None,
            # "Test: Rebuild (TODO)": None,
            # "Test: Default (TODO)": None,
            # "Test: Check (TODO)": None,
            # "Test: Error (TODO)": None,
            "Test: FocusedSeq": construct_editor.gallery.test_focusedseq.gallery_item,
            # "Test: Pickled (TODO)": None,
            # "Test: Numpy (TODO)": None,
            # "Test: NamedTuple (TODO)": None,
            "Test: TimestampAdapter": construct_editor.gallery.test_timestamp.gallery_item,
            # "Test: Hex (TODO)": None,
            # "Test: HexDump (TODO)": None,
            "## conditional ##########################": None,
            # "Test: Union (TODO)": None,
            "Test: Select": construct_editor.gallery.test_select.gallery_item,
            "Test: Select (Complex)": construct_editor.gallery.test_select_complex.gallery_item,
            "Test: IfThenElse": construct_editor.gallery.test_ifthenelse.gallery_item,
            "Test: IfThenElse (Nested Switch)": construct_editor.gallery.test_ifthenelse_nested_switch.gallery_item,
            "Test: Switch": construct_editor.gallery.test_switch.gallery_item,
            "Test: Switch (Dataclass)": construct_editor.gallery.test_switch_dataclass.gallery_item,
            # "Test: StopIf (TODO)": None,
            "## alignment and padding ##########################": None,
            "Test: Padded": construct_editor.gallery.test_padded.gallery_item,
            "Test: Aligned": construct_editor.gallery.test_aligned.gallery_item,
            "## stream manipulation ##########################": None,
            "Test: Pointer/Peek/Seek/Tell": construct_editor.gallery.test_pointer_peek_seek_tell.gallery_item,
            "Test: Pass": construct_editor.gallery.test_pass.gallery_item,
            # "Test: Terminated (TODO)": None,
            "## tunneling and byte/bit swapping ##########################": None,
            # "Test: RawCopy (TODO)": None,
            # "Test: Prefixed (TODO)": None,
            "Test: FixedSized": construct_editor.gallery.test_fixedsized.gallery_item,
            "Test: NullTerminated": construct_editor.gallery.test_nullterminated.gallery_item,
            "Test: NullStripped": construct_editor.gallery.test_nullstripped.gallery_item,
            # "Test: RestreamData (TODO)": None,
            # "Test: Transformed (TODO)": None,
            # "Test: Restreamed (TODO)": None,
            # "Test: ProcessXor (TODO)": None,
            # "Test: ProcessRotateLeft (TODO)": None,
            "Test: Checksum": construct_editor.gallery.test_checksum.gallery_item,
            "Test: Compressed": construct_editor.gallery.test_compressed.gallery_item,
            # "Test: CompressedLZ4 (TODO)": None,
            # "Test: Rebuffered (TODO)": None,
            # "## lazy equivalents ##########################": None,
            # "Test: Lazy (TODO)": None,
            # "Test: LazyStruct (TODO)": None,
            # "Test: LazyArray (TODO)": None,
            # "Test: LazyBound (TODO)": None,
            # "## adapters and validators ##########################": None,
            # "Test: ExprAdapter (TODO)": None,
            # "Test: ExprSymmetricAdapter (TODO)": None,
            # "Test: ExprValidator (TODO)": None,
            # "Test: Slicing (TODO)": None,
            # "Test: Indexing (TODO)": None,
        }
        self.gallery_selection = 1
        default_gallery = list(self.construct_gallery.keys())[self.gallery_selection]
        default_gallery_item = self.construct_gallery[default_gallery]

        # Define GUI elements #############################################
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)

        # gallery selctor
        self.gallery_selector_lbx = wx.ListBox(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            list(self.construct_gallery.keys()),
            0,
            name="gallery_selector",
        )
        self.gallery_selector_lbx.SetStringSelection(default_gallery)
        vsizer.Add(self.gallery_selector_lbx, 1, wx.ALL, 1)

        # reload btn
        self.reload_btn = wx.Button(
            self, wx.ID_ANY, "Reload", wx.DefaultPosition, wx.DefaultSize, 0
        )
        vsizer.Add(self.reload_btn, 0, wx.ALL | wx.EXPAND, 1)

        # line
        vsizer.Add(wx.StaticLine(self), 0, wx.TOP | wx.BOTTOM | wx.EXPAND, 5)

        # clear binary
        self.clear_binary_btn = wx.Button(
            self, wx.ID_ANY, "Clear Binary", wx.DefaultPosition, wx.DefaultSize, 0
        )
        vsizer.Add(self.clear_binary_btn, 0, wx.ALL | wx.EXPAND, 1)

        # example selctor
        self.example_selector_lbx = wx.ListBox(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(-1, 100),
            list(default_gallery_item.example_binarys.keys()),
            0,
            name="gallery_selector",
        )
        if len(default_gallery_item.example_binarys) > 0:
            self.example_selector_lbx.SetStringSelection(
                list(default_gallery_item.example_binarys.keys())[0]
            )
        vsizer.Add(self.example_selector_lbx, 0, wx.ALL | wx.EXPAND, 1)

        # load binary from file
        self.load_binary_file_btn = wx.Button(
            self,
            wx.ID_ANY,
            "Load Binary from File",
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        vsizer.Add(self.load_binary_file_btn, 0, wx.ALL | wx.EXPAND, 1)

        self.sizer.Add(vsizer, 0, wx.ALL | wx.EXPAND, 0)

        self.sizer.Add(
            wx.StaticLine(self, style=wx.LI_VERTICAL),
            0,
            wx.LEFT | wx.RIGHT | wx.EXPAND,
            5,
        )

        # construct hex editor
        self.construct_hex_editor = ConstructHexEditor(
            self,
            construct=default_gallery_item.construct,
            contextkw=default_gallery_item.contextkw,
        )
        self.construct_hex_editor.construct_editor.expand_all()
        self.sizer.Add(self.construct_hex_editor, 1, wx.ALL | wx.EXPAND, 0)

        self.SetSizer(self.sizer)

        # Connect Events ##################################################
        self.gallery_selector_lbx.Bind(
            wx.EVT_LISTBOX, self.on_gallery_selection_changed
        )
        self.reload_btn.Bind(wx.EVT_BUTTON, self.on_gallery_selection_changed)
        self.clear_binary_btn.Bind(wx.EVT_BUTTON, self.on_clear_binary_clicked)
        self.example_selector_lbx.Bind(
            wx.EVT_LISTBOX, self.on_example_selection_changed
        )

        self.load_binary_file_btn.Bind(wx.EVT_BUTTON, self.on_load_binary_file_clicked)

        # Emulate Selection Click
        self.on_gallery_selection_changed(None)

    def on_gallery_selection_changed(self, event):
        selection = self.gallery_selector_lbx.GetStringSelection()
        gallery_item = self.construct_gallery[selection]
        if gallery_item is None:
            self.gallery_selector_lbx.SetSelection(
                self.gallery_selection
            )  # restore old selection
            return

        # save currently shown selection
        self.gallery_selection = self.gallery_selector_lbx.GetSelection()

        self.example_selector_lbx.Clear()
        if len(gallery_item.example_binarys) > 0:
            self.example_selector_lbx.InsertItems(
                list(gallery_item.example_binarys.keys()), 0
            )
            self.example_selector_lbx.SetStringSelection(
                list(gallery_item.example_binarys.keys())[0]
            )

            example = self.example_selector_lbx.GetStringSelection()
            example_binary = self.construct_gallery[selection].example_binarys[example]
        else:
            example_binary = bytes(0)

        self.Freeze()
        self.construct_hex_editor.construct = gallery_item.construct
        self.construct_hex_editor.contextkw = gallery_item.contextkw
        self.construct_hex_editor.binary = example_binary
        self.construct_hex_editor.construct_editor.expand_all()
        self.Thaw()

    def on_clear_binary_clicked(self, event):
        self.example_selector_lbx.SetSelection(wx.NOT_FOUND)
        self.construct_hex_editor.binary = bytes()
        self.construct_hex_editor.construct_editor.expand_all()

    def on_example_selection_changed(self, event):
        selection = self.gallery_selector_lbx.GetStringSelection()
        example = self.example_selector_lbx.GetStringSelection()
        example_binary = self.construct_gallery[selection].example_binarys[example]

        # Set example binary
        self.construct_hex_editor.binary = example_binary
        self.construct_hex_editor.construct_editor.expand_all()

    def on_load_binary_file_clicked(self, event):
        with wx.FileDialog(
            self,
            "Open binary file",
            wildcard="binary files (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            pathname = Path(fileDialog.GetPath())
            with open(pathname, "rb") as file:
                self.construct_hex_editor.binary = file.read()
                self.construct_hex_editor.refresh()


icon = PyEmbeddedImage(
    b"iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABGdBTUEAALGPC/xhBQAAACBj"
    b"SFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAABmJLR0QA/wD/AP+g"
    b"vaeTAAAAB3RJTUUH5QMVEwoXzWaNiAAACetJREFUWMPFl3tQVNcdxz/37oNlF3mJoAS0pviq"
    b"gqiMxRCjkGhSajMTw0wYJyEgiWmijulfRqfEvGge2nSsto5TnFjrMyaTxqmP0WiqEDWIFDS8"
    b"Nmp4s6zswr5Z9t57+geyFSHT6V89M3fOueeec37f3+P7+50L/+cmjTdZ9t6OpwOBwcUCKUKS"
    b"JCQJhLh/hRg9EqPnxb3JB3tN0zDo9T2mCOPn5ds2t40L4Nebtv41I31OUd5jjxATM4GRE4UA"
    b"gQiPRw4WCISmoaoamqahaiqaOtyr6r2xqqCqGoHBAB1dNi5X13kiI/RPfPzB29W6+4W/+9Gu"
    b"rCmTE//0xGM/Z/tHH1L3r1p+teqX1NfVUf7eu0xOSmR+RgaBgJ+3tm2jsvISK1c8Qd/du5S/"
    b"9y6qqrD00UdxDfTzwfu/w+N2k5e7HIvFzK4/7qSq8hKPZC9mVtr0iIvfVM9JTXnokHw/AEVR"
    b"5i1ZvJAdO3awYcMG5s+fz6effkp2djYrV67EarUihGDPnj3k5+ezZs0adu3aRVpaGs8//zz1"
    b"9fUIIUhOTmbdunXU1taiaRrnz5/HbDazdetWdu/ezUPJk5kyefK8yn+enzYKgNFo1JnNkbjd"
    b"bqZOncrMmTNpbGxEr9cTFxeHuBcIra2tzJs3jxkzZtDc3Iwsy0ycOBEATdMQQoTXq6pKa2sr"
    b"M2bMYMKECfh8PhRFIdIUYfD7fZP09wOQJQkhBJGRkaiqit1uJyYmBiHEqCchIYGBgQF8Pt+Y"
    b"76qqomlaGIiiKMTHxzMwMMDQ0BCKoowoIgGmUQBGAm7t2rVs3rwZr9dLWVkZN27c4MCBA3i9"
    b"XhYtWkRxcTHl5eUIISguLqazs5OdO3ditVo5ffo0CxcOu7GpqYkTJ06wbNky3njjDWpqasjL"
    b"y0On+0/ojWLB+7//c+kvViyrSJ87G4/Hg9/vZ9KkSQghsNvtCCEwGo1ER0fj9/txu90kJCQg"
    b"hKCvr49QKARATEwMTqeTYDCIEIKYmBgCgQAOh4MJEyYgSRJHvzjt//CdrU/LYw0wLOzrr78O"
    b"vzudTqqrqwmFQkRHRyOE4MKFCzQ2NiLEML/r6uq4fv16WFh9fT12u524uDiCwSC1tbX09vZi"
    b"NBpHNJcAxrhAALdu3eLYsWN4vV6ee+45Wltb+fLLL+no6GDdunUcOXIEq9WKLMu4XC50Oh3n"
    b"zp0jNTUVm83G8uXLuXbtGu3t7Wzfvh2/38/Nmzepra1l165do+TJo4UPJ5rs7Gzy8vLCgZSZ"
    b"mclTTz0VDrTKykoKCwspKiri9OnTVFVVUVBQQHFxMWfPnmXy5MkUFhYihECSJOLj4ykqKhrW"
    b"XJJGxYD+QfXFPbOPUO7+8f000+l0aJrG0NAQQggMBgNAOA6GU7iELMvIsoxOp0OSJAwGA6qq"
    b"/giAeyyw2+20trZiNBpxuVwoisLt27dxOBw4HA5ycnI4deoUg4ODZGVlkZqaypkzZ5gyZQpZ"
    b"WVmEQiGam5vp7+/HbreTmJhIQ0MDHo8Hm80WzhnjukAIgcvlIj4+HovFQltbG16vF71eT2Ji"
    b"Irdv36agoICJEycSGxvLM888Q15eHunp6SiKQklJCaqq0t3dTW5uLk1NTQDcuXOH/Px8Ghsb"
    b"h10gjUPD8u27S1fk5lRkzJszyvSapoUTzINJ6cEmSVK4f/C7pmkAeDwe/nLg2OAHb29dNdoC"
    b"9yh18uRJcnNzOXPmDJqmUVNTw5o1a1i7di29vb3U1NTw7LPPUlFRAUBXVxcvvvgipaWlfP/9"
    b"97hcLkpKSigtLaW+vp5QKMRLL73EK6+8QlVVFbIsI93TXf8gAFVVycnJob29nYGBAVRV5ZNP"
    b"PmHLli24XC4OHjzIpk2bWL9+PdevX0eSJI4fP05RURGZmZmUl5eTlZXFqlWrWL16NS+//DIF"
    b"BQVkZ2fz2muvUVhYyJ49e8aPAU0Mm7qzsxOn08ndu3fp6enB4XBgMpmIioqio6ODUCiEXq8P"
    b"W6yvr4/U1FSSkpLo6enB6XSSmpqK2WzG4/HQ29tLSkpKeM8IU8ZaQBOo9/wEMDQ0hNfrJTo6"
    b"mq6uLmw2G5MmTSIUCoX9Kcsy06dPx2azERUVRXJyMtOnT6e7uxuHw4HFYiEtLY3m5mYCgUCY"
    b"sqqmhsYCQKCpKvX19Vy8eBFJkkhJSaGoqIi9e/eiqiqvv/46ra2tHDhwAJ/Px9mzZ3nhhRco"
    b"KyvD5/Oxfv16MjIy2LJlC+fOnePVV19l6dKlfPXVV2zcuJHS0lJs9j5hbbF2A2IUC7aVf1ya"
    b"k72wIi7aEjaTTqfDZDKFs5fFYsFgMCCEQK/XYzQaMZlMAASDQSIjI8NM+K6xhQG3Z7g8qyp+"
    b"vx8kCYfDyTtvvbm3u7N9z5gg1FQVj8fDkSNHSEpKYvXq1QSDQQ4ePEhsbCwlJSUoisK+ffsw"
    b"GAxs3LiR3t5eDh06RGZmJitWrECSJL6tqWNKUiLzfjaLYDCI2+2mv7+fYDDIP06esna03blo"
    b"NlvaxqVhRUUFGRkZuFwurly5wv79+3n44YeJiIjgxIkTHD58mNjYWKZNm8a+ffswmUykpKRw"
    b"8uRJgsEg1deuEz0hip9MS0HTNILBIF6vl6GhIb759rr36MH9f9PpdI1+v29gTCYcuQnNnj2b"
    b"RYsWcePGDdra2li4cCFLliyhtraWhoYGli5dyvLly7l69SqxsbEsWLAAIQQtLS1cqa5hzqw0"
    b"FEXB7/fT39+Pz+fjh7ZOdftHHx72+7xXzZao5nGLkaZp4QISCATQ6/Xo9cPL/H5/2O8jh48U"
    b"IYDBwUF6enpwu92EQiGCwSBOpxOv10tP713tt2Vln3W1/3DGbLbUeNyu4BgAI3e5nJwcjh49"
    b"SkdHB4WFhcydO5f9+/fj8XhYtWoV8fHxVFRUoNfrefLJJ3E4HBw/fhyr1UpLSwtCiPCNyePx"
    b"0NXTq5W9+daJlsabX0SYTJf9ft/AuHkgpCiEFIX8/Hyam5uRJInZs2eHfaxpGunp6ZjNZhIS"
    b"EvD5fCxYsACdTsfKlSt5/PHHuXXrFm6/HZfLhcfj4dYP7UpZWdln1qbvvjCZIqsGBwO998sc"
    b"BUCSpLaOLhvTpz7EnDlzwjQUQjBz5kwMBkOYgmlpaRgMBvR6PbIss3jxYiRJwmg0Yutz4Xa7"
    b"uXDpsvvjHdsP9XS1n42IMF0eHAzYHyxeowAY9LpLDc236+Nio+fPnfVTZFlG0zQURUHTNEKh"
    b"UPhyMRInsiyHLx8And29IiY2ju1/2P3d3z8/dngw4K82W6Jq/T7vAOO0Mf+GG36zNf5O6533"
    b"IyIiH42KslgQQh61Thq9/f5XVVWV7u5Oe0N9baXd1vWtLOuaLFEWq8ftHuJH2rh/x0uW5uqa"
    b"Gm4kDzgdkwAj/1sTsiy7jcaIrsHBgPu/Lf4340NlvbmvI1QAAAAldEVYdGRhdGU6Y3JlYXRl"
    b"ADIwMjEtMDMtMjFUMTk6MTA6MjIrMDA6MDDMGKfHAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDIx"
    b"LTAzLTIxVDE5OjEwOjIyKzAwOjAwvUUfewAAAABJRU5ErkJggg=="
)


def main():
    if sys.platform == "win32":
        # Windows Icon fix: https://stackoverflow.com/a/1552105
        import ctypes

        myappid = "timrid.construct_hex_editor"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    inspect = False
    if inspect is True:
        import wx.lib.mixins.inspection as wit

        app = wit.InspectableApp()
    else:
        wit = None
        app = wx.App(False)

    frame = ConstructGalleryFrame(None)
    frame.Show(True)
    if wit is not None:
        wit.InspectionTool().Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
