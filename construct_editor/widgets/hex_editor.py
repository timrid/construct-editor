# -*- coding: utf-8 -*-
import logging

import logging
import dataclasses
import enum
import wx
import wx.stc
import wx.grid as Grid
import wx.lib.newevent
from typing import Optional, Callable
import math
import typing as t

logger = logging.getLogger("my-logger")
logger.propagate = False


# #####################################################################################################################
# ############################################## Grid.GridTableBase ###################################################
# #####################################################################################################################


class OffsetFmt(enum.Enum):
    Hex = 0
    Dez = 1


@dataclasses.dataclass(frozen=True)
class TableFormat:
    width: int = 16
    offsetfmt: OffsetFmt = OffsetFmt.Dez


class HexEditorTable(Grid.GridTableBase):
    def __init__(
        self,
        grid: Grid.Grid,
        binary: bytes,
        table_format: TableFormat,
        on_binary_changed: Optional[Callable[[int, int], None]] = None,
    ):
        super().__init__()

        self.grid = grid

        self.binary: bytearray = bytearray(binary)  # create bytearray from bytes to make it changeable
        self.on_binary_changed = on_binary_changed
        self.table_format = table_format

        self._rows = 0
        self._cols = self.table_format.width

        self._font = wx.Font(
            10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )
        self._attr_default = Grid.GridCellAttr()
        self._attr_default.SetFont(self._font)
        self._attr_default.SetBackgroundColour("white")

        self._attr_selected = Grid.GridCellAttr()
        self._attr_selected.SetFont(self._font)
        self._attr_selected.SetBackgroundColour(wx.Colour(200, 200, 200))

        self.selections: t.List[t.Tuple[int, int]] = []

    def get_next_cursor_rowcol(self, row: int, col: int):
        idx = self.get_byte_index(row, col)
        if idx < len(self.binary):  # one pos further than len(binary) is okay.
            idx += 1
        return self.get_byte_rowcol(idx)

    def get_prev_cursor_rowcol(self, row: int, col: int):
        idx = self.get_byte_index(row, col)
        if idx > 0:
            idx -= 1
        return self.get_byte_rowcol(idx)

    def get_byte_rowcol(self, idx: int):
        col = idx % self._cols
        row = math.floor(idx / self._cols)
        return (row, col)

    def get_byte_index(self, row: int, col: int):
        idx = (row * self._cols) + col
        return idx

    # def ResetView(self, grid: Grid.Grid):
    def refresh(self):
        """
        (Grid) -> Reset the grid view.   Call this to
        update the grid if rows and columns have been added or deleted
        """
        oldrows = self._rows
        oldcols = self._cols

        self._rows = math.ceil(len(self.binary) / self.table_format.width)
        self._cols = self.table_format.width

        self.grid.BeginBatch()
        for current, new, delmsg, addmsg in [
            (
                oldrows,
                self._rows,
                Grid.GRIDTABLE_NOTIFY_ROWS_DELETED,
                Grid.GRIDTABLE_NOTIFY_ROWS_APPENDED,
            ),
            (
                oldcols,
                self._cols,
                Grid.GRIDTABLE_NOTIFY_COLS_DELETED,
                Grid.GRIDTABLE_NOTIFY_COLS_APPENDED,
            ),
        ]:
            if new < current:
                msg = Grid.GridTableMessage(self, delmsg, new, current - new)
                self.grid.ProcessTableMessage(msg)
            elif new > current:
                msg = Grid.GridTableMessage(self, addmsg, new - current)
                self.grid.ProcessTableMessage(msg)
                self.UpdateValues(self.grid)
        self.grid.EndBatch()

        # update the scrollbars and the displayed part of the grid
        self.grid.SetColMinimalAcceptableWidth(0)
        

        # get height of a the biggest char of the font
        dc = wx.MemoryDC()
        dc.SetFont(self._font)
        (char_width, char_height) = dc.GetTextExtent("M")
        self.grid.SetDefaultRowSize(char_height + 2)

        # settings for each column
        hexcol_width = (char_width * 2) + 5
        for col in range(self._cols):
            logger.debug("hexcol %d width=%d" % (col, hexcol_width))
            self.grid.SetColMinimalWidth(col, 0)
            self.grid.SetColSize(col, hexcol_width)

        self.grid.AdjustScrollbars()
        self.grid.ForceRefresh()

    def UpdateValues(self, grid: Grid.Grid):
        """Update all displayed values"""
        # This sends an event to the grid table to update all of the values
        msg = Grid.GridTableMessage(self, Grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        grid.ProcessTableMessage(msg)

    # ############################################ GridTableBase Interface ############################################
    def SetValue(self, row: int, col: int, value: str):
        byte_index = self.get_byte_index(row, col)
        self.binary[byte_index] = int(value, 16)
        if self.on_binary_changed:
            self.on_binary_changed(byte_index, 1)

    def GetValue(self, row: int, col: int):
        byte_index = self.get_byte_index(row, col)
        if byte_index < len(self.binary):
            return f"{self.binary[byte_index]:02x}"
        else:
            return ""

    def IsEmptyCell(self, row: int, col: int):
        byte_index = self.get_byte_index(row, col)
        if byte_index >= len(self.binary):
            return True
        else:
            return False

    def GetColLabelValue(self, col: int):
        return f"{col:X}"

    def GetNumberCols(self):
        return self._cols

    def GetNumberRows(self):
        return self._rows

    def GetRowLabelValue(self, row: int):
        return f"{row * self._cols:04X}"

    def SetAttr(self, attr, row, col):
        # SetAttr not supported
        raise ValueError("SetAttr is not supported")

    def GetAttr(self, row, col, kind):
        byte_pos = (row * self._cols) + col
        
        selected = False
        for sel in self.selections:
            if sel[0] <= byte_pos < sel[1]:
                selected = True
                break

        if selected:
            attr = self._attr_selected
        else:
            attr = self._attr_default

        attr.IncRef() # increment reference count (https://stackoverflow.com/a/14213641)
        return attr


_KEYPAD = [
    wx.WXK_NUMPAD0,
    wx.WXK_NUMPAD1,
    wx.WXK_NUMPAD2,
    wx.WXK_NUMPAD3,
    wx.WXK_NUMPAD4,
    wx.WXK_NUMPAD5,
    wx.WXK_NUMPAD6,
    wx.WXK_NUMPAD7,
    wx.WXK_NUMPAD8,
    wx.WXK_NUMPAD9,
]


def _is_valid_hex_digit(key):
    return (
        key in _KEYPAD
        or (key >= ord("0") and key <= ord("9"))
        or (key >= ord("A") and key <= ord("F"))
        or (key >= ord("a") and key <= ord("f"))
    )


def _get_valid_hex_digit(key):
    if key in _KEYPAD:
        return chr(ord("0") + key - wx.WXK_NUMPAD0)
    elif (
        (key >= ord("0") and key <= ord("9"))
        or (key >= ord("A") and key <= ord("F"))
        or (key >= ord("a") and key <= ord("f"))
    ):
        return chr(key)
    else:
        return None


# #####################################################################################################################
# ############################################## wx.TextCtrl ##########################################################
# #####################################################################################################################
class HexTextCtrl(wx.TextCtrl):
    def __init__(self, parent, id, parentgrid):
        # Don't use the validator here, because apparently we can't
        # reset the validator based on the columns.  We have to do the
        # validation ourselves using EVT_KEY_DOWN.
        wx.TextCtrl.__init__(
            self, parent, id, style=wx.TE_PROCESS_TAB | wx.TE_PROCESS_ENTER
        )
        logger.debug("parent=%s" % parent)
        self.SetInsertionPoint(0)
        self.Bind(wx.EVT_TEXT, self.on_text)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.parentgrid = parentgrid
        self.set_mode("hex")
        self.startValue = None

    def set_mode(self, mode):
        self.mode = mode
        if mode == "hex":
            self.SetMaxLength(2)
            self.autoadvance = 2
        elif mode == "char":
            self.SetMaxLength(1)
            self.autoadvance = 1
        else:
            self.SetMaxLength(0)
            self.autoadvance = 0
        self.userpressed = False

    def editing_new_cell(self, value, mode="hex"):
        """
        Begin editing a new cell by determining the edit mode and
        setting the initial value.
        """
        # Set the mode before setting the value, otherwise on_text gets
        # triggered before self.userpressed is set to false.  When
        # operating in char mode (i.e. autoadvance=1), this causes the
        # editor to skip every other cell.
        self.set_mode(mode)
        self.startValue = value
        self.SetValue(value)
        self.SetFocus()
        self.SetInsertionPoint(0)
        self.SetSelection(-1, -1)  # select the text

    def insert_first_key(self, key):
        """
        Check for a valid initial keystroke, and insert it into the
        text ctrl if it is one.

        @param key: keystroke
        @type key: int

        @returns: True if keystroke was valid, False if not.
        """
        ch = None
        if self.mode == "hex":
            ch = _get_valid_hex_digit(key)
        elif key >= wx.WXK_SPACE and key <= 255:
            ch = chr(key)

        if ch is not None:
            # set self.userpressed before SetValue, because it appears
            # that the on_text callback happens immediately and the
            # keystroke won't be flagged as one that the user caused.
            self.userpressed = True
            self.SetValue(ch)
            self.SetInsertionPointEnd()
            return True

        return False

    def on_key_down(self, evt):
        """
        Keyboard handler to process command keys before they are
        inserted.  Tabs, arrows, ESC, return, etc. should be handled
        here.  If the key is to be processed normally, evt.Skip must
        be called.  Otherwise, the event is eaten here.

        @param evt: key event to process
        """
        logger.debug("key down before evt=%s" % evt.GetKeyCode())
        key = evt.GetKeyCode()

        if key == wx.WXK_TAB:
            wx.CallAfter(self.parentgrid._advance_cursor)
            return
        if key == wx.WXK_ESCAPE:
            self.SetValue(self.startValue)
            wx.CallAfter(self.parentgrid._abort_edit)
            return
        elif self.mode == "hex":
            if _is_valid_hex_digit(key):
                self.userpressed = True
        elif self.mode != "hex":
            self.userpressed = True
        evt.Skip()

    def on_text(self, evt):
        """
        Callback used to automatically advance to the next edit field.
        If self.autoadvance > 0, this number is used as the max number
        of characters in the field.  Once the text string hits this
        number, the field is processed and advanced to the next
        position.

        @param evt: CommandEvent
        """
        logger.debug(
            "evt=%s str=%s cursor=%d" % (evt, evt.GetString(), self.GetInsertionPoint())
        )

        # NOTE: we check that GetInsertionPoint returns 1 less than
        # the desired number because the insertion point hasn't been
        # updated yet and won't be until after this event handler
        # returns.
        if self.autoadvance and self.userpressed:
            if (
                len(evt.GetString()) >= self.autoadvance
                and self.GetInsertionPoint() >= self.autoadvance - 1
            ):
                # FIXME: problem here with a bunch of really quick
                # keystrokes -- the interaction with the
                # underlyingSTCChanged callback causes a cell's
                # changes to be skipped over.  Need some flag in grid
                # to see if we're editing, or to delay updates until a
                # certain period of calmness, or something.
                wx.CallAfter(self.parentgrid._advance_cursor)


# #####################################################################################################################
# ############################################## Grid.GridCellEditor ##################################################
# #####################################################################################################################
class HexCellEditor(Grid.GridCellEditor):
    """
    Cell editor for the grid, based on GridCustEditor.py from the
    wxPython demo.
    """

    def __init__(self, grid: "HexEditorGrid"):
        super().__init__()
        self.parentgrid = grid

    def Create(self, parent, id, evtHandler):
        """
        Called to create the control, which must derive from wx.Control.
        *Must Override*
        """
        logger.debug("")
        self._tc = HexTextCtrl(parent, id, self.parentgrid)
        self.SetControl(self._tc)

        if evtHandler:
            self._tc.PushEventHandler(evtHandler)

    def SetSize(self, rect):
        """
        Called to position/size the edit control within the cell rectangle.
        If you don't fill the cell (the rect) then be sure to override
        PaintBackground and do something meaningful there.
        """
        logger.debug("rect=%s\n" % rect)
        self._tc.SetSize(
            rect.x - 4, rect.y, rect.width + 8, rect.height + 2, wx.SIZE_ALLOW_MINUS_ONE
        )

    def Show(self, show, attr):
        """
        Show or hide the edit control.  You can use the attr (if not None)
        to set colours or fonts for the control.
        """
        logger.debug("show=%s, attr=%s" % (show, attr))
        Grid.PyGridCellEditor.Show(self, show, attr)

    def PaintBackground(self, dc, rectCell, attr):
        """
        Draws the part of the cell not occupied by the edit control.  The
        base  class version just fills it with background colour from the
        attribute.  In this class the edit control fills the whole cell so
        don't do anything at all in order to reduce flicker.
        """
        logger.debug("MyCellEditor: PaintBackground\n")

    def BeginEdit(self, row, col, grid):
        """
        Fetch the value from the table and prepare the edit control
        to begin editing.  Set the focus to the edit control.
        *Must Override*
        """
        logger.debug("row,col=(%d,%d)" % (row, col))
        self.startValue = grid.GetTable().GetValue(row, col)
        mode = "hex"
        self._tc.editing_new_cell(self.startValue, mode)

    def EndEdit(self, row, col, grid, oldval):
        """
        End editing the cell.

        This function must check if the current value of the editing cell
        is valid and different from the original value in its string
        form. If not then simply return None.  If it has changed then
        this method should save the new value so that ApplyEdit can
        apply it later and the string representation of the new value
        should be returned.

        Notice that this method shoiuld not modify the grid as the
        change could still be vetoed.
        """
        logger.debug("row,col=(%d,%d)" % (row, col))
        changed = False

        val = self._tc.GetValue()

        if val != self.startValue:
            changed = True

        return changed

    def ApplyEdit(self, row, col, grid):
        """
        ApplyEdit(row, col, grid)

        Effectively save the changes in the grid.
        """
        val = self._tc.GetValue()

        grid.GetTable().SetValue(row, col, val)  # update the table

        self.startValue = ""
        self._tc.SetValue("")

    def Reset(self):
        """
        Reset the value in the control back to its starting value.
        *Must Override*
        """
        logger.debug("")
        self._tc.SetValue(self.startValue)
        self._tc.SetInsertionPointEnd()

    def IsAcceptedKey(self, evt):
        """
        Return True to allow the given key to start editing: the base class
        version only checks that the event has no modifiers.  F2 is special
        and will always start the editor.
        """
        logger.debug("keycode=%d" % (evt.GetKeyCode()))

        # We can ask the base class to do it
        # return self.base_IsAcceptedKey(evt)

        # or do it ourselves
        return (
            not (evt.ControlDown() or evt.AltDown())
            and evt.GetKeyCode() != wx.WXK_SHIFT
        )

    def StartingKey(self, evt):
        """
        If the editor is enabled by pressing keys on the grid, this will be
        called to let the editor do something about that first key if desired.
        """
        logger.debug("keycode=%d" % evt.GetKeyCode())
        key = evt.GetKeyCode()
        if not self._tc.insert_first_key(key):
            evt.Skip()

    def StartingClick(self):
        """
        If the editor is enabled by clicking on the cell, this method will be
        called to allow the editor to simulate the click on the control if
        needed.
        """
        logger.debug("")

    def Destroy(self):
        """final cleanup"""
        logger.debug("")
        Grid.PyGridCellEditor.Destroy(self)

    def Clone(self):
        """
        Create a new object which is the copy of this one
        *Must Override*
        """
        logger.debug("")
        return HexCellEditor(self.parentgrid)


# #####################################################################################################################
# ############################################## Grid.Grid ############################################################
# #####################################################################################################################
class HexEditorGrid(Grid.Grid):
    """
    Grid for editing in hexidecimal notation.
    """

    def __init__(
        self,
        parent,
        binary: Optional[bytes] = None,
        table_format: Optional[TableFormat] = None,
        on_binary_changed: Optional[Callable[[int, int], None]] = None,
    ):
        """Create the HexEditorGrid viewer"""
        super().__init__(parent)

        if binary is None:
            binary = bytes()
        if table_format is None:
            table_format = TableFormat()

        self._table = HexEditorTable(self, binary, table_format, on_binary_changed)

        # The second parameter means that the grid is to take
        # ownership of the table and will destroy it when done.
        # Otherwise you would need to keep a reference to it and call
        # its Destroy method later.
        self.SetTable(self._table, True)
        self.SetMargins(wx.SYS_VSCROLL_X - 10, wx.SYS_HSCROLL_Y - 10)
        self.SetColMinimalAcceptableWidth(10)
        self.EnableDragGridSize(False)
        self.EnableDragRowSize(False)
        self.EnableDragColSize(False)

        self.SetRowLabelSize(50)
        self.SetColLabelSize(20)

        self.RegisterDataType(Grid.GRID_VALUE_STRING, None, None)
        self.SetDefaultEditor(HexCellEditor(self))

        self.ShowScrollbars(wx.SHOW_SB_ALWAYS, wx.SHOW_SB_ALWAYS)

        self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
        self.GetGridWindow().Bind(wx.EVT_MOTION, self._on_motion)
        self.Show(True)

        self._table.refresh()

        self._colorised_range = None
        self._prev_motion_rowcol = (None, None)

    def _advance_cursor(self):
        self.DisableCellEditControl()
        # FIXME: moving from the hex region to the value region using
        # self.MoveCursorRight(False) causes a segfault, so make sure
        # to stay in the same region
        (row, col) = self.GetTable().get_next_cursor_rowcol(
            self.GetGridCursorRow(), self.GetGridCursorCol()
        )
        self.SetGridCursor(row, col)
        self.EnableCellEditControl()

    def _abort_edit(self):
        self.DisableCellEditControl()

    def _on_motion(self, event):
        x, y = self.CalcUnscrolledPosition(event.GetPosition())
        row = self.YToRow(y)
        col = self.XToCol(x)
        # print(f"row{row} col{col}")
        if (row >= 0) and (col >= 0) and ((row, col) != self._prev_motion_rowcol):
            idx = self._table.get_byte_index(row, col)
            self.GetGridWindow().SetToolTip(f"Index={idx}")
        event.Skip()


    def _on_key_down(self, evt):
        logger.debug("evt=%s" % evt)
        if evt.GetKeyCode() == wx.WXK_RETURN or evt.GetKeyCode() == wx.WXK_TAB:
            if evt.ControlDown():  # the edit control needs this key
                evt.Skip()
            else:
                self.DisableCellEditControl()
                if evt.ShiftDown():
                    (row, col) = self.GetTable().get_prev_cursor_rowcol(
                        self.GetGridCursorRow(), self.GetGridCursorCol()
                    )
                else:
                    (row, col) = self.GetTable().get_next_cursor_rowcol(
                        self.GetGridCursorRow(), self.GetGridCursorCol()
                    )
                self.SetGridCursor(row, col)
                self.MakeCellVisible(row, col)
        else:
            evt.Skip()

    def colorise(self, start: int, end: int, refresh: bool = True):
        """ Colorize a byte range in the Hex Editor. Only a singe range can be colorized """
        self._table.selections = [(start, end)]

        if refresh:
            self.refresh()

    def scroll_to_pos(self, pos: int, refresh: bool = True):
        """ Scroll to a specific byte position in the Hex Editor """
        row, col = self._table.get_byte_rowcol(pos)

        self.MakeCellVisible(row, col)

        if refresh:
            self.refresh()

    def refresh(self):
        """ Refresh the Grid, when some values have canged """
        self._table.refresh()

    # Property: binary ########################################################
    @property
    def binary(self) -> bytes:
        """ Binary data, that is shown in the HexEditor. """
        return self._table.binary

    @binary.setter
    def binary(self, val: bytes):
        self._table.binary = bytearray(val)
        self._table.refresh()

    # Property: table_format ##################################################
    @property
    def table_format(self) -> TableFormat:
        """ Format of the HexEditor. """
        return self._table.table_format

    @table_format.setter
    def table_format(self, val: TableFormat):
        self._table.table_format = val
        self._table.refresh()


if __name__ == "__main__":

    class MyFrame(wx.Frame):
        """ We simply derive a new class of Frame. """

        def __init__(self, parent, title):
            wx.Frame.__init__(self, parent, title=title, size=(1200, 800))
            # self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
            sizer = wx.BoxSizer(wx.HORIZONTAL)

            # Create an instance of our model...
            self.hex_editor = HexEditorGrid(self)
            sizer.Add(self.hex_editor, 0, wx.ALL | wx.EXPAND, 5)

            sizer.Add(
                wx.StaticLine(self, style=wx.LI_VERTICAL), 0, wx.EXPAND | wx.ALL, 5
            )

            self.hex_editor.binary = bytearray(b"HalloWelt123456789ABCDEF")
            self.hex_editor.colorise(10, 1)

            self.SetSizer(sizer)
            self.Show(True)

    app = wx.App(False)
    frame = MyFrame(None, "Construct Viewer")
    app.MainLoop()
