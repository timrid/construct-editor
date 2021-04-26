# -*- coding: utf-8 -*-
# GUI File aus "wxFormBuilder" importieren
import enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

import construct as cs
import construct_typed as cst
import wx
import wx.dataview as dv
import dataclasses
from construct_editor.helper import CallbackList

from construct_editor.helper.preprocessor import get_gui_metadata, include_metadata
from construct_editor.helper.wrapper import (
    ObjPanel_Empty,
    EntryConstruct,
    create_entry_from_construct,
)


class RootObjChangedCallbackList(CallbackList[Callable[[Any], None]]):
    def fire(self, root_obj: Any):
        for listener in self:
            listener(root_obj)


class EntrySelectedCallbackList(
    CallbackList[Callable[[Optional[int], Optional[int]], None]]
):
    def fire(self, start_idx: Optional[int], end_idx: Optional[int]):
        for listener in self:
            listener(start_idx, end_idx)


# #####################################################################################################################
# Entry Details Viewer ################################################################################################
# #####################################################################################################################
class EntryDetailsViewer(wx.Panel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        vsizer = wx.BoxSizer(wx.VERTICAL)

        # Name
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(
            self, wx.ID_ANY, "Name:", wx.DefaultPosition, wx.Size(50, -1), 0
        )
        hsizer.Add(label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.name_txt = wx.TextCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.Size(-1, -1),
            wx.TE_READONLY,
        )
        hsizer.Add(self.name_txt, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        vsizer.Add(hsizer, 0, wx.EXPAND, 5)

        # Type
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(
            self, wx.ID_ANY, "Type:", wx.DefaultPosition, wx.Size(50, -1), 0
        )
        hsizer.Add(label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.type_txt = wx.TextCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.Size(-1, -1),
            wx.TE_READONLY,
        )
        hsizer.Add(self.type_txt, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        # Offset
        label = wx.StaticText(
            self, wx.ID_ANY, "Offset:", wx.DefaultPosition, wx.Size(-1, -1), 0
        )
        hsizer.Add(label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.offset_txt = wx.TextCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.Size(100, -1),
            wx.TE_READONLY,
        )
        hsizer.Add(self.offset_txt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        # Length
        label = wx.StaticText(
            self, wx.ID_ANY, "Length:", wx.DefaultPosition, wx.Size(-1, -1), 0
        )
        hsizer.Add(label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.length_txt = wx.TextCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.Size(100, -1),
            wx.TE_READONLY,
        )
        hsizer.Add(self.length_txt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        vsizer.Add(hsizer, 0, wx.EXPAND, 5)

        # Obj
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(
            self, wx.ID_ANY, "Value:", wx.DefaultPosition, wx.Size(50, -1), 0
        )
        hsizer.Add(label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.obj_panel = ObjPanel_Empty(self)
        hsizer.Add(self.obj_panel, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.obj_sizer = hsizer
        vsizer.Add(hsizer, 0, wx.EXPAND, 5)

        # Doc
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(
            self, wx.ID_ANY, "Doc:", wx.DefaultPosition, wx.Size(50, -1), 0
        )
        hsizer.Add(label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.docs_txt = wx.TextCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.Size(-1, 100),
            wx.TE_MULTILINE | wx.TE_READONLY,
        )
        self.docs_txt.SetBackgroundColour(wx.Colour(240, 240, 240))
        hsizer.Add(self.docs_txt, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        vsizer.Add(hsizer, 0, wx.EXPAND, 5)

        self.SetSizer(vsizer)
        self.Layout()

    def _replace_obj_panel(self, entry: Optional["EntryConstruct"]):
        self.Freeze()
        if entry is None:
            new_panel = ObjPanel_Empty(self)
        else:
            new_panel = entry.create_obj_panel(self)
        self.obj_sizer.Replace(self.obj_panel, new_panel)
        self.obj_panel.Destroy()
        self.obj_panel = new_panel
        self.obj_panel.MoveBeforeInTabOrder(self.docs_txt)
        self.obj_sizer.Layout()
        self.Thaw()

    def set_entry(self, entry: "EntryConstruct"):
        # set general infos
        self.name_txt.SetValue("->".join(entry.path))
        self.type_txt.SetValue(entry.typ_str)
        self.docs_txt.SetValue(entry.docs)

        # get metadata
        metadata = get_gui_metadata(entry.obj)
        if metadata is not None:
            self.offset_txt.SetValue(str(metadata.offset_start))
            self.length_txt.SetValue(str(metadata.length))
        else:
            self.offset_txt.SetValue("")
            self.length_txt.SetValue("")

        # set obj panel
        self._replace_obj_panel(entry)

    def clear(self):
        self.name_txt.SetValue("")
        self.type_txt.SetValue("")
        self.docs_txt.SetValue("")
        self.length_txt.SetValue("")
        self.offset_txt.SetValue("")
        self._replace_obj_panel(None)


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

        self.expand_all_mi = wx.MenuItem(self, wx.ID_ANY, "Expand All")
        self.Append(self.expand_all_mi)
        self.Bind(wx.EVT_MENU, self.on_expand_all, self.expand_all_mi)

        self.collapse_all_mi = wx.MenuItem(self, wx.ID_ANY, "Collapse All")
        self.Append(self.collapse_all_mi)
        self.Bind(wx.EVT_MENU, self.on_collapse_all, self.collapse_all_mi)

        self.Append(wx.MenuItem(self, wx.ID_ANY, kind=wx.ITEM_SEPARATOR))

        self.hide_protected_mi = wx.MenuItem(
            self, wx.ID_ANY, "Hide Protected", kind=wx.ITEM_CHECK
        )
        self.Append(self.hide_protected_mi)
        self.Bind(wx.EVT_MENU, self.on_hide_protected, self.hide_protected_mi)
        self.hide_protected_mi.Check(self.parent.hide_protected)

        self.Append(wx.MenuItem(self, wx.ID_ANY, kind=wx.ITEM_SEPARATOR))

        # Add List with all currently shown list viewed items
        submenu = wx.Menu()
        self.submenu_map: Dict[Any, EntryConstruct] = {}
        for e in model.list_viewed_entries:
            name = "->".join(e.path)
            mi = wx.MenuItem(submenu, wx.ID_ANY, name, kind=wx.ITEM_CHECK)
            submenu.Append(mi)
            self.submenu_map[mi.GetId()] = e
            self.Bind(wx.EVT_MENU, self.on_remove_list_viewed_item, mi)
            mi.Check(True)

        submenu_mi: wx.MenuItem = self.AppendSubMenu(submenu, "List Viewed Items")
        if len(model.list_viewed_entries) == 0:
            self.Enable(submenu_mi.GetId(), False)

        # Add additional items for this entry
        if entry is not None:
            entry.modify_context_menu(self)

    def on_expand_all(self, event):
        self.parent.expand_all()

    def on_collapse_all(self, event):
        self.parent.collapse_all()

    def on_hide_protected(self, event):
        checked = self.hide_protected_mi.IsChecked()
        self.parent.hide_protected = checked
        self.parent.reload()

    def on_remove_list_viewed_item(self, event: wx.CommandEvent):
        entry = self.submenu_map[event.GetId()]
        self.model.list_viewed_entries.remove(entry)
        self.parent.reload()

# #####################################################################################################################
# Construct Editor Model ##############################################################################################
# #####################################################################################################################
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

    def __init__(self):
        dv.PyDataViewModel.__init__(self)

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
        self.UseWeakRefs(True)

    def get_column_count(self):
        """ Get the column count """
        return 3

    def get_column_name(self, selected_item, col):
        """ Get the name of the column. The column name depends on the selected item """
        entry = self.ItemToObject(selected_item)
        if not isinstance(entry, EntryConstruct):
            raise ValueError(f"{repr(entry)} is no valid entry")

        flat_subentry_list: List["EntryConstruct"] = []
        entry.create_flat_subentry_list(flat_subentry_list)

        return "->".join(flat_subentry_list[col].path)

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
            item = self.ObjectToItem(entry)
            entry.dvc_item = item
            children.append(item)
            return 1

        parent_entry = self.ItemToObject(parent)
        if not isinstance(parent_entry, EntryConstruct):
            raise ValueError(f"{repr(parent_entry)} is no valid entry")

        for entry in parent_entry.subentries:
            name = entry.name
            if (self.hide_protected == True) and (name.startswith("_") or name == ""):
                continue
            item = self.ObjectToItem(entry)
            entry.dvc_item = item
            children.append(item)
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
        if entry.parent is None:
            return dv.NullDataViewItem
        else:
            return entry.parent.dvc_item

    def GetValue(self, item, col):
        # Return the value to be displayed for this item and column.

        entry = self.ItemToObject(item)
        if not isinstance(entry, EntryConstruct):
            raise ValueError(f"{repr(entry)} is no valid entry")

        if col == ConstructEditorColumn.Name:
            return entry.name
        if col == ConstructEditorColumn.Type:
            return entry.typ_str
        if col == ConstructEditorColumn.Value:
            return entry.obj_str

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

    def GetAttr(self, item, col, attr):
        entry = self.ItemToObject(item)

        if entry is self.root_entry:
            attr.SetColour("blue")
            attr.SetBold(True)
            return True

        return False

    def SetValue(self, value, item, col):
        return True


@dataclasses.dataclass
class ExpansionInfo:
    expanded: bool
    subinfos: Dict[str, "ExpansionInfo"]


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
        vsizer.Add(self._dvc, 3, wx.ALL | wx.EXPAND, 5)

        # Create Model of DataViewCtrl
        self._model = ConstructEditorModel()
        self._dvc.AssociateModel(self._model)

        # Create InfoBars
        self._parse_error_info_bar = wx.InfoBar(self)
        vsizer.Add(self._parse_error_info_bar, 0, wx.EXPAND)

        self._build_error_info_bar = wx.InfoBar(self)
        vsizer.Add(self._build_error_info_bar, 0, wx.EXPAND)

        # create details viewer
        self._entry_details_viewer = EntryDetailsViewer(self)
        vsizer.Add(self._entry_details_viewer, 1, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(vsizer)
        self.Layout()

        # Connect Events
        self._dvc.Bind(
            dv.EVT_DATAVIEW_SELECTION_CHANGED,
            self._on_dvc_selection_changed,
            id=wx.ID_ANY,
        )
        self._dvc.Bind(dv.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self._on_dvc_value_changed)
        self._dvc.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self._on_right_click)

        self.on_entry_selected = EntrySelectedCallbackList()
        self.on_root_obj_changed = RootObjChangedCallbackList()
        self.construct = construct

    def _get_expansion_infos(
        self, parent: Optional[dv.DataViewItem]
    ) -> Dict[str, ExpansionInfo]:
        """ Get infos about the expaneded items in the DVC """
        infos: Dict[str, ExpansionInfo] = {}
        childs: List[dv.DataViewItem] = []
        self._model.GetChildren(parent, childs)
        for child in childs:
            if self._model.IsContainer(child):
                expanded = self._dvc.IsExpanded(child)
                subinfos = self._get_expansion_infos(child)
                entry: EntryConstruct = self._model.ItemToObject(child)
                infos[entry.name] = ExpansionInfo(expanded, subinfos)
        return infos

    def _expand_from_expansion_infos(
        self,
        parent: Optional[dv.DataViewItem],
        expansion_infos: Dict[str, ExpansionInfo],
    ):
        """
        Expand the DVC items from previously saved expansion infos.
        The expansion stays the same if the name of the item is still the same. Items with
        new name, will be collapsed.
        """
        childs: List[dv.DataViewItem] = []
        self._model.GetChildren(parent, childs)
        for child in childs:
            if self._model.IsContainer(child):
                entry: EntryConstruct = self._model.ItemToObject(child)
                if entry.name in expansion_infos:
                    info = expansion_infos[entry.name]
                    if info.expanded:
                        self._dvc.Expand(child)
                    self._expand_from_expansion_infos(child, info.subinfos)

    def _get_selected_entry_path(self) -> List[str]:
        """ Get the path to the selected entry """
        if self._dvc.HasSelection():
            selected_entry: EntryConstruct = self._model.ItemToObject(
                self._dvc.GetSelection()
            )
            return ["root"] + selected_entry.path
        else:
            return []

    def _set_selection_from_path(
        self, parent: Optional[dv.DataViewItem], path: List[str]
    ):
        """ Set the selected entry from path """
        if len(path) == 0:
            return

        name = path.pop(0)

        childs: List[dv.DataViewItem] = []
        self._model.GetChildren(parent, childs)
        for child in childs:
            entry: EntryConstruct = self._model.ItemToObject(child)
            if entry.name == name:
                if len(path) == 0:
                    self._dvc.Select(entry.dvc_item)
                    self._on_dvc_selection_changed(None)
                else:
                    if self._model.IsContainer(child):
                        self._set_selection_from_path(child, path)
                return

    def reload(self):
        """ Reload the ConstructEditor, while remaining expaned elements and selection """
        try:
            self.Freeze()

            # reload dvc columns  # TODO: Macht das hier noch probleme?
            self._reload_dvc_columns()

            # save settings
            expansion_infos = self._get_expansion_infos(None)
            selected_entry_path = self._get_selected_entry_path()

            # clear everything
            self._model.Cleared()
            self._entry_details_viewer.clear()

            # restore settings
            self._expand_from_expansion_infos(None, expansion_infos)
            self._set_selection_from_path(None, selected_entry_path)

        finally:
            self.Thaw()

    def parse(self, binary: bytes, **contextkw: Any):
        """ Parse binary data to struct. """
        try:
            self._model.root_obj = self._construct.parse(binary, **contextkw)
            self._parse_error_info_bar.Dismiss()
        except Exception as e:
            self._parse_error_info_bar.ShowMessage(
                f"Error while parsing binary data: {type(e).__name__}\n{str(e)}",
                wx.ICON_WARNING,
            )
            self._model.root_obj = None
        self.reload()

    def build(self, **contextkw: Any) -> bytes:
        """ Build binary data from struct. """
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
        # TODO: If this is uncommented, the focus of the ObjPanel is lost every time a change is made
        # wx.CallAfter(lambda: self.parse(binary, **contextkw))

        return binary

    # Property: construct #####################################################
    @property
    def construct(self) -> cs.Construct:
        """ Construct that is used for displaying. """
        return self._construct

    @construct.setter
    def construct(self, val: cs.Construct):
        # modify the copied construct, so that each item also includes metadata for the GUI
        self._construct = include_metadata(val)

        # create entry from the construct
        self._model.root_entry = create_entry_from_construct(
            self._model, None, cs.Renamed(self._construct, newname="root")
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

    # expand_all ##############################################################
    def expand_all(self):
        """
        Expand all Entries
        """

        def dvc_expand(entry: EntryConstruct):
            if entry.subentries is not None:
                if entry.dvc_item is not None:
                    self._dvc.Expand(entry.dvc_item)
                for sub_entry in entry.subentries:
                    dvc_expand(sub_entry)

        if self._model.root_entry:
            dvc_expand(self._model.root_entry)

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
    def collapse_all(self):
        """
        Collapse all Entries
        """

        def dvc_collapse(entry: EntryConstruct):
            subentries = entry.subentries
            dvc_item = entry.dvc_item
            if subentries is not None:
                for sub_entry in subentries:
                    dvc_collapse(sub_entry)
                if dvc_item is not None:
                    self._dvc.Collapse(dvc_item)

        if self._model.root_entry:
            dvc_collapse(self._model.root_entry)

        # expand the root entry again
        self.expand_level(1)

    # Internals ###############################################################
    def _reload_dvc_columns(self):
        """ Reload the dvc columns """
        self._dvc.ClearColumns()

        self._dvc.AppendTextColumn("Name", ConstructEditorColumn.Name, width=160)
        self._dvc.AppendTextColumn("Type", ConstructEditorColumn.Type, width=90)
        self._dvc.AppendTextColumn("Value", ConstructEditorColumn.Value, width=200)

        list_cols = 0
        for list_viewed_entry in self._model.list_viewed_entries:
            for subentry in list_viewed_entry.subentries:
                flat_list = []
                subentry.create_flat_subentry_list(flat_list)
                list_cols = max(list_cols, len(flat_list))

        for list_col in range(list_cols):
            self._dvc.AppendTextColumn(
                str(list_col), len(ConstructEditorColumn) + list_col
            )

    def _rename_dvc_columns(self, entry: EntryConstruct):
        """ Rename the dvc columns """

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
                dvc_column.SetTitle("->".join(path))
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
            self._entry_details_viewer.set_entry(entry)

            metadata = get_gui_metadata(entry.obj)

            if metadata is None:
                start = None
                end = None
            else:
                start = metadata.offset_start
                end = metadata.offset_end

            self.on_entry_selected.fire(start, end)

            self._rename_dvc_columns(entry)

        else:
            self._entry_details_viewer.clear()

    def _on_dvc_value_changed(self, event: dv.DataViewEvent):
        """ This method is called, if a value in the dvc has changed. """
        self.on_root_obj_changed.fire(self._model.root_obj)

    def _on_right_click(self, event: dv.DataViewEvent):
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
