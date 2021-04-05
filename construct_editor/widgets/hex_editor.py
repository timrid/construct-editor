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

    def getNextCursorPosition(self, row: int, col: int):
        col += 1
        if col >= self._cols:
            if row < self._rows - 1:
                row += 1
                col = 0
            else:
                col = self._cols - 1

        return (row, col)

    def getPrevCursorPosition(self, row: int, col: int):
        col -= 1
        if col < 0:
            if row > 0:
                row -= 1
                col = self._cols - 1
            else:
                col = 0

        return (row, col)

    def get_bytes_position(self, idx: int):
        col = idx % self._cols
        row = math.floor(idx / self._cols)
        return (row, col)

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
        font = wx.Font(
            10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )

        # get height of a the biggest char of the font
        dc = wx.MemoryDC()
        dc.SetFont(font)
        (char_width, char_height) = dc.GetTextExtent("M")
        self.grid.SetDefaultRowSize(char_height + 2)

        # settings for each column
        hexcol_width = (char_width * 2) + 5
        for col in range(self._cols):
            # Can't share GridCellAttrs among columns; causes crash when
            # freeing them.  So, have to individually allocate the attrs for
            # each column
            hexattr = Grid.GridCellAttr()
            hexattr.SetFont(font)
            hexattr.SetBackgroundColour("white")
            logger.debug("hexcol %d width=%d" % (col, hexcol_width))
            self.grid.SetColMinimalWidth(col, 0)
            self.grid.SetColSize(col, hexcol_width)
            self.grid.SetColAttr(col, hexattr)

        self.grid.AdjustScrollbars()
        self.grid.ForceRefresh()

    def UpdateValues(self, grid: Grid.Grid):
        """Update all displayed values"""
        # This sends an event to the grid table to update all of the values
        msg = Grid.GridTableMessage(self, Grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        grid.ProcessTableMessage(msg)

    # ############################################ GridTableBase Interface ############################################
    def SetValue(self, row: int, col: int, value: str):
        byte_pos = (row * self._cols) + col
        self.binary[byte_pos] = int(value, 16)
        if self.on_binary_changed:
            self.on_binary_changed(byte_pos, 1)

    def GetValue(self, row: int, col: int):
        byte_pos = (row * self._cols) + col
        logger.debug(
            f"GetValue row={row} col={col} byte_pos={byte_pos} binary_len={len(self.binary)}"
        )
        if byte_pos < len(self.binary):
            return "%02x" % self.binary[byte_pos]
        else:
            return ""

    def IsEmptyCell(self, row: int, col: int):
        byte_pos = (row * self._cols) + col

        if byte_pos >= len(self.binary):
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


class HexDigitMixin(object):
    keypad = [
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

    def isValidHexDigit(self, key):
        return (
            key in HexDigitMixin.keypad
            or (key >= ord("0") and key <= ord("9"))
            or (key >= ord("A") and key <= ord("F"))
            or (key >= ord("a") and key <= ord("f"))
        )

    def getValidHexDigit(self, key):
        if key in HexDigitMixin.keypad:
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
class HexTextCtrl(wx.TextCtrl, HexDigitMixin):
    def __init__(self, parent, id, parentgrid):
        # Don't use the validator here, because apparently we can't
        # reset the validator based on the columns.  We have to do the
        # validation ourselves using EVT_KEY_DOWN.
        wx.TextCtrl.__init__(
            self, parent, id, style=wx.TE_PROCESS_TAB | wx.TE_PROCESS_ENTER
        )
        logger.debug("parent=%s" % parent)
        self.SetInsertionPoint(0)
        self.Bind(wx.EVT_TEXT, self.OnText)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.parentgrid = parentgrid
        self.setMode("hex")
        self.startValue = None

    def setMode(self, mode):
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

    def editingNewCell(self, value, mode="hex"):
        """
        Begin editing a new cell by determining the edit mode and
        setting the initial value.
        """
        # Set the mode before setting the value, otherwise OnText gets
        # triggered before self.userpressed is set to false.  When
        # operating in char mode (i.e. autoadvance=1), this causes the
        # editor to skip every other cell.
        self.setMode(mode)
        self.startValue = value
        self.SetValue(value)
        self.SetFocus()
        self.SetInsertionPoint(0)
        self.SetSelection(-1, -1)  # select the text

    def insertFirstKey(self, key):
        """
        Check for a valid initial keystroke, and insert it into the
        text ctrl if it is one.

        @param key: keystroke
        @type key: int

        @returns: True if keystroke was valid, False if not.
        """
        ch = None
        if self.mode == "hex":
            ch = self.getValidHexDigit(key)
        elif key >= wx.WXK_SPACE and key <= 255:
            ch = chr(key)

        if ch is not None:
            # set self.userpressed before SetValue, because it appears
            # that the OnText callback happens immediately and the
            # keystroke won't be flagged as one that the user caused.
            self.userpressed = True
            self.SetValue(ch)
            self.SetInsertionPointEnd()
            return True

        return False

    def OnKeyDown(self, evt):
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
            if self.isValidHexDigit(key):
                self.userpressed = True
        elif self.mode != "hex":
            self.userpressed = True
        evt.Skip()

    def OnText(self, evt):
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
class HexCellEditor(Grid.GridCellEditor, HexDigitMixin):
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
        self._tc.editingNewCell(self.startValue, mode)

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
        if not self._tc.insertFirstKey(key):
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

        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Show(True)

        self._table.refresh()

        self._colorised_range = None

    def _advance_cursor(self):
        self.DisableCellEditControl()
        # FIXME: moving from the hex region to the value region using
        # self.MoveCursorRight(False) causes a segfault, so make sure
        # to stay in the same region
        (row, col) = self.GetTable().getNextCursorPosition(
            self.GetGridCursorRow(), self.GetGridCursorCol()
        )
        self.SetGridCursor(row, col)
        self.EnableCellEditControl()

    def _abort_edit(self):
        self.DisableCellEditControl()

    def OnKeyDown(self, evt):
        logger.debug("evt=%s" % evt)
        if evt.GetKeyCode() == wx.WXK_RETURN or evt.GetKeyCode() == wx.WXK_TAB:
            if evt.ControlDown():  # the edit control needs this key
                evt.Skip()
            else:
                self.DisableCellEditControl()
                if evt.ShiftDown():
                    (row, col) = self.GetTable().getPrevCursorPosition(
                        self.GetGridCursorRow(), self.GetGridCursorCol()
                    )
                else:
                    (row, col) = self.GetTable().getNextCursorPosition(
                        self.GetGridCursorRow(), self.GetGridCursorCol()
                    )
                self.SetGridCursor(row, col)
                self.MakeCellVisible(row, col)
        else:
            evt.Skip()

    def colorise(self, start: int, end: int, refresh: bool = True):
        """ Colorize a byte range in the Hex Editor. Only a singe range can be colorized """
        # reset old colors
        if self._colorised_range:
            old_start = self._colorised_range[0]
            old_end = self._colorised_range[1]
            self._colorise(old_start, old_end, wx.WHITE)

        # set new colors
        self._colorised_range = (start, end)
        self._colorise(start, end, wx.Colour(200, 200, 200))

        if refresh:
            self.refresh()

    def scroll_to_pos(self, pos: int, refresh: bool = True):
        """ Scroll to a specific byte position in the Hex Editor """
        row, col = self._table.get_bytes_position(pos)

        self.MakeCellVisible(row, col)

        if refresh:
            self.refresh()

    def _colorise(self, start: int, end: int, colour: wx.Colour):
        for idx in range(start, end, 1):
            row, col = self._table.get_bytes_position(idx)
            self.SetCellBackgroundColour(row, col, colour)

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
