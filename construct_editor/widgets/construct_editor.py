# -*- coding: utf-8 -*-
# GUI File aus "wxFormBuilder" importieren
import enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

import construct as cs
import construct_typed as cst
import wx
import wx.dataview as dv
import dataclasses

from construct_editor.helper.preprocessor import get_gui_metadata, include_metadata
from construct_editor.helper.wrapper import EntryConstruct, entry_mapping_construct


class EmptyObjPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Obj
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.obj_txt = wx.TextCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.Size(-1, -1),
            wx.TE_READONLY,
        )
        hsizer.Add(self.obj_txt, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)

        self.SetSizer(hsizer)
        self.Layout()


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
        self.obj_panel = EmptyObjPanel(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(-1, -1),
        )
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

    def _replace_obj_panel(self, new_panel_class: Type[wx.Panel]):
        self.Freeze()
        new_panel = new_panel_class(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(-1, -1),
        )
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
        self._replace_obj_panel(entry.obj_panel_class)

    def clear(self):
        self.name_txt.SetValue("")
        self.type_txt.SetValue("")
        self.docs_txt.SetValue("")
        self.length_txt.SetValue("")
        self.offset_txt.SetValue("")
        self._replace_obj_panel(EmptyObjPanel)


# #####################################################################################################################
# Context Menu ########################################################################################################
# #####################################################################################################################
class ContextMenu(wx.Menu):
    def __init__(self, parent: "ConstructEditor"):
        super(ContextMenu, self).__init__()
        self.parent = parent

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

    def on_expand_all(self, event):
        self.parent.expand_all()

    def on_collapse_all(self, event):
        self.parent.collapse_all()

    def on_hide_protected(self, event):
        checked = self.hide_protected_mi.IsChecked()
        self.parent.hide_protected = checked
        self.parent.reload()


