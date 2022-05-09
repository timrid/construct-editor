# -*- coding: utf-8 -*-
import enum
from typing import Any, Callable, Dict, List, Optional
import typing as t
import construct as cs
import wx
import wx.dataview as dv
from construct_editor.helper import CallbackList
import textwrap

from construct_editor.helper.preprocessor import include_metadata
from construct_editor.helper.wrapper import (
    ObjEditorMixin,
    EntryConstruct,
    create_entry_from_construct,
    get_gui_metadata,
    add_gui_metadata,
)


class RootObjChangedCallbackList(CallbackList[Callable[[Any], None]]):
    def fire(self, root_obj: Any):
        for listener in self:
            listener(root_obj)


class EntrySelectedCallbackList(CallbackList[Callable[[EntryConstruct], None]]):
    def fire(self, entry: EntryConstruct):
        for listener in self:
            listener(entry)


# #####################################################################################################################
# Object Renderer #####################################################################################################
# #####################################################################################################################
class ObjectRenderer(dv.DataViewCustomRenderer):
    def __init__(self):
        super().__init__(varianttype="PyObject", mode=dv.DATAVIEW_CELL_EDITABLE)
        self.entry: Optional[EntryConstruct] = None
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

    def CreateEditorCtrl(self, parent, labelRect: wx.Rect, value: EntryConstruct):
        editor: ObjEditorMixin = value.create_obj_panel(parent)
        editor.SetPosition(labelRect.Position)
        editor.SetSize(labelRect.Size)
        return editor

    def GetValueFromEditorCtrl(self, editor: ObjEditorMixin):
        new_obj = editor.get_new_obj()
        # new_obj is passed in a dict, because subtypes of `int` (eg. `IntEnum`)
        # and `str` (eg. `cs.EnumIntegerString`) are converted to its base type
        # by the DVC...
        return {"new_obj": new_obj}


# #####################################################################################################################
# Context Menu ########################################################################################################
# #####################################################################################################################
class ContextMenu(wx.Menu):
    def __init__(
        self,
        parent: "ConstructEditor",
        model: "ConstructEditorModel",
        entry: Optional["EntryConstruct"],
    ):
        super(ContextMenu, self).__init__()
        self.parent = parent
        self.model = model

        item: wx.MenuItem = self.Append(wx.ID_COPY, "Copy\tCtrl+C")
        # self.Bind(wx.EVT_MENU, self.on_copy, id=item.Id)
        item.Enable(False)

        item: wx.MenuItem = self.Append(wx.ID_PASTE, "Paste\tCtrl+V")
        # self.Bind(wx.EVT_MENU, self.on_paste, id=item.Id)
        item.Enable(False)  # TODO:

        self.AppendSeparator()

        item: wx.MenuItem = self.Append(wx.ID_UNDO, "Undo\tCtrl+Z")
        self.Bind(
            wx.EVT_MENU,
            lambda event: self.model.command_processor.Undo(),
            id=item.Id,
        )
        item.Enable(self.model.command_processor.CanUndo())

        item: wx.MenuItem = self.Append(wx.ID_REDO, "Redo\tCtrl+Y")
        self.Bind(
            wx.EVT_MENU,
            lambda event: self.model.command_processor.Redo(),
            id=item.Id,
        )
        item.Enable(self.model.command_processor.CanRedo())

        self.AppendSeparator()

        item: wx.MenuItem = self.AppendCheckItem(wx.ID_ANY, "Hide Protected")
        self.Bind(wx.EVT_MENU, self.on_hide_protected, id=item.Id)
        item.Check(self.parent.hide_protected)
        self.hide_protected_mi = item

        self.AppendSeparator()

        item: wx.MenuItem = self.AppendRadioItem(wx.ID_ANY, "Dec")
        self.Bind(wx.EVT_MENU, self.on_intformat_dec, id=item.Id)
        self.intformat_dec_mi = item

        item: wx.MenuItem = self.AppendRadioItem(wx.ID_ANY, "Hex")
        self.Bind(wx.EVT_MENU, self.on_intformat_hex, id=item.Id)
        self.intformat_hex_mi = item

        if self.model.integer_format is IntegerFormat.Hex:
            self.intformat_hex_mi.Check(True)
        else:
            self.intformat_dec_mi.Check(True)

        # Add List with all currently shown list viewed items
        if len(model.list_viewed_entries) > 0:
            self.AppendSeparator()

            submenu = wx.Menu()
            self.submenu_map: Dict[Any, EntryConstruct] = {}
            for e in model.list_viewed_entries:
                name = ".".join(e.path)
                item: wx.MenuItem = submenu.AppendCheckItem(wx.ID_ANY, name)
                self.submenu_map[item.GetId()] = e
                self.Bind(wx.EVT_MENU, self.on_remove_list_viewed_item, item)
                item.Check(True)

            self.AppendSubMenu(submenu, "List Viewed Items")

        # Add additional items for this entry
        if entry is not None:
            entry.modify_context_menu(self)

    def on_hide_protected(self, event):
        checked = self.hide_protected_mi.IsChecked()
        self.parent.hide_protected = checked
        self.parent.reload()

    def on_intformat_dec(self, event: wx.CommandEvent):
        self.intformat_dec_mi.Check(True)
        self.model.integer_format = IntegerFormat.Dec
        self.parent.reload()
        event.Skip()

    def on_intformat_hex(self, event: wx.CommandEvent):
        self.intformat_hex_mi.Check(True)
        self.model.integer_format = IntegerFormat.Hex
        self.parent.reload()
        event.Skip()

    def on_remove_list_viewed_item(self, event: wx.CommandEvent):
        entry = self.submenu_map[event.GetId()]
        self.model.list_viewed_entries.remove(entry)
        self.parent.reload()


