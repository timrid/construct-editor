# -*- coding: utf-8 -*-
import logging

import dataclasses
import wx
import wx.stc
import wx.grid as Grid
import wx.lib.newevent
from typing import Optional, Callable, List
import math
import typing as t

from construct_editor.helper import CallbackList

logger = logging.getLogger("my-logger")
logger.propagate = False


class BinaryChangedCallbackList(CallbackList[Callable[["HexEditorBinaryData"], None]]):
    def fire(self, binary_data: "HexEditorBinaryData"):
        for listener in self:
            listener(binary_data)


class SelectionChangedCallbackList(CallbackList[Callable[[int, Optional[int]], None]]):
    def fire(self, start_idx: int, end_idx: Optional[int]):
        for listener in self:
            listener(start_idx, end_idx)


# #####################################################################################################################
# ############################################## HexEditorBinaryData ##################################################
# #####################################################################################################################
class HexEditorBinaryData:
    """
    Binary Data, which is shown in the HexEditor.
    This class is used mainly to track changes and notiy everyone
    """

    def __init__(self, binary: bytes) -> None:
        self._binary = bytearray(binary)

        self.on_binary_changed = BinaryChangedCallbackList()
        self.command_processor = wx.CommandProcessor()

    def overwrite_all(self, byts: bytes):
        """overwrite the complete data with the new ones"""
        obj = self

        class Cmd(wx.Command):
            def __init__(self):
                super().__init__(True, "Overwrite All")

            def Do(self):
                self._binary_backup = obj._binary
                obj._binary.clear()
                obj._binary[0:0] = byts
                obj.on_binary_changed.fire(obj)
                return True

            def Undo(self):
                obj._binary.clear()
                obj._binary[0:0] = self._binary_backup
                obj.on_binary_changed.fire(obj)
                return True

        self.command_processor.Submit(Cmd())

    def overwrite_range(self, idx: int, byts: bytes):
        """overwrite byte range beginning from the given index"""
        obj = self

        class Cmd(wx.Command):
            def __init__(self):
                super().__init__(
                    True, f"Overwrite Range (Index: {idx}, Length: {len(byts)})"
                )

            def Do(self):
                self._range_backup = obj._binary[idx : idx + len(byts)]
                if obj._binary[idx : idx + len(byts)] == byts:
                    return False
                obj._binary[idx : idx + len(byts)] = byts
                obj.on_binary_changed.fire(obj)
                return True

            def Undo(self):
                obj._binary[idx : idx + len(byts)] = self._range_backup
                obj.on_binary_changed.fire(obj)
                return True

        self.command_processor.Submit(Cmd())

    def insert_range(self, idx: int, byts: bytes):
        """inserts byte range at the given index"""
        obj = self

        class Cmd(wx.Command):
            def __init__(self):
                super().__init__(
                    True, f"Insert Range (Index: {idx}, Length: {len(byts)})"
                )

            def Do(self):
                obj._binary[idx:idx] = byts
                obj.on_binary_changed.fire(obj)
                return True

            def Undo(self):
                del obj._binary[idx : idx + len(byts)]
                obj.on_binary_changed.fire(obj)
                return True

        self.command_processor.Submit(Cmd())

    def remove_range(self, idx: int, length: int):
        """remove the bytes at at the given range"""
        obj = self

        class Cmd(wx.Command):
            def __init__(self):
                super().__init__(True, f"Remove Range (Index: {idx}, Length: {length})")
                super().__init__(True, "Overwrite Range")

            def Do(self):
                self._range_backup = obj._binary[idx : idx + length]
                del obj._binary[idx : idx + length]
                obj.on_binary_changed.fire(obj)
                return True

            def Undo(self):
                obj._binary[idx:idx] = self._range_backup
                obj.on_binary_changed.fire(obj)
                return True

        self.command_processor.Submit(Cmd())

    def get_value(self, idx: int):
        """get the value at the given index"""
        return self._binary[idx]

    def get_range(self, idx: int, len: int):
        """get the value at the given index"""
        return bytes(self._binary[idx : idx + len])

    def get_bytes(self) -> bytes:
        """return readonly version of the data"""
        return bytes(self._binary)

    def __len__(self):
        return len(self._binary)


