# -*- coding: utf-8 -*-
import dataclasses
import textwrap
import typing as t

import construct as cs
import wx
import wx.dataview as dv

from construct_editor.core.construct_editor import ConstructEditor
from construct_editor.core.entries import EntryConstruct, EntryFlag
from construct_editor.core.model import ConstructEditorColumn, ConstructEditorModel
from construct_editor.wx_widgets.wx_context_menu import WxContextMenu
from construct_editor.wx_widgets.wx_obj_view import (
    WxObjEditor,
    WxObjRendererHelper,
    create_obj_editor,
    create_obj_renderer_helper,
)
from construct_editor.wx_widgets.wx_exception_dialog import WxExceptionDialog


@dataclasses.dataclass
class ValueFromEditorCtrl:
    """
    The `new_obj` has to be passed in a subclass, because subtypes of `int` (eg. `IntEnum`)
    and `str` (eg. `cs.EnumIntegerString`) are converted to its base type
    by the DVC...
    """

    new_obj: t.Any


class ObjectRenderer(dv.DataViewCustomRenderer):
    def __init__(self):
        super().__init__(varianttype="PyObject")
        self.entry: t.Optional[EntryConstruct] = None
        self.entry_renderer_helper: t.Optional[WxObjRendererHelper] = None
        self.EnableEllipsize(wx.ELLIPSIZE_END)

    def SetValue(self, value: EntryConstruct):
        self.entry = value
        self.entry_renderer_helper = create_obj_renderer_helper(
            self.entry.obj_view_settings
        )
        return True

    def GetValue(self):
        return self.entry

    def GetSize(self):
        if self.entry_renderer_helper is None:
            raise ValueError("`entry_renderer_helper` not set")
        return self.entry_renderer_helper.get_size(self)

    def Render(self, rect: wx.Rect, dc: wx.DC, state):
        if self.entry_renderer_helper is None:
            raise ValueError("`entry_renderer_helper` not set")
        return self.entry_renderer_helper.render(self, rect, dc, state)

    def GetMode(self) -> int:
        """
        Return the mode.
        - dv.DATAVIEW_CELL_INERT:
            The cell only displays information and cannot be manipulated or
            otherwise interacted with in any way.

        - dv.DATAVIEW_CELL_ACTIVATABLE:
            Indicates that the cell can be activated by clicking it or using
            keyboard.
            (see `ActivateCell`)

        - dv.DATAVIEW_CELL_EDITABLE:
            Indicates that the user can edit the data in-place in an inline
            editor control that will show up when the user wants to edit the
            cell.
            (see `HasEditorCtrl`, `CreateEditorCtrl`, `GetValueFromEditorCtrl`)

        """
        # `SetValue` is not called befor `GetMode` is called, so
        # `self.entry_renderer_helper` is not valid to use here. So we
        # have to detect the selecte item of the dvc and assume that
        # we need to get the mode for this item. (Fingers crossed that
        # this always works.)

        dvc: "dv.DataViewCtrl" = self.GetView()
        editor: "WxConstructEditor" = dvc.GetParent()
        selected_entry = editor.get_selected_entry()
        if selected_entry is None:
            mode = dv.DATAVIEW_CELL_INERT
        else:
            try:
                obj_view_settings = selected_entry.obj_view_settings
                helper = create_obj_renderer_helper(obj_view_settings)
                mode = helper.get_mode()
            except Exception:
                # it is possible that an error occures, when the construct
                # format has changed...
                mode = dv.DATAVIEW_CELL_INERT
        return mode

    def ActivateCell(
        self,
        rect: wx.Rect,
        model: dv.DataViewModel,
        item: dv.DataViewItem,
        col: int,
        mouseEvent: t.Optional[wx.MouseEvent],
    ):
        if self.entry_renderer_helper is None:
            raise ValueError("`entry_renderer_helper` not set")
        return self.entry_renderer_helper.activate_cell(
            self, rect, model, item, col, mouseEvent
        )

    # The HasEditorCtrl, CreateEditorCtrl and GetValueFromEditorCtrl
    # methods need to be implemented if this renderer is going to
    # support in-place editing of the cell value, otherwise they can
    # be omitted.

    def HasEditorCtrl(self):
        return True

    def CreateEditorCtrl(
        self, parent, labelRect: wx.Rect, value: EntryConstruct
    ) -> WxObjEditor:
        view_settings = value.obj_view_settings
        editor: WxObjEditor = create_obj_editor(parent, view_settings)
        editor.SetPosition(labelRect.Position)
        editor.SetSize(labelRect.Size)
        return editor

    def GetValueFromEditorCtrl(self, editor: WxObjEditor):
        new_obj = editor.get_new_obj()
        return ValueFromEditorCtrl(new_obj)


