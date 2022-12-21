# -*- coding: utf-8 -*-

import textwrap
import typing as t

import construct as cs
import wx
import wx.dataview as dv

from construct_editor.core.editor import ConstructEditor
from construct_editor.core.entries import EntryConstruct
from construct_editor.core.model import ConstructEditorColumn, ConstructEditorModel
from construct_editor.widgets.wx.wx_obj_editors import WxObjEditor, create_obj_editor
import dataclasses


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
        super().__init__(varianttype="PyObject", mode=dv.DATAVIEW_CELL_EDITABLE)
        self.entry: t.Optional[EntryConstruct] = None
        self.EnableEllipsize(wx.ELLIPSIZE_END)

    def SetValue(self, value):
        self.entry = value
        return True

    def GetValue(self):
        return self.entry

    def GetSize(self):
        # Return the size needed to display the value.  The renderer
        # has a helper function we can use for measuring text that is
        # aware of any custom attributes that may have been set for
        # this item.
        obj_str = self.entry.obj_str if self.entry else ""
        size = self.GetTextExtent(obj_str)
        size += (2, 2)
        return size

    def Render(self, rect, dc, state):
        # And then finish up with this helper function that draws the
        # text for us, dealing with alignment, font and color
        # attributes, etc.
        obj_str = self.entry.obj_str if self.entry else ""
        self.RenderText(
            obj_str, 0, rect, dc, state  # x-offset  # wxDataViewCellRenderState flags
        )
        return True

    def ActivateCell(self, rect, model, item, col, mouseEvent):
        return False

    # The HasEditorCtrl, CreateEditorCtrl and GetValueFromEditorCtrl
    # methods need to be implemented if this renderer is going to
    # support in-place editing of the cell value, otherwise they can
    # be omitted.

    def HasEditorCtrl(self):
        return True

    def CreateEditorCtrl(
        self, parent, labelRect: wx.Rect, value: EntryConstruct
    ) -> WxObjEditor:
        editor_settings = value.obj_editor_settings
        editor: WxObjEditor = create_obj_editor(parent, editor_settings)
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
    # ConstructEditorModel Interface ##################################################################################
    # #################################################################################################################
    def on_value_changed(self, entry: "EntryConstruct"):
        dvc_item = self._entry_to_dvc_item(entry)
        self.ItemChanged(dvc_item)

    # #################################################################################################################
    # dv.PyDataViewModel Interface ####################################################################################
    # #################################################################################################################

    def _dvc_item_to_entry(self, dvc_item: dv.DataViewItem) -> EntryConstruct:
        entry = self.ItemToObject(dvc_item)
        if not isinstance(entry, EntryConstruct):
            raise ValueError(f"{repr(entry)} is no valid entry")
        return entry

    def _entry_to_dvc_item(self, entry: EntryConstruct) -> dv.DataViewItem:
        visible_row_entry = entry.get_visible_row_entry()
        if visible_row_entry is None:
            return dv.NullDataViewItem
        dvc_item = self.ObjectToItem(visible_row_entry)
        return dvc_item

    def GetColumnCount(self):
        # Report how many columns this model provides data for.
        return self.get_column_count()

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
            entry = self._dvc_item_to_entry(parent)

        childs = self.get_children(entry)
        for child in childs:
            dvc_item = self._entry_to_dvc_item(child)
            # dvc_item = self.ObjectToItem(child)
            children.append(dvc_item)
        return len(children)

    def IsContainer(self, item):
        # Return True if the item has children, False otherwise.

        # The hidden root is a container
        if not item:
            return True

        entry = self._dvc_item_to_entry(item)

        if entry.subentries is None:
            return False

        return True

    def HasContainerColumns(self, item):
        # True zurückgeben, damit in Containern auch in allen Spalten Werte angezeigt werden
        return True

    def GetParent(self, item):
        # Return the item which is this item's parent.

        if not item:
            entry = None  # Root object
        else:
            entry = self._dvc_item_to_entry(item)

        parent = self.get_parent(entry)
        if parent is None:
            parent_item = dv.NullDataViewItem
        else:
            parent_item = self._entry_to_dvc_item(parent)
        return parent_item

    def GetValue(self, item: dv.DataViewItem, col: int):
        entry = self._dvc_item_to_entry(item)

        return self.get_value(entry, col)

    def SetValue(self, value: ValueFromEditorCtrl, item: dv.DataViewItem, col: int):
        if not isinstance(value, ValueFromEditorCtrl):
            raise ValueError(f"value has the wrong type ({value})")

        entry = self._dvc_item_to_entry(item)
        self.set_value(value.new_obj, entry, col)

        return True

    def GetAttr(self, item, col, attr):
        entry = self._dvc_item_to_entry(item)

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
        vsizer.Add(self._parse_error_info_bar, 0, wx.EXPAND)

        self._build_error_info_bar = wx.InfoBar(self)
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
        # self._dvc.Bind(dv.EVT_DATAVIEW_ITEM_EXPANDED, self._on_dvc_item_expanded)# TODO (MUST): implement this!
        # self._dvc.Bind(dv.EVT_DATAVIEW_ITEM_COLLAPSED, self._on_dvc_item_collapsed)# TODO (MUST): implement this!

        self._dvc_main_window: wx.Window = self._dvc.GetMainWindow()
        self._dvc_main_window.Bind(wx.EVT_MOTION, self._on_dvc_motion)
        self._dvc_main_window.Bind(wx.EVT_KEY_DOWN, self._on_dvc_key_down)
        self._dvc_main_window.Bind(wx.EVT_CHAR, self._on_dvc_char)
        self._last_tooltip: t.Optional[
            t.Tuple[EntryConstruct, ConstructEditorColumn]
        ] = None

    def reload(self):
        """
        Reload the ConstructEditor, while remaining expaned elements and selection
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

            # TODO (MUST): implement this!
            # # expand everything
            # if self._model.root_entry is not None:
            #     self._model.root_entry.dvc_item_restore_expansion()

            # restore selection
            self._dvc.SetSelections(selections)

        finally:
            self.Thaw()

    def show_parse_error_message(self, msg: t.Optional[str]):
        """
        Show an message to the user.
        """
        if msg is None:
            self._parse_error_info_bar.Dismiss()
        else:
            self._parse_error_info_bar.ShowMessage(msg, wx.ICON_WARNING)

    def show_build_error_message(self, msg: t.Optional[str]):
        """
        Show an build error message to the user.
        """
        if msg is None:
            self._build_error_info_bar.Dismiss()
        else:
            self._build_error_info_bar.ShowMessage(msg, wx.ICON_WARNING)

    def show_status(self, path_info: str, bytes_info: str):
        """
        Show an status to the user.
        """
        self._status_bar.SetStatusText(path_info, 0)
        self._status_bar.SetStatusText(bytes_info, 1)

    def get_root_obj(self) -> t.Any:
        """
        Get the current root object of the parsed binary.
        """
        return self._model.root_obj

    # # expand_entry ############################################################
    # def expand_entry(self, entry: EntryConstruct):
    #     self._dvc.Expand(entry.dvc_item)

    # # expand_children #########################################################
    # def expand_children(self, entry: EntryConstruct):
    #     if entry.subentries is not None:
    #         if entry.dvc_item is not None:
    #             self._dvc.Expand(entry.dvc_item)
    #         for sub_entry in entry.subentries:
    #             self.expand_children(sub_entry)

    # # expand_all ##############################################################
    # def expand_all(self):
    #     """
    #     Expand all Entries
    #     """
    #     if self._model.root_entry:
    #         self.expand_children(self._model.root_entry)

    # # expand_level ############################################################
    # def expand_level(self, level: int):
    #     """
    #     Expand all Entries to Level ... (0=root level)
    #     """

    #     def dvc_expand(entry: EntryConstruct, current_level: int):
    #         subentries = entry.subentries
    #         dvc_item = entry.dvc_item
    #         if subentries is not None:
    #             if dvc_item is not None:
    #                 self._dvc.Expand(dvc_item)
    #             if current_level < level:
    #                 for sub_entry in subentries:
    #                     dvc_expand(sub_entry, current_level + 1)

    #     if self._model.root_entry:
    #         dvc_expand(self._model.root_entry, 1)

    # # collapse_all ############################################################
    # def collapse_children(self, entry: EntryConstruct):
    #     subentries = entry.subentries
    #     dvc_item = entry.dvc_item
    #     if subentries is not None:
    #         for sub_entry in subentries:
    #             self.collapse_children(sub_entry)
    #         if dvc_item is not None:
    #             self._dvc.Collapse(dvc_item)

    # # collapse_all ############################################################
    # def collapse_all(self):
    #     """
    #     Collapse all Entries
    #     """
    #     if self._model.root_entry:
    #         self.collapse_children(self._model.root_entry)

    #     # expand the root entry again
    #     self.expand_level(1)

    # Internals ###############################################################
    def _reload_dvc_columns(self):
        """Reload the dvc columns"""
        self._dvc.ClearColumns()

        self._dvc.AppendTextColumn("Name", ConstructEditorColumn.Name, width=160)
        self._dvc.AppendTextColumn("Type", ConstructEditorColumn.Type, width=90)
        # self._dvc.AppendTextColumn("Value", ConstructEditorColumn.Value, width=200)

        renderer = ObjectRenderer()
        col = dv.DataViewColumn(
            "Value", renderer, ConstructEditorColumn.Value, width=200
        )
        col.Alignment = wx.ALIGN_LEFT
        self._dvc.AppendColumn(col)

        list_cols = 0
        for list_viewed_entry in self._model.list_viewed_entries:
            if list_viewed_entry.subentries is not None:
                for subentry in list_viewed_entry.subentries:
                    flat_list = []
                    subentry.create_flat_subentry_list(flat_list)
                    list_cols = max(list_cols, len(flat_list))

        for list_col in range(list_cols):
            self._dvc.AppendTextColumn(
                str(list_col), len(ConstructEditorColumn) + list_col
            )

    def _rename_dvc_columns(self, entry: EntryConstruct):
        """Rename the dvc columns"""

        flat_list: t.List["EntryConstruct"] = []
        if (entry.parent is not None) and (
            entry.parent in self._model.list_viewed_entries
        ):
            entry.create_flat_subentry_list(flat_list)

        list_cols = self._dvc.GetColumnCount() - len(ConstructEditorColumn)
        for list_col in range(list_cols):
            dvc_column: dv.DataViewColumn = self._dvc.GetColumn(
                len(ConstructEditorColumn) + list_col
            )
            if list_col < len(flat_list):
                path = flat_list[list_col].path
                path = path[len(entry.path) :]  # remove the path from the parent
                dvc_column.SetTitle(".".join(path))
            else:
                dvc_column.SetTitle(str(list_col))

    def _on_dvc_selection_changed(self, event):
        """
        This method is called, if the selection in the dvc has changed.

        Then the infos of the new selected entry is shown.
        """
        item = self._dvc.GetSelection()
        if item.ID is not None:
            entry: EntryConstruct = self._model.ItemToObject(item)
            self._refresh_status_bar(entry)

            self.on_entry_selected.fire(entry)

            self._rename_dvc_columns(entry)

        else:
            self._refresh_status_bar(None)

    def _on_dvc_value_changed(self, event: dv.DataViewEvent):
        """This method is called, if a value in the dvc has changed."""
        if event.Column == ConstructEditorColumn.Value:
            self.on_root_obj_changed.fire(self._model.root_obj)

    def _on_dvc_motion(self, event: wx.MouseEvent):
        # this is a mouse event, so we have to calculate the position of
        # the item where the mouse is manually.
        pos = event.GetPosition()
        pos += self._dvc_main_window.GetPosition()  # correct the dvc header
        item, col = self._dvc.HitTest(pos)
        if item.GetID() is None:
            self._dvc_main_window.SetToolTip("")
            return
        entry: EntryConstruct = self._model.ItemToObject(item)

        if col.ModelColumn == ConstructEditorColumn.Name:
            # only set tooltip if the obj changed. this prevents flickering
            if self._last_tooltip != (entry, ConstructEditorColumn.Name):
                self._dvc_main_window.SetToolTip(textwrap.dedent(entry.docs).strip())
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
            entry = self._model.ItemToObject(item)
        else:
            entry = None
        # TODO (MUST): implement this!
        # self.PopupMenu(ContextMenu(self, self._model, entry), event.GetPosition())

    def _on_dvc_key_down(self, event: wx.KeyEvent):
        # Ctrl+E
        if event.ControlDown() and event.GetKeyCode() == ord("E"):
            # TODO (MUST): implement this!
            # self.expand_all()
            pass

        # Ctrl+W
        if event.ControlDown() and event.GetKeyCode() == ord("W"):
            # TODO (MUST): implement this!
            # self.collapse_all()
            pass

        # Ctrl+Z
        if event.ControlDown() and event.GetKeyCode() == ord("Z"):
            self._model.command_processor.undo()

        # Ctrl+Y
        elif event.ControlDown() and event.GetKeyCode() == ord("Y"):
            self._model.command_processor.redo()

        # Ctrl+C
        elif event.ControlDown() and event.GetKeyCode() == ord("C"):
            pass  # TODO

        # Ctrl+V
        elif event.ControlDown() and event.GetKeyCode() == ord("V"):
            pass  # TODO

        else:
            event.Skip()

    def _on_dvc_char(self, event: wx.KeyEvent):
        if event.GetUnicodeKey() in (wx.WXK_NONE, wx.WXK_RETURN):
            event.Skip()
            return

        # when any printable key is pressed, the editing should start
        self._dvc.EditItem(
            self._dvc.GetSelection(),
            self._dvc.GetColumn(ConstructEditorColumn.Value),
        )

        sim = wx.UIActionSimulator()
        sim.KeyDown(event.GetKeyCode())

    # def _on_dvc_item_expanded(self, event: dv.DataViewEvent):
    #     item = event.GetItem()
    #     if item.ID is None:
    #         return
    #     entry: EntryConstruct = self._model.ItemToObject(item)
    #     entry.dvc_item_expanded = True

    # def _on_dvc_item_collapsed(self, event: dv.DataViewEvent):
    #     item = event.GetItem()
    #     if item.ID is None:
    #         return
    #     entry: EntryConstruct = self._model.ItemToObject(item)
    #     entry.dvc_item_expanded = False