# #####################################################################################################################
# ############################################## Grid.GridTableBase ###################################################
# #####################################################################################################################


@dataclasses.dataclass(frozen=True)
class HexEditorFormat:
    width: int = 16
    label_base: int = 16


class HexEditorTable(Grid.GridTableBase):
    def __init__(self, editor: "HexEditor", binary_data: HexEditorBinaryData):
        super().__init__()

        self._editor = editor
        self._binary_data = binary_data

        self._rows: int = 0
        self._cols: int = self._editor.format.width

        self.font = wx.Font(
            10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )

        self._attr_default = Grid.GridCellAttr()
        self._attr_default.SetFont(self.font)
        self._attr_default.SetBackgroundColour("white")

        self._attr_selected = Grid.GridCellAttr()
        self._attr_selected.SetFont(self.font)
        self._attr_selected.SetBackgroundColour(wx.Colour(200, 200, 200))

        self.selections: t.List[t.Tuple[int, int]] = []

    def get_next_cursor_rowcol(self, row: int, col: int):
        idx = self.get_byte_idx(row, col)
        if idx < len(self._binary_data):  # one index further than len(binary) is okay.
            idx += 1
        return self.get_byte_rowcol(idx)

    def get_prev_cursor_rowcol(self, row: int, col: int):
        idx = self.get_byte_idx(row, col)
        if idx > 0:
            idx -= 1
        return self.get_byte_rowcol(idx)

    def get_byte_rowcol(self, idx: int):
        col = idx % self._cols
        row = math.floor(idx / self._cols)
        return (row, col)

    def get_byte_idx(self, row: int, col: int):
        idx = (row * self._cols) + col
        return idx

    def refresh_rows_cols(self):
        self._rows = math.ceil(len(self._binary_data) / self._editor.format.width)
        if (len(self._binary_data) % self._editor.format.width) == 0:
            self._rows += 1
        self._cols = self._editor.format.width

    # ############################################ GridTableBase Interface ############################################
    def SetValue(self, row: int, col: int, value: str):
        byte_idx = self.get_byte_idx(row, col)
        if value == "" and byte_idx >= len(self._binary_data):
            return
        self._binary_data.overwrite_range(byte_idx, bytes([int(value, 16)]))

    def GetValue(self, row: int, col: int):
        byte_idx = self.get_byte_idx(row, col)
        if byte_idx < len(self._binary_data):
            return f"{self._binary_data.get_value(byte_idx):02x}"
        else:
            return ""

    def IsEmptyCell(self, row: int, col: int):
        byte_idx = self.get_byte_idx(row, col)
        if byte_idx >= len(self._binary_data):
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
        byte_idx = self.get_byte_idx(row, col)

        selected = False
        for sel in self.selections:
            if sel[0] <= byte_idx < sel[1]:
                selected = True
                break

        if selected:
            attr = self._attr_selected
        else:
            attr = self._attr_default

        attr.IncRef()  # increment reference count (https://stackoverflow.com/a/14213641)
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
            else:
                return
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
        editor: "HexEditor",
        table: HexEditorTable,
        binary_data: HexEditorBinaryData,
        read_only: bool = False,
    ):
        super().__init__(editor)
        self._editor = editor
        self._table = table
        self._binary_data = binary_data
        self.read_only = read_only
        self.on_selection_changed = SelectionChangedCallbackList()

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
        self.EnableEditing(not self.read_only)

        self.SetRowLabelSize(50)
        self.SetColLabelSize(20)

        self.RegisterDataType(Grid.GRID_VALUE_STRING, None, None)
        self.SetDefaultEditor(HexCellEditor(self))

        self.ShowScrollbars(wx.SHOW_SB_ALWAYS, wx.SHOW_SB_ALWAYS)

        self.GetGridWindow().Bind(wx.EVT_LEFT_DOWN, self._on_mouse_left_down)
        self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
        self.Bind(Grid.EVT_GRID_SELECT_CELL, self._on_select_cell)
        self.Bind(Grid.EVT_GRID_RANGE_SELECTING, self._on_range_selecting_mouse)
        self.Bind(Grid.EVT_GRID_CELL_RIGHT_CLICK, self._on_cell_right_click)

        self.Show(True)

        self.refresh()

        self._selection: t.Tuple[Optional[int], Optional[int]] = (None, None)

    def refresh(self):
        """
        (Grid) -> Reset the grid view.   Call this to
        update the grid if rows and columns have been added or deleted
        """
        oldrows = self._table.GetNumberRows()
        oldcols = self._table.GetNumberCols()

        self._table.refresh_rows_cols()

        newrows = self._table.GetNumberRows()
        newcols = self._table.GetNumberCols()

        self.BeginBatch()
        for current, new, delmsg, addmsg in [
            (
                oldrows,
                newrows,
                Grid.GRIDTABLE_NOTIFY_ROWS_DELETED,
                Grid.GRIDTABLE_NOTIFY_ROWS_APPENDED,
            ),
            (
                oldcols,
                newcols,
                Grid.GRIDTABLE_NOTIFY_COLS_DELETED,
                Grid.GRIDTABLE_NOTIFY_COLS_APPENDED,
            ),
        ]:
            if new < current:
                msg = Grid.GridTableMessage(self._table, delmsg, new, current - new)
                self.ProcessTableMessage(msg)
            elif new > current:
                msg = Grid.GridTableMessage(self._table, addmsg, new - current)
                self.ProcessTableMessage(msg)
                # This sends an event to the grid table to update all of the displayed values
                msg = Grid.GridTableMessage(
                    self._table, Grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES
                )
                self.ProcessTableMessage(msg)
        self.EndBatch()

        # update the scrollbars and the displayed part of the grid
        self.SetColMinimalAcceptableWidth(0)

        # get height of a the biggest char of the font
        dc = wx.MemoryDC()
        dc.SetFont(self._table.font)
        (char_width, char_height) = dc.GetTextExtent("M")
        self.SetDefaultRowSize(char_height + 2)

        # settings for each column
        hexcol_width = (char_width * 2) + 5
        for col in range(newcols):
            logger.debug("hexcol %d width=%d" % (col, hexcol_width))
            self.SetColMinimalWidth(col, 0)
            self.SetColSize(col, hexcol_width)

        self.AdjustScrollbars()
        self.ForceRefresh()

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

    def _on_mouse_left_down(self, event):
        if event.AltDown() or event.ShiftDown() or event.ControlDown():
            # don't support selecting multiple ranges with ATL/SHIFT/CTRL.
            self._on_range_selecting_mouse(None)
            return
        else:
            event.Skip()

    def _on_select_cell(self, event: Grid.GridEvent):
        """Single cell selected"""
        idx = self._table.get_byte_idx(event.GetRow(), event.GetCol())
        self.ClearSelection()
        self._selection = (idx, None)
        self.on_selection_changed.fire(start_idx=idx, end_idx=None)

    def _on_range_selecting_mouse(self, event):
        """Change selection from a rectangular block to a range between two indexes"""
        # get the first selected item
        row1, col1 = self.GetGridCursorCoords()

        # get the current mouse position
        x, y = self.CalcUnscrolledPosition(
            self.GetGridWindow().ScreenToClient(wx.GetMousePosition())
        )
        row2 = self.YToRow(y)
        col2 = self.XToCol(x)

        idx1 = self._table.get_byte_idx(row1, col1)
        idx2 = self._table.get_byte_idx(row2, col2)

        self.select_range(idx1, idx2)

    def _on_range_selecting_keyboard(self, row_diff: int = 0, col_diff: int = 0):
        """Change selection from the keyboard"""
        sel = self._selection
        if sel[0] is None:
            return  # nothing is currently selected

        cursor_row, cursor_col = self.GetGridCursorCoords()
        cursor_idx = self._table.get_byte_idx(cursor_row, cursor_col)

        if sel[1] is None:
            other_idx = cursor_idx
        else:
            if sel[0] == cursor_idx:
                other_idx = sel[1]
            else:
                other_idx = sel[0]

        cursor_row += row_diff
        cursor_col += col_diff
        cursor_idx = self._table.get_byte_idx(cursor_row, cursor_col)

        self.SetGridCursor(cursor_row, cursor_col)

        self.select_range(cursor_idx, other_idx)

    def select_range(self, idx1: int, idx2: int):
        """Select the range between two byte indexes."""
        if idx1 < 0 or idx2 < 0:
            return
        idx1 = min(idx1, len(self._binary_data) - 1)
        idx2 = min(idx2, len(self._binary_data) - 1)
        if idx1 > idx2:
            idx1, idx2 = idx2, idx1
        start_row, start_col = self._table.get_byte_rowcol(idx1)
        end_row, end_col = self._table.get_byte_rowcol(idx2)

        first_col = 0
        last_col = self._table.GetNumberCols() - 1
        row_dist = end_row - start_row

        self.ClearSelection()
        if row_dist == 0:
            # start and end are in the same row
            self.SelectBlock(start_row, start_col, end_row, end_col, True)
        else:
            # start and end are in different rows
            self.SelectBlock(start_row, start_col, start_row, last_col, True)
            self.SelectBlock(end_row, first_col, end_row, end_col, True)

        if row_dist > 1:
            # select body
            self.SelectBlock(start_row + 1, first_col, end_row - 1, last_col, True)

        self._selection = (idx1, idx2)
        self.on_selection_changed.fire(start_idx=idx1, end_idx=idx2)

    def _cut_selection(self) -> bool:
        """
        Copy the selected data to the clipboard and remove it from the binary data

        Return:
         - true if copy is okay
         - false if an error occured
        """
        if self.read_only is True:
            return False

        if self._copy_selection() is False:
            return False
        if self._remove_selection() is False:
            return False
        return True

    def _remove_selection(self) -> bool:
        """
        Remove the selected bytes

        Return:
         - true if copy is okay
         - false if an error occured
        """
        if self.read_only is True:
            return False

        sel = self._selection
        if sel[0] is None:
            return False

        if sel[1] == None:
            len = 1
        else:
            len = sel[1] - sel[0] + 1

        byts = self._binary_data.remove_range(sel[0], len)

        self.ClearSelection()
        self._selection = (None, None)

        self.refresh()
        return True

    def _copy_selection(self) -> bool:
        """
        Copy the selected data to the clipboard

        Return:
         - true if copy is okay
         - false if an error occured
        """
        sel = self._selection
        if sel[0] is None:
            return False

        if sel[1] == None:
            len = 1
        else:
            len = sel[1] - sel[0] + 1

        byts = self._binary_data.get_range(sel[0], len)

        if wx.TheClipboard.Open():
            byts_str = byts.hex(" ")
            wx.TheClipboard.SetData(wx.TextDataObject(byts_str))
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Can't open the clipboard", "Warning")
            return False
        return True

    def _paste(self, overwrite: bool = False, insert: bool = False) -> bool:
        """
        Paste the data from the clipboard to the selected position.

        If overwrite=True: overwrite the current binary data. The binary data is only
                           increased, if the pasted data overlaps the binary size.

        If insert=True: Insert new bytes to the binary data. The binary data is always
                        increased by the size of the data from the clipboard.
        """
        if self.read_only is True:
            return False

        # check if somethis is selected
        sel = self._selection
        if sel[0] is None:
            return False

        if overwrite and insert:
            wx.MessageBox(
                "Only one option is supported. 'overwrite' or 'insert'", "Warning"
            )
            return False

        # get data from clipboard
        if not wx.TheClipboard.Open():
            wx.MessageBox("Can't open the clipboard", "Warning")
            return False
        clipboard = wx.TextDataObject()
        wx.TheClipboard.GetData(clipboard)
        wx.TheClipboard.Close()
        byts_str: str = clipboard.GetText()

        # convert string to bytes
        try:
            byts_str = byts_str.replace(" ", "")
            byts = bytes.fromhex(byts_str)
        except Exception as e:
            wx.MessageBox(
                f"Can't convert data from clipboard to bytes.\n\n{str(e)}\n\nClipboard Data:\n{byts_str}",
                "Warning",
            )
            return False

        # copy new data to the binary data
        if overwrite:
            self._binary_data.overwrite_range(sel[0], byts)
        if insert:
            self._binary_data.insert_range(sel[0], byts)

        self.select_range(sel[0], sel[0] + len(byts) - 1)
        return True

    def _undo(self):
        self._binary_data.command_processor.Undo()

    def _redo(self):
        self._binary_data.command_processor.Redo()

    def _on_key_down(self, event: wx.KeyEvent):
        if event.GetKeyCode() == wx.WXK_RETURN or event.GetKeyCode() == wx.WXK_TAB:
            if event.ControlDown():  # the edit control needs this key
                event.Skip()
            else:
                self.DisableCellEditControl()
                if event.ShiftDown():
                    (row, col) = self.GetTable().get_prev_cursor_rowcol(
                        self.GetGridCursorRow(), self.GetGridCursorCol()
                    )
                else:
                    (row, col) = self.GetTable().get_next_cursor_rowcol(
                        self.GetGridCursorRow(), self.GetGridCursorCol()
                    )
                self.SetGridCursor(row, col)
                self.MakeCellVisible(row, col)

        # Shift+Up
        elif event.ShiftDown() and event.GetKeyCode() == wx.WXK_UP:
            self._on_range_selecting_keyboard(row_diff=-1)

        # Shift+Down
        elif event.ShiftDown() and event.GetKeyCode() == wx.WXK_DOWN:
            self._on_range_selecting_keyboard(row_diff=1)

        # Shift+Left
        elif event.ShiftDown() and event.GetKeyCode() == wx.WXK_LEFT:
            self._on_range_selecting_keyboard(col_diff=-1)

        # Shift+Right
        elif event.ShiftDown() and event.GetKeyCode() == wx.WXK_RIGHT:
            self._on_range_selecting_keyboard(col_diff=1)

        # Ctrl+Z
        elif event.ControlDown() and event.GetKeyCode() == ord("Z"):
            self._undo()

        # Ctrl+Y
        elif event.ControlDown() and event.GetKeyCode() == ord("Y"):
            self._redo()

        # Ctrl+X
        elif event.ControlDown() and event.GetKeyCode() == ord("X"):
            self._cut_selection()

        # Ctrl+C
        elif event.ControlDown() and event.GetKeyCode() == ord("C"):
            self._copy_selection()

        elif event.ControlDown() and event.GetKeyCode() == ord("V"):
            # Ctrl+Shift+V
            if event.ShiftDown():
                self._paste(insert=True)

            # Ctrl+V
            else:
                self._paste(overwrite=True)

        # Ctrl+A
        elif event.ControlDown() and event.GetKeyCode() == ord("A"):
            self.select_range(0, len(self._binary_data) - 1)

        else:
            event.Skip()

    def _on_cell_right_click(self, event: Grid.GridEvent):
        """Show context menu"""
        # Check if the click is inside the current selection.
        # If not, select the current cell
        sel = self._selection
        select_cell = True
        if sel[0] is not None and sel[1] is not None:
            idx = self._table.get_byte_idx(event.GetRow(), event.GetCol())
            if sel[0] <= idx <= sel[1]:
                select_cell = False

        if select_cell:
            self.SetGridCursor(event.GetRow(), event.GetCol())

        menus = [
            (
                wx.ID_CUT,
                "Cut\tCtrl+X",
                lambda event: self._cut_selection(),
                not self.read_only,
            ),
            (wx.ID_COPY, "Copy\tCtrl+C", lambda event: self._copy_selection(), True),
            (
                wx.ID_PASTE,
                "Paste (overwrite)\tCtrl+V",
                lambda event: self._paste(overwrite=True),
                not self.read_only,
            ),
            (
                wx.ID_PASTE,
                "Paste (insert)\tCtrl+Shift+V",
                lambda event: self._paste(insert=True),
                not self.read_only,
            ),
            None,
            (
                wx.ID_UNDO,
                "Undo\tCtrl+Z",
                lambda event: self._undo(),
                self._binary_data.command_processor.CanUndo(),
            ),
            (
                wx.ID_REDO,
                "Redo\tCtrl+Y",
                lambda event: self._redo(),
                self._binary_data.command_processor.CanRedo(),
            ),
        ]

        popup_menu = wx.Menu()
        for menu in menus:
            if menu is None:
                popup_menu.AppendSeparator()
                continue
            item: wx.MenuItem = popup_menu.Append(menu[0], menu[1])
            self.Bind(wx.EVT_MENU, menu[2], id=item.Id)
            item.Enable(menu[3])

        self.PopupMenu(popup_menu, event.GetPosition())
        popup_menu.Destroy()