class WxConstructEditorModel(dv.PyDataViewModel, ConstructEditorModel):
    """
    This model acts as a bridge between the DataViewCtrl and the dataclasses.
    This model provides these data columns:
        0. Name: string
        1. Type: string
        2. Value: string
    """

    def __init__(self, dvc: dv.DataViewCtrl):
        ConstructEditorModel.__init__(self)
        dv.PyDataViewModel.__init__(self)
        self.dvc = dvc

        # The PyDataViewModel derives from both DataViewModel and from
        # DataViewItemObjectMapper, which has methods that help associate
        # data view items with Python objects. Normally a dictionary is used
        # so any Python object can be used as data nodes. If the data nodes
        # are weak-referencable then the objmapper can use a
        # WeakValueDictionary instead.
        # self.UseWeakRefs(True)  # weak refs are slower when creating a large number of items

    # #################################################################################################################
    # Helper ##########################################################################################################
    # #################################################################################################################
    def dvc_item_to_entry(self, dvc_item: dv.DataViewItem) -> EntryConstruct:
        """
        Convert an Entry to an dvc item.
        """
        entry = self.ItemToObject(dvc_item)
        if not isinstance(entry, EntryConstruct):
            raise ValueError(f"{repr(entry)} is no valid entry")
        return entry

    def entry_to_dvc_item(self, entry: EntryConstruct) -> dv.DataViewItem:
        """
        Convert an entry to an dvc item.
        An dvc item always represents an visible row in the view. So if
        an entry is not visible, the corresponding visible entry is used.
        """
        visible_row_entry = entry.get_visible_row_entry()
        if visible_row_entry is None:
            return dv.NullDataViewItem
        dvc_item = self.ObjectToItem(visible_row_entry)
        return dvc_item

    # #################################################################################################################
    # ConstructEditorModel Interface ##################################################################################
    # #################################################################################################################
    def on_value_changed(self, entry: "EntryConstruct"):
        dvc_item = self.entry_to_dvc_item(entry)
        self.ItemChanged(dvc_item)

    # #################################################################################################################
    # dv.PyDataViewModel Interface ####################################################################################
    # #################################################################################################################
    def GetChildren(self, parent, children):
        # The view calls this method to find the children of any node in the
        # control. There is an implicit hidden root node, and the top level
        # item(s) should be reported as children of this node. A List view
        # simply provides all items as children of this hidden root. A Tree
        # view adds additional items as children of the other items, as needed,
        # to provide the tree hierarchy.

        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.

        if self.root_entry is None:
            return 0

        if not parent:
            # hidden root
            entry = None
        else:
            entry = self.dvc_item_to_entry(parent)

        childs = self.get_children(entry)
        for child in childs:
            dvc_item = self.entry_to_dvc_item(child)
            children.append(dvc_item)
        return len(children)

    def IsContainer(self, item):
        # Return True if the item has children, False otherwise.

        # The hidden root is a container
        if not item:
            return True

        entry = self.dvc_item_to_entry(item)

        if entry.subentries is None:
            return False

        return True

    def HasContainerColumns(self, item):
        # Retrun Ture, because containers (eg. Struct, Array) should have also values in all columns.
        return True

    def GetParent(self, item):
        # Return the item which is this item's parent.

        if not item:
            entry = None  # Root object
        else:
            entry = self.dvc_item_to_entry(item)

        parent = self.get_parent(entry)
        if parent is None:
            parent_item = dv.NullDataViewItem
        else:
            parent_item = self.entry_to_dvc_item(parent)
        return parent_item

    def GetValue(self, item: dv.DataViewItem, col: int):
        entry = self.dvc_item_to_entry(item)

        return self.get_value(entry, col)

    def SetValue(self, value: ValueFromEditorCtrl, item: dv.DataViewItem, col: int):
        if not isinstance(value, ValueFromEditorCtrl):
            raise ValueError(f"value has the wrong type ({value})")

        entry = self.dvc_item_to_entry(item)
        self.set_value(value.new_obj, entry, col)

        return True

    def GetAttr(self, item, col, attr):
        entry = self.dvc_item_to_entry(item)

        if entry is self.root_entry:
            attr.SetColour("blue")
            attr.SetBold(True)
            return True

        return False