# #####################################################################################################################
# Construct Editor Model ##############################################################################################
# #####################################################################################################################
class ConstructEditorModel(dv.PyDataViewModel):
    """
    This model acts as a bridge between the DataViewCtrl and the dataclasses.
    This model provides these data columns:
        0. Name: string
        1. Type: string
        2. Value: string
    """

    class Column(enum.IntEnum):
        Name = 0
        Type = 1
        Value = 2

    def __init__(
        self,
        construct: cs.Construct,
        on_obj_changed: Optional[Callable[[], None]] = None,
    ):
        dv.PyDataViewModel.__init__(self)
        self._hide_protected = True
        self._on_obj_changed = on_obj_changed

        # Initialize root
        self._construct = construct
        self._root_entry = self.create_construct_entry(
            None, cs.Renamed(self._construct, newname="root"), None
        )

        # The PyDataViewModel derives from both DataViewModel and from
        # DataViewItemObjectMapper, which has methods that help associate
        # data view items with Python objects. Normally a dictionary is used
        # so any Python object can be used as data nodes. If the data nodes
        # are weak-referencable then the objmapper can use a
        # WeakValueDictionary instead.
        self.UseWeakRefs(True)

    # Property: construct #####################################################
    @property
    def construct(self) -> cs.Construct:
        """ construct used for displaying """
        return self._construct

    @construct.setter
    def construct(self, val: cs.Construct):
        self._construct = val
        self._root_entry = self.create_construct_entry(
            None, cs.Renamed(self._construct, newname="root"), None
        )

    # Property: root_obj ######################################################
    @property
    def root_obj(self) -> Any:
        return self._root_entry._root_obj

    @root_obj.setter
    def root_obj(self, val: Any):
        self._root_entry._root_obj = val

    # Property: hide_protected ################################################
    @property
    def hide_protected(self) -> bool:
        return self._hide_protected

    @hide_protected.setter
    def hide_protected(self, value: bool):
        self._hide_protected = value

    # #########################################################################
    def create_construct_entry(
        self,
        parent: Optional["EntryConstruct"],
        subcon: "cs.Construct[Any, Any]",
        obj: Any,
    ) -> "EntryConstruct":

        if type(subcon) in entry_mapping_construct:
            return entry_mapping_construct[type(subcon)](self, parent, subcon, obj)
        else:
            for key, value in entry_mapping_construct.items():
                if isinstance(subcon, key):  # type: ignore
                    return entry_mapping_construct[key](self, parent, subcon, obj)

        # use fallback, if no entry found in the mapping
        if isinstance(subcon, cs.Construct):
            return EntryConstruct(self, parent, subcon, obj)

        raise ValueError("subcon type {} is not implemented".format(repr(subcon)))

    # #################################################################################################################
    # dv.PyDataViewModel Interface ####################################################################################
    # #################################################################################################################
    def GetColumnCount(self):
        # Report how many columns this model provides data for.
        return 3

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

        # Entry Gruppen auswerten...
        entries = None
        if not parent:
            if self._root_entry is not None:
                entries = [self._root_entry]
        else:
            parent_entry = self.ItemToObject(parent)
            if isinstance(parent_entry, EntryConstruct):
                entries = []
                for entry in parent_entry.subentries:
                    if (self._hide_protected == True) and (entry.name.startswith("_") or entry.name == ""):
                        continue
                    entries.append(entry)

            else:
                raise ValueError(f"{repr(parent_entry)} is no valid entry")

        if entries is None:
            return 0
        else:
            for entry in entries:
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
        # Return the value to be displayed for this item and column. For this
        # example we'll just pull the values from the data objects we
        # associated with the items in GetChildren.

        # Fetch the data object for this item.
        entry = self.ItemToObject(item)

        # show values
        if isinstance(entry, EntryConstruct):
            mapper = {
                self.Column.Name: entry.name,
                self.Column.Type: entry.typ_str,
                self.Column.Value: entry.obj_str,
            }
        else:
            raise ValueError(f"{repr(entry)} is no valid entry")

        return mapper[col]

    def GetAttr(self, item, col, attr):
        entry = self.ItemToObject(item)

        if entry is self._root_entry:
            attr.SetColour("blue")
            attr.SetBold(True)
            return True

        return False

    def SetValue(self, value, item, col):
        return True