# #####################################################################################################################
# Construct Editor Model ##############################################################################################
# #####################################################################################################################


class IntegerFormat(enum.Enum):
    Dec = enum.auto()
    Hex = enum.auto()


class ConstructEditorColumn(enum.IntEnum):
    Name = 0
    Type = 1
    Value = 2


class ConstructEditorModel(dv.PyDataViewModel):
    """
    This model acts as a bridge between the DataViewCtrl and the dataclasses.
    This model provides these data columns:
        0. Name: string
        1. Type: string
        2. Value: string
    """

    def __init__(self, dvc: dv.DataViewCtrl):
        dv.PyDataViewModel.__init__(self)
        self.dvc = dvc
        self.root_entry: Optional["EntryConstruct"] = None
        self.root_obj: Optional[Any] = None

        self.hide_protected = True

        # List with all entries that have the list view enabled
        self.list_viewed_entries: List["EntryConstruct"] = []

        # The PyDataViewModel derives from both DataViewModel and from
        # DataViewItemObjectMapper, which has methods that help associate
        # data view items with Python objects. Normally a dictionary is used
        # so any Python object can be used as data nodes. If the data nodes
        # are weak-referencable then the objmapper can use a
        # WeakValueDictionary instead.
        # self.UseWeakRefs(True)  # weak refs are slower when creating a large number of items

        self.command_processor = wx.CommandProcessor()

        self.integer_format = IntegerFormat.Dec

    def get_column_count(self):
        """Get the column count"""
        return 3

    def get_column_name(self, selected_item, col):
        """Get the name of the column. The column name depends on the selected item"""
        entry = self.ItemToObject(selected_item)
        if not isinstance(entry, EntryConstruct):
            raise ValueError(f"{repr(entry)} is no valid entry")

        flat_subentry_list: List["EntryConstruct"] = []
        entry.create_flat_subentry_list(flat_subentry_list)

        return ".".join(flat_subentry_list[col].path)

    # #################################################################################################################
    # dv.PyDataViewModel Interface ####################################################################################
    # #################################################################################################################
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
            entry = self.root_entry
            if entry.dvc_item is None:
                item = self.ObjectToItem(entry)
                entry.dvc_item = item
            children.append(entry.dvc_item)
            return 1

        parent_entry = self.ItemToObject(parent)
        if not isinstance(parent_entry, EntryConstruct):
            raise ValueError(f"{repr(parent_entry)} is no valid entry")

        if parent_entry.subentries is not None:
            for entry in parent_entry.subentries:
                name = entry.name
                if (self.hide_protected == True) and (
                    name.startswith("_") or name == ""
                ):
                    continue
                if entry.dvc_item is None:
                    item = self.ObjectToItem(entry)
                    entry.dvc_item = item
                children.append(entry.dvc_item)
        return len(children)

    def IsContainer(self, item):
        # Return True if the item has children, False otherwise.

        # The hidden root is a container
        if not item:
            return True

        # check if the entry is a container
        entry: EntryConstruct = self.ItemToObject(item)
        return entry.subentries is not None

    def HasContainerColumns(self, item):
        # True zurückgeben, damit in Containern auch in allen Spalten Werte angezeigt werden
        return True

    def GetParent(self, item):
        # Return the item which is this item's parent.

        # Root object
        if not item:
            return dv.NullDataViewItem

        # return parent of entry
        entry: EntryConstruct = self.ItemToObject(item)
        return entry.get_parent_dvc_item()

    def GetValue(self, item: dv.DataViewItem, col: int):
        # Return the value to be displayed for this item and column.

        entry = self.ItemToObject(item)
        if not isinstance(entry, EntryConstruct):
            raise ValueError(f"{repr(entry)} is no valid entry")

        if col == ConstructEditorColumn.Name:
            return entry.name
        if col == ConstructEditorColumn.Type:
            return entry.typ_str
        if col == ConstructEditorColumn.Value:
            return entry

        if (entry.parent is None) or (entry.parent not in self.list_viewed_entries):
            return ""

        # flatten the hierarchical structure to a list
        col = col - len(ConstructEditorColumn)

        flat_subentry_list: List["EntryConstruct"] = []
        entry.create_flat_subentry_list(flat_subentry_list)
        if len(flat_subentry_list) > col:
            return flat_subentry_list[col].obj_str
        else:
            return ""

    def SetValue(self, value: Any, item: dv.DataViewItem, col: int):
        if col != ConstructEditorColumn.Value:
            raise ValueError(f"col={col} cannot be modified")

        entry: EntryConstruct = self.ItemToObject(item)
        if not isinstance(entry, EntryConstruct):
            raise ValueError(f"{repr(entry)} is no valid entry")

        # new_obj is passed in a dict, because subtypes of `int` (eg. `IntEnum`)
        # and `str` (eg. `cs.EnumIntegerString`) are converted to its base type
        # by the DVC...
        new_obj = value["new_obj"]

        # get the current object
        obj = entry.obj

        # link the metadata from the current object to the new one
        metadata = get_gui_metadata(obj)
        if metadata is not None:
            new_obj = add_gui_metadata(new_obj, metadata)

        model = self

        class Cmd(wx.Command):
            def __init__(self):
                super().__init__(True, f"Value '{entry.path[-1]}' changed")

            def Do(self):
                self._obj_backup = obj
                entry.obj = new_obj
                model.ItemChanged(entry.dvc_item)
                return True

            def Undo(self):
                entry.obj = self._obj_backup
                model.ItemChanged(entry.dvc_item)
                return True

        self.command_processor.Submit(Cmd())
        return True

    def GetAttr(self, item, col, attr):
        entry = self.ItemToObject(item)

        if entry is self.root_entry:
            attr.SetColour("blue")
            attr.SetBold(True)
            return True

        return False