# #####################################################################################################################
# ############################################## HexEditor ############################################################
# #####################################################################################################################
class HexEditor(wx.Panel):
    """
    HexEdior Panel.
    """

    def __init__(
        self,
        parent,
        binary: bytes = b"",
        format: Optional[HexEditorFormat] = None,
        read_only: bool = False,
        bitwiese: bool = False,
    ):
        super().__init__(parent)

        self._binary_data = HexEditorBinaryData(binary)
        if format is None:
            self._format = HexEditorFormat()
        else:
            self._format = format
        self.bitwiese = bitwiese

        # self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # create HexEditorTable & HexEditorGrid
        self._table = HexEditorTable(self, self._binary_data)
        self._grid = HexEditorGrid(self, self._table, self._binary_data, read_only)
        sizer.Add(self._grid, 1, wx.ALL | wx.EXPAND, 0)

        # create status bar
        self._status_bar = wx.StatusBar(
            self,
            style=wx.STB_SHOW_TIPS | wx.STB_ELLIPSIZE_END | wx.FULL_REPAINT_ON_RESIZE,
        )
        self._status_bar.SetFieldsCount(2)
        self._status_bar.SetStatusStyles(
            [wx.SB_NORMAL, wx.SB_FLAT]
        )  # remove vertical line after the last field
        sizer.Add(self._status_bar, 0, wx.ALL | wx.EXPAND, 0)

        self.on_binary_changed.append(self._on_binary_changed)
        self.on_selection_changed.append(self._on_selection_changed)

        self.SetSizer(sizer)
        self.Show(True)

    def _on_binary_changed(self, binary_data: HexEditorBinaryData):
        if self.bitwiese is True:
            unit = "Bits"
        else:
            unit = "Bytes"

        msg = f"{len(binary_data):n} {unit}"
        self._status_bar.SetStatusText(msg, 0)
        self.refresh()

    def _on_selection_changed(self, idx1: int, idx2: Optional[int]):
        if idx2 is None:
            msg = f"Selection: {idx1:n}"
        else:
            msg = f"Selection: {idx1:n}-{idx2:n} ({idx2-idx1+1:n})"

        self._status_bar.SetStatusText(msg, 1)

    def colorise(self, start: int, end: int, refresh: bool = True):
        """Colorize a byte range in the Hex Editor. Only a singe range can be colorized"""
        self._table.selections = [(start, end)]

        if refresh:
            self.refresh()

    def scroll_to_idx(self, idx: int, refresh: bool = True):
        """Scroll to a specific byte index in the Hex Editor"""
        row, col = self._table.get_byte_rowcol(idx)

        self._grid.MakeCellVisible(row, col)

        if refresh:
            self.refresh()

    def refresh(self):
        """Refresh the Grid, when some values have canged"""
        self._grid.refresh()

    # Property: binary ########################################################
    @property
    def binary(self) -> bytes:
        """Binary data, that is shown in the HexEditor."""
        return self._binary_data.get_bytes()

    @binary.setter
    def binary(self, val: bytes):
        self.colorise(0, 0, True)
        self._binary_data.overwrite_all(val)
        # clear all commands, when new data is set from external
        self._binary_data.command_processor.ClearCommands()

    # Property: format ##################################################
    @property
    def format(self) -> HexEditorFormat:
        """Format of the HexEditor."""
        return self._format

    @format.setter
    def format(self, val: HexEditorFormat):
        self._format = val
        self.refresh()

    # Property: on_binary_changed #############################################
    @property
    def on_binary_changed(self) -> BinaryChangedCallbackList:
        return self._binary_data.on_binary_changed

    # Property: on_binary_changed #############################################
    @property
    def on_selection_changed(self) -> SelectionChangedCallbackList:
        return self._grid.on_selection_changed


if __name__ == "__main__":

    class MyFrame(wx.Frame):
        """We simply derive a new class of Frame."""

        def __init__(self, parent, title):
            wx.Frame.__init__(self, parent, title=title, size=(420, 800))

            # Create an instance of our model...
            self.hex_editor = HexEditor(self)

            self.hex_editor.binary = bytearray(500)

            self.Show(True)

    app = wx.App(False)
    frame = MyFrame(None, "HexEditor Example")
    app.MainLoop()