class WxConstructEditor(wx.Panel, ConstructEditor):
    def __init__(
        self,
        parent,
        construct: cs.Construct,
    ):
        wx.Panel.__init__(self, parent)
        self._init_gui()

        ConstructEditor.__init__(self, construct, self._model)

    def _init_gui(self):
        vsizer = wx.BoxSizer(wx.VERTICAL)

        # Create DataViewCtrl
        self._dvc = dv.DataViewCtrl(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            style=dv.DV_VERT_RULES | dv.DV_ROW_LINES,
            name="construct_editor",
        )
        vsizer.Add(self._dvc, 3, wx.EXPAND, 0)

        # Create Model of DataViewCtrl
        self._model = WxConstructEditorModel(self._dvc)
        self._dvc.AssociateModel(self._model)

        # Create InfoBars
        self._parse_error_info_bar = wx.InfoBar(self)
        btn_id = wx.NewIdRef()
        self._parse_error_info_bar.AddButton(btn_id, "Exception Infos")
        self._parse_error_info_bar.Bind(
            wx.EVT_BUTTON, self._parse_error_info_bar_btn_clicked, id=btn_id
        )
        self._parse_error_ex: t.Optional[Exception] = None
        vsizer.Add(self._parse_error_info_bar, 0, wx.EXPAND)

        self._build_error_info_bar = wx.InfoBar(self)
        btn_id = wx.NewIdRef()
        self._build_error_info_bar.AddButton(btn_id, "Exception Infos")
        self._build_error_info_bar.Bind(
            wx.EVT_BUTTON, self._build_error_info_bar_btn_clicked, id=btn_id
        )
        self._build_error_ex: t.Optional[Exception] = None
        vsizer.Add(self._build_error_info_bar, 0, wx.EXPAND)

        # create status bar
        self._status_bar = wx.StatusBar(
            self,
            style=wx.STB_SHOW_TIPS | wx.STB_ELLIPSIZE_END | wx.FULL_REPAINT_ON_RESIZE,
        )
        self._status_bar.SetFieldsCount(2)
        self._status_bar.SetStatusStyles(
            [wx.SB_NORMAL, wx.SB_FLAT]
        )  # remove vertical line after the last field
        self._status_bar.SetStatusWidths([-2, -1])
        vsizer.Add(self._status_bar, 0, wx.ALL | wx.EXPAND, 0)

        self.SetSizer(vsizer)
        self.Layout()

        # Connect Events
        self._dvc.Bind(
            dv.EVT_DATAVIEW_SELECTION_CHANGED,
            self._on_dvc_selection_changed,
            id=wx.ID_ANY,
        )
        self._dvc.Bind(dv.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self._on_dvc_value_changed)
        self._dvc.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self._on_dvc_right_clicked)
        self._dvc.Bind(dv.EVT_DATAVIEW_ITEM_EXPANDED, self._on_dvc_item_expanded)
        self._dvc.Bind(dv.EVT_DATAVIEW_ITEM_COLLAPSED, self._on_dvc_item_collapsed)

        self._dvc_main_window: wx.Window = self._dvc.GetMainWindow()
        self._dvc_main_window.Bind(wx.EVT_MOTION, self._on_dvc_motion)
        self._dvc_main_window.Bind(wx.EVT_KEY_DOWN, self._on_dvc_key_down)
        self._dvc_main_window.Bind(wx.EVT_CHAR, self._on_dvc_char)
        self._last_tooltip: t.Optional[
            t.Tuple[EntryConstruct, ConstructEditorColumn]
        ] = None

    def reload(self):
        """
        Reload the ConstructEditor, while remaining expaned elements and selection.
        """
        try:
            self.Freeze()

            # reload dvc columns
            self._reload_dvc_columns()

            # save selection
            selections = self._dvc.GetSelections()

            # clear the dvc.
            # unfortunately the selection and expanded items get lost... so we have to save and restore it manually
            self._model.Cleared()
            self._refresh_status_bar(None)

            # restore expansion saved in the model itself
            if self._model.root_entry is not None:
                self.restore_expansion_from_model(self._model.root_entry)

            # restore selection
            self._dvc.SetSelections(selections)

        finally:
            self.Thaw()

    def show_parse_error_message(self, msg: t.Optional[str], ex: t.Optional[Exception]):
        """
        Show an message to the user.
        """
        if msg is None:
            self._parse_error_info_bar.Dismiss()
        else:
            self._parse_error_ex = ex
            self._parse_error_info_bar.ShowMessage(msg, wx.ICON_WARNING)

    def show_build_error_message(self, msg: t.Optional[str], ex: t.Optional[Exception]):
        """
        Show an build error message to the user.
        """
        if msg is None:
            self._build_error_info_bar.Dismiss()
        else:
            self._build_error_ex = ex
            self._build_error_info_bar.ShowMessage(msg, wx.ICON_WARNING)

    def show_status(self, path_info: str, bytes_info: str):
        """
        Show an status to the user.
        """
        self._status_bar.SetStatusText(path_info, 0)
        self._status_bar.SetStatusText(bytes_info, 1)

    def get_selected_entry(self) -> t.Optional[EntryConstruct]:
        """
        Get the currently selected entry (or None if nothing is selected).
        """
        item = self._dvc.GetSelection()
        if item.ID is None:
            return None
        return self._model.dvc_item_to_entry(item)

    def select_entry(self, entry: EntryConstruct) -> None:
        """
        Select an entry programmatically.
        """
        dvc_item = self._model.entry_to_dvc_item(entry)
        self._dvc.Select(dvc_item)

        # calling "Select" dont trigger an dv.EVT_DATAVIEW_SELECTION_CHANGED event, so call
        # it manually
        self._on_dvc_selection_changed(None)

    def get_root_obj(self) -> t.Any:
        """
        Get the current root object of the parsed binary.
        """
        return self._model.root_obj

    def expand_entry(self, entry: EntryConstruct):
        """
        Expand an entry.
        """
        dvc_item = self._model.entry_to_dvc_item(entry)
        self._dvc.Expand(dvc_item)

    def collapse_entry(self, entry: EntryConstruct):
        """
        Collapse an entry.
        """
        dvc_item = self._model.entry_to_dvc_item(entry)
        self._dvc.Collapse(dvc_item)

    # Internals ###############################################################
    def _reload_dvc_columns(self):
        """
        Reload the dvc columns
        """
        self._dvc.ClearColumns()

        col = dv.DataViewColumn(
            "Name",
            dv.DataViewTextRenderer(),
            ConstructEditorColumn.Name,
            width=160,
        )
        self._dvc.AppendColumn(col)

        col = dv.DataViewColumn(
            "Type",
            dv.DataViewTextRenderer(),
            ConstructEditorColumn.Type,
            width=90,
        )
        col.Alignment = wx.ALIGN_LEFT
        self._dvc.AppendColumn(col)

        col = dv.DataViewColumn(
            "Value",
            ObjectRenderer(),
            ConstructEditorColumn.Value,
            width=200,
        )
        col.Alignment = wx.ALIGN_LEFT
        self._dvc.AppendColumn(col)

        list_cols = self._get_list_viewed_column_count()
        for list_col in range(list_cols):
            col = dv.DataViewColumn(
                str(list_col),
                dv.DataViewTextRenderer(),
                len(ConstructEditorColumn) + list_col,
            )
            col.Alignment = wx.ALIGN_LEFT
            self._dvc.AppendColumn(col)

        # This prevents flickering in the dvc.
        # The length of the value column has a variable size, even though we
        # have set it to a constant, but it always expands to the end of the
        # visible area. I guess the flickering comes, because at first the
        # fixed size is used and then an Event occures an sets the corret size
        # of the dvc. This Yield forces to process this event.
        wx.Yield()

    def _rename_dvc_columns(self, entry: EntryConstruct):
        """
        Rename the dvc columns
        """
        list_viewed_column_names = self._get_list_viewed_column_names(entry)
        list_viewed_column_offset = len(ConstructEditorColumn)

        for column in range(list_viewed_column_offset, self._dvc.GetColumnCount()):
            dvc_column: dv.DataViewColumn = self._dvc.GetColumn(column)
            list_viewed_column = column - list_viewed_column_offset
            if list_viewed_column < len(list_viewed_column_names):
                dvc_column.SetTitle(list_viewed_column_names[list_viewed_column])
            else:
                dvc_column.SetTitle(str(list_viewed_column))

    def _on_dvc_selection_changed(self, event):
        """
        This method is called, if the selection in the dvc has changed.

        Then the infos of the new selected entry is shown.
        """
        item = self._dvc.GetSelection()
        if item.ID is not None:
            entry = self._model.dvc_item_to_entry(item)
            self._refresh_status_bar(entry)

            self.on_entry_selected.fire(entry)

            self._rename_dvc_columns(entry)

        else:
            self._refresh_status_bar(None)

    def _on_dvc_value_changed(self, event: dv.DataViewEvent):
        """This method is called, if a value in the dvc has changed."""
        if event.Column == ConstructEditorColumn.Value:
            # The `CallAfter` is necessary, because without it the program crashes
            # sporadically, when you edit an value in an EditCtrl and then clicking
            # on another value to close the EditCtrl... Maybe this is because the
            # callbacks may change the root_obj itself. So better do it after this
            # event has completed
            wx.CallAfter(self.on_root_obj_changed.fire, self._model.root_obj)

    def _on_dvc_motion(self, event: wx.MouseEvent):
        # this is a mouse event, so we have to calculate the position of
        # the item where the mouse is manually.
        pos = event.GetPosition()
        pos += self._dvc_main_window.GetPosition()  # correct the dvc header
        item, col = self._dvc.HitTest(pos)
        if item.GetID() is None:
            self._dvc_main_window.SetToolTip("")
            return
        entry = self._model.dvc_item_to_entry(item)

        if col.ModelColumn == ConstructEditorColumn.Name:
            # only set tooltip if the obj changed. this prevents flickering
            if self._last_tooltip != (entry, ConstructEditorColumn.Name):
                self._dvc_main_window.SetToolTip(
                    textwrap.dedent(entry.docs or entry.name).strip()
                )
            self._last_tooltip = (entry, ConstructEditorColumn.Name)
        elif col.ModelColumn == ConstructEditorColumn.Type:
            # only set tooltip if the obj changed. this prevents flickering
            if self._last_tooltip != (entry, ConstructEditorColumn.Type):
                self._dvc_main_window.SetToolTip(str(entry.construct))
            self._last_tooltip = (entry, ConstructEditorColumn.Type)
        else:
            self._dvc_main_window.SetToolTip("")
            self._last_tooltip = None

    def _on_dvc_right_clicked(self, event: dv.DataViewEvent):
        """
        This method is called, the dvc ist right clicked

        Then a context menu is created
        """
        item = event.GetItem()
        entry: t.Optional["EntryConstruct"]
        if item.ID is not None:
            entry = self._model.dvc_item_to_entry(item)
        else:
            entry = None
        self.PopupMenu(WxContextMenu(self, self._model, entry), event.GetPosition())

    def _on_dvc_key_down(self, event: wx.KeyEvent):
        # Ctrl+E
        if event.ControlDown() and event.GetKeyCode() == ord("E"):
            self.expand_all()

        # Ctrl+W
        elif event.ControlDown() and event.GetKeyCode() == ord("W"):
            self.collapse_all()
            self.expand_level(1)  # expand at least the root

        # Ctrl+Z
        elif event.ControlDown() and event.GetKeyCode() == ord("Z"):
            self._model.command_processor.undo()

        # Ctrl+Y
        elif event.ControlDown() and event.GetKeyCode() == ord("Y"):
            self._model.command_processor.redo()

        # Ctrl+C
        elif event.ControlDown() and event.GetKeyCode() == ord("C"):
            selected_entry = self.get_selected_entry()
            if selected_entry is None:
                event.Skip()
                return
            self.copy_entry_value_to_clipboard(selected_entry)

        # Ctrl+V
        elif event.ControlDown() and event.GetKeyCode() == ord("V"):
            selected_entry = self.get_selected_entry()
            if selected_entry is None:
                event.Skip()
                return
            self.paste_entry_value_from_clipboard(selected_entry)

        else:
            event.Skip()

    def _on_dvc_char(self, event: wx.KeyEvent):
        if event.GetUnicodeKey() in (wx.WXK_NONE, wx.WXK_RETURN, wx.WXK_SPACE):
            event.Skip()
            return

        if self._dvc.GetSelectedItemsCount() == 0:
            event.Skip()
            return

        # when any printable key is pressed, the editing should start
        self._dvc.EditItem(
            self._dvc.GetSelection(),
            self._dvc.GetColumn(ConstructEditorColumn.Value),
        )

        # redo the button click, so that the key is passed to edit
        sim = wx.UIActionSimulator()
        sim.KeyDown(event.GetKeyCode())

    def _on_dvc_item_expanded(self, event: dv.DataViewEvent):
        dvc_item = event.GetItem()
        if dvc_item.ID is None:
            return
        entry = self._model.dvc_item_to_entry(dvc_item)
        entry.row_expanded = True

    def _on_dvc_item_collapsed(self, event: dv.DataViewEvent):
        dvc_item = event.GetItem()
        if dvc_item.ID is None:
            return
        entry = self._model.dvc_item_to_entry(dvc_item)
        entry.row_expanded = False

    def _put_to_clipboard(self, txt: str):
        """
        Put text to the clipboard.
        """
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(txt))
            wx.TheClipboard.Close()

    def _get_from_clipboard(self):
        """
        Get text from the clipboard.
        """
        # get data from clipboard
        if not wx.TheClipboard.Open():
            wx.MessageBox("Can't open the clipboard", "Warning")
            return None
        clipboard = wx.TextDataObject()
        wx.TheClipboard.GetData(clipboard)
        wx.TheClipboard.Close()
        txt: str = clipboard.GetText()
        return txt

    def _parse_error_info_bar_btn_clicked(self, event):
        if self._parse_error_ex is None:
            return

        dial = WxExceptionDialog(None, "Parse error", self._parse_error_ex)
        dial.ShowModal()

    def _build_error_info_bar_btn_clicked(self, event):
        if self._build_error_ex is None:
            return

        dial = WxExceptionDialog(None, "Build error", self._build_error_ex)
        dial.ShowModal()