# #####################################################################################################################
# Construct Editor ####################################################################################################
# #####################################################################################################################
class ConstructEditor(wx.Panel):
    def __init__(
        self,
        parent,
        construct: cs.Construct,
    ):
        super().__init__(parent)

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
        self._model = ConstructEditorModel(self._dvc)
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
        self._dvc.Bind(dv.EVT_DATAVIEW_ITEM_EXPANDED, self._on_dvc_item_expanded)
        self._dvc.Bind(dv.EVT_DATAVIEW_ITEM_COLLAPSED, self._on_dvc_item_collapsed)

        self._dvc_main_window: wx.Window = self._dvc.GetMainWindow()
        self._dvc_main_window.Bind(wx.EVT_MOTION, self._on_dvc_motion)
        self._dvc_main_window.Bind(wx.EVT_KEY_DOWN, self._on_dvc_key_down)
        self._last_tooltip: Optional[
            t.Tuple[EntryConstruct, ConstructEditorColumn]
        ] = None

        self._dvc_header = self._dvc.FindWindowByName("wxMSWHeaderCtrl")
        if self._dvc_header is not None:
            self._dvc_header.Bind(wx.EVT_MOTION, self._on_dvc_header_motion)

        self.on_entry_selected = EntrySelectedCallbackList()
        self.on_root_obj_changed = RootObjChangedCallbackList()
        self.construct = construct

    def reload(self):
        """Reload the ConstructEditor, while remaining expaned elements and selection"""
        try:
            self.Freeze()

            # reload dvc columns
            self._reload_dvc_columns()

            # save selection
            selections = self._dvc.GetSelections()

            # clear the dvc.
            # unfortunately the selection and expanded items get lost... so we have to save and restore it manually
            self._model.Cleared()
            self._clear_status_bar()

            # expand everything
            if self._model.root_entry is not None:
                self._model.root_entry.dvc_item_restore_expansion()

            # restore selection
            self._dvc.SetSelections(selections)

        finally:
            self.Thaw()

    def parse(self, binary: bytes, **contextkw: Any):
        """Parse binary data to struct."""
        try:
            self._model.root_obj = self._construct.parse(binary, **contextkw)
            self._parse_error_info_bar.Dismiss()
        except Exception as e:
            self._parse_error_info_bar.ShowMessage(
                f"Error while parsing binary data: {type(e).__name__}\n{str(e)}",
                wx.ICON_WARNING,
            )
            self._model.root_obj = None
        # clear all commands, when new data is set from external
        self._model.command_processor.ClearCommands()
        self.reload()

    def build(self, **contextkw: Any) -> bytes:
        """Build binary data from struct."""
        try:
            binary = self._construct.build(self.root_obj, **contextkw)
            self._build_error_info_bar.Dismiss()
        except Exception as e:
            self._build_error_info_bar.ShowMessage(
                f"Error while building binary data: {type(e).__name__}\n{str(e)}",
                wx.ICON_WARNING,
            )
            raise e

        # parse the build binary, so that constructs that parses from nothing are shown correctly (eg. cs.Peek)
        wx.CallAfter(lambda: self.parse(binary, **contextkw))

        return binary

    # Property: construct #####################################################
    @property
    def construct(self) -> cs.Construct:
        """Construct that is used for displaying."""
        return self._construct

    @construct.setter
    def construct(self, val: cs.Construct):
        # add root name, is none is available
        if val.name is None:
            val = "root" / val

        # modify the copied construct, so that each item also includes metadata for the GUI
        self._construct = include_metadata(val)

        # create entry from the construct
        self._model.root_entry = create_entry_from_construct(
            self._model, None, self._construct, None, ""
        )

        self._model.list_viewed_entries.clear()

    # Property: root_obj ######################################################
    @property
    def root_obj(self) -> Any:
        return self._model.root_obj

    # Property: hide_protected ################################################
    @property
    def hide_protected(self) -> bool:
        """
        Hide protected members.
        A protected member starts with an undescore (_)
        """
        return self._model.hide_protected

    @hide_protected.setter
    def hide_protected(self, value: bool):
        self._model.hide_protected = value
        self.reload()

    # expand_entry ############################################################
    def expand_entry(self, entry: EntryConstruct):
        self._dvc.Expand(entry.dvc_item)

    # expand_children #########################################################
    def expand_children(self, entry: EntryConstruct):
        if entry.subentries is not None:
            if entry.dvc_item is not None:
                self._dvc.Expand(entry.dvc_item)
            for sub_entry in entry.subentries:
                self.expand_children(sub_entry)

    # expand_all ##############################################################
    def expand_all(self):
        """
        Expand all Entries
        """
        if self._model.root_entry:
            self.expand_children(self._model.root_entry)

    # expand_level ############################################################
    def expand_level(self, level: int):
        """
        Expand all Entries to Level ... (0=root level)
        """

        def dvc_expand(entry: EntryConstruct, current_level: int):
            subentries = entry.subentries
            dvc_item = entry.dvc_item
            if subentries is not None:
                if dvc_item is not None:
                    self._dvc.Expand(dvc_item)
                if current_level < level:
                    for sub_entry in subentries:
                        dvc_expand(sub_entry, current_level + 1)

        if self._model.root_entry:
            dvc_expand(self._model.root_entry, 1)

    # collapse_all ############################################################
    def collapse_children(self, entry: EntryConstruct):
        subentries = entry.subentries
        dvc_item = entry.dvc_item
        if subentries is not None:
            for sub_entry in subentries:
                self.collapse_children(sub_entry)
            if dvc_item is not None:
                self._dvc.Collapse(dvc_item)

    # collapse_all ############################################################
    def collapse_all(self):
        """
        Collapse all Entries
        """
        if self._model.root_entry:
            self.collapse_children(self._model.root_entry)

        # expand the root entry again
        self.expand_level(1)

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

        flat_list: List["EntryConstruct"] = []
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
            self._clear_status_bar()

    def _refresh_status_bar(self, entry: EntryConstruct):
        self._status_bar.SetStatusText(".".join(entry.path), 0)
        bytes_info = ""
        stream_infos = entry.get_stream_infos()

        # Show byte range only when no nested streams are used
        if len(stream_infos) == 1:
            byte_range = stream_infos[0].byte_range
            start = byte_range[0]
            end = byte_range[1] - 1
            size = end - start + 1
            if size > 0:
                bytes_info = f"Bytes: {start:n}-{end:n} ({size:n})"
        self._status_bar.SetStatusText(bytes_info, 1)

    def _clear_status_bar(self):
        self._status_bar.SetStatusText("", 0)
        self._status_bar.SetStatusText("", 1)

    def _on_dvc_value_changed(self, event: dv.DataViewEvent):
        """This method is called, if a value in the dvc has changed."""
        if event.Column == ConstructEditorColumn.Value:
            self.on_root_obj_changed.fire(self._model.root_obj)

    def _on_dvc_motion(self, event: wx.MouseEvent):
        # this is a mouse event, so we have to calculate the position of
        # the item where the mouse is manually.
        pos = event.GetPosition()
        pos += (0, self._dvc_header.Size.Height)  # correct the dvc header
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

    def _on_dvc_header_motion(self, event: wx.MouseEvent):
        event.Skip()  # TODO: Create Tooltip for DVC-Header

    def _on_dvc_right_clicked(self, event: dv.DataViewEvent):
        """
        This method is called, the dvc ist right clicked

        Then a context menu is created
        """
        item = event.GetItem()
        entry: Optional["EntryConstruct"]
        if item.ID is not None:
            entry = self._model.ItemToObject(item)
        else:
            entry = None
        self.PopupMenu(ContextMenu(self, self._model, entry), event.GetPosition())

    def _on_dvc_key_down(self, event: wx.KeyEvent):
        # Ctrl+E
        if event.ControlDown() and event.GetKeyCode() == ord("E"):
            self.expand_all()

        # Ctrl+W
        if event.ControlDown() and event.GetKeyCode() == ord("W"):
            self.collapse_all()

        # Ctrl+Z
        if event.ControlDown() and event.GetKeyCode() == ord("Z"):
            self._model.command_processor.Undo()

        # Ctrl+Y
        elif event.ControlDown() and event.GetKeyCode() == ord("Y"):
            self._model.command_processor.Redo()

        # Ctrl+C
        elif event.ControlDown() and event.GetKeyCode() == ord("C"):
            pass  # TODO

        # Ctrl+V
        elif event.ControlDown() and event.GetKeyCode() == ord("V"):
            pass  # TODO

        else:
            event.Skip()

    def _on_dvc_item_expanded(self, event: dv.DataViewEvent):
        item = event.GetItem()
        if item.ID is None:
            return
        entry: EntryConstruct = self._model.ItemToObject(item)
        entry.dvc_item_expanded = True

    def _on_dvc_item_collapsed(self, event: dv.DataViewEvent):
        item = event.GetItem()
        if item.ID is None:
            return
        entry: EntryConstruct = self._model.ItemToObject(item)
        entry.dvc_item_expanded = False