@dataclasses.dataclass
class ExpansionInfo():
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
        on_obj_changed: Optional[Callable[[], None]] = None,
        on_entry_selected: Optional[
            Callable[[Optional[int], Optional[int]], None]
        ] = None,
    ):
        super().__init__(parent)

        self._on_entry_selected = on_entry_selected

        vsizer = wx.BoxSizer(wx.VERTICAL)

        # Create DataViewCtrl
        self._dvc = dv.DataViewCtrl(
            self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0, name="construct_editor"
        )
        self._dvc.AppendTextColumn("Name", 0, width=250)
        self._dvc.AppendTextColumn("Type", 1, width=100)
        self._dvc.AppendTextColumn("Value", 2, width=260)
        vsizer.Add(self._dvc, 3, wx.ALL | wx.EXPAND, 5)

        # Create Model of DataViewCtrl
        self._model = ConstructEditorModel(include_metadata(construct), on_obj_changed)
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
        self._dvc.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self._on_right_click)




    def _get_expansion_infos(self, parent: Optional[dv.DataViewItem]) -> Dict[str, ExpansionInfo]:
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

    def _expand_from_expansion_infos(self, parent: Optional[dv.DataViewItem], expansion_infos: Dict[str, ExpansionInfo]):
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
            selected_entry: EntryConstruct = self._model.ItemToObject(self._dvc.GetSelection())
            return selected_entry.path
        else:
            return []

    def _set_selection_from_path(self, path: List[str]):
        """ Set the selected entry from path """
        # TODO: Enhancement for cs.Peek

    def reload(self):
        """ Reload the ConstructEditor, while remaining expaned elements and selection """
        try:
            self.Freeze()

            # save settings
            expansion_infos = self._get_expansion_infos(None)
            selected_entry_path = self._get_selected_entry_path()

            # clear everything
            self._model.Cleared()
            self._entry_details_viewer.clear()
            self._parse_error_info_bar.Dismiss()
            self._build_error_info_bar.Dismiss()

            # restore settings
            self._expand_from_expansion_infos(None, expansion_infos)
            selected_entry = self._set_selection_from_path(selected_entry_path)

        finally:
            self.Thaw()

    def parse(self, binary: bytes, **contextkw: Any):
        """ Parse binary data to struct. """
        try:
            self._model.root_obj = self._model.construct.parse(binary, **contextkw)
            self._parse_error_info_bar.Dismiss()
        except Exception as e:
            self._parse_error_info_bar.ShowMessage(f"Error while parsing binary data: {type(e).__name__}\n{str(e)}", wx.ICON_WARNING)
            self._model.root_obj = None
        self.reload()

    def build(self, **contextkw: Any) -> bytes:
        """ Build binary data from struct. """
        try:
            binary = self._model.construct.build(self.root_obj, **contextkw)
            self._build_error_info_bar.Dismiss()
        except Exception as e:
            self._build_error_info_bar.ShowMessage(f"Error while building binary data: {type(e).__name__}\n{str(e)}", wx.ICON_WARNING)
            raise e

        # wx.CallAfter(lambda: self.parse(binary, **contextkw))  # TODO: Enhancement for cs.Peek
        return binary

    # Property: construct #####################################################
    @property
    def construct(self) -> cs.Construct:
        """ Construct that is used for displaying. """
        return self._model.construct

    @construct.setter
    def construct(self, val: cs.Construct):
        # modify the copied construct, so that each item also includes metadata for the GUI
        val = include_metadata(val)
        self._model.construct = val

    # Property: root_obj ######################################################
    @property
    def root_obj(self) -> bytes:
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

        if self._model._root_entry:
            dvc_expand(self._model._root_entry)

    # expand_level ############################################################
    def expand_level(self, level: int):
        """
        Expand all Entries to Level ... (0=root level)
        """

        def dvc_expand(entry: EntryConstruct, current_level: int):
            if entry.subentries is not None:
                if entry.dvc_item is not None:
                    self._dvc.Expand(entry.dvc_item)
                if current_level < level:
                    for sub_entry in entry.subentries:
                        dvc_expand(sub_entry, current_level + 1)

        if self._model._root_entry:
            dvc_expand(self._model._root_entry, 1)

    # collapse_all ############################################################
    def collapse_all(self):
        """
        Collapse all Entries
        """

        def dvc_collapse(entry: EntryConstruct):
            if entry.subentries is not None:
                if entry.dvc_item is not None:
                    self._dvc.Collapse(entry.dvc_item)
                for sub_entry in entry.subentries:
                    dvc_collapse(sub_entry)

        if self._model._root_entry:
            dvc_collapse(self._model._root_entry)

    # Internals ###############################################################
    def _on_dvc_selection_changed(self, event: wx.Event):
        """
        This method is called, if the selection in the dvc has changed.

        Then the infos of the new selected entry is shown.
        """
        dvc = event.GetEventObject()
        item = dvc.GetSelection()
        if item.ID is not None:
            entry: EntryConstruct = dvc.Model.ItemToObject(item)
            self._entry_details_viewer.set_entry(entry)

            metadata = get_gui_metadata(entry.obj)

            if metadata is None:
                start = None
                end = None
            else:
                start = metadata.offset_start
                end = metadata.offset_end

            if self._on_entry_selected is not None:
                self._on_entry_selected(start, end)

        else:
            self._entry_details_viewer.clear()

    def _on_right_click(self, event):
        """
        This method is called, the dvc ist right clicked

        Then a context menu is created
        """
        self.PopupMenu(ContextMenu(self), event.GetPosition())
