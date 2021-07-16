import dataclasses
import enum
import string
import typing as t
from typing import Any, Dict, List, Optional, Type, Union

import arrow
import construct as cs
import construct_editor.widgets.construct_editor as construct_editor
import construct_typed as cst
import wx
import wx.adv
from construct_editor.helper.preprocessor import (
    GuiMetaData,
    IncludeGuiMetaData,
    add_gui_metadata,
    get_gui_metadata,
)


def evaluate(param, context):
    return param(context) if callable(param) else param


def int_to_str(integer_format: "construct_editor.IntegerFormat", val: int) -> str:
    if isinstance(val, str):
        return val  # tolerate string
    if integer_format is construct_editor.IntegerFormat.Hex:
        return f"0x{val:X}"
    return f"{val}"


def str_to_int(s: str) -> int:
    if len(s) == 0:
        s = "0"

    # convert string to int
    # (base=0 means, that eg. 0x, 0b prefixes are allowed)
    i = int(s, base=0)

    return i


def str_to_bytes(s: str) -> bytes:
    return bytes.fromhex(s)


# #####################################################################################################################
# GUI Elements ########################################################################################################
# #####################################################################################################################
class ObjPanel(wx.Panel):
    """ Base class for a panel that shows the value and allows modifications of it. """

    def get_new_obj(self) -> Any:
        raise NotImplementedError()


class ObjPanel_Empty(ObjPanel):
    def __init__(self, parent):
        super().__init__(parent)

        # Obj
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.obj_txt = wx.TextCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.Size(-1, -1),
            style=wx.TE_READONLY,
        )
        hsizer.Add(self.obj_txt, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)

        self.SetSizer(hsizer)
        self.Layout()


class ObjPanel_Default(ObjPanel):
    def __init__(self, parent, entry: "EntryConstruct"):
        super().__init__(parent)
        self.entry = entry

        # Test if the obj of the entry is available
        if self.entry.obj is None:
            return

        # Obj
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.obj_txt = wx.TextCtrl(
            self,
            wx.ID_ANY,
            self.entry.obj_str,
            wx.DefaultPosition,
            wx.Size(-1, -1),
            style=wx.TE_READONLY,
        )
        hsizer.Add(self.obj_txt, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)

        self.SetSizer(hsizer)
        self.Layout()

    def get_new_obj(self) -> Any:
        return self.entry.obj


class ObjPanel_String(ObjPanel):
    def __init__(self, parent, entry: "EntryConstruct"):
        super().__init__(parent)
        self.entry = entry

        # Test if the obj of the entry is available
        if self.entry.obj is None:
            return

        # Obj
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.obj_txt = wx.TextCtrl(
            self,
            wx.ID_ANY,
            self.entry.obj_str,
            style=wx.TE_PROCESS_ENTER,
        )
        hsizer.Add(self.obj_txt, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)

        self.SetSizer(hsizer)
        self.Layout()

    def get_new_obj(self) -> Any:
        val_str: str = self.obj_txt.GetValue()
        return val_str


class ObjPanel_Integer(ObjPanel):
    def __init__(self, parent, entry: "EntryConstruct"):
        super().__init__(parent)
        self.entry = entry

        # Test if the obj of the entry is available
        if self.entry.obj is None:
            return

        # Obj
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.obj_txtctrl = wx.TextCtrl(
            self,
            wx.ID_ANY,
            self.entry.obj_str,
            style=wx.TE_PROCESS_ENTER,
        )
        hsizer.Add(self.obj_txtctrl, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)

        self.SetSizer(hsizer)
        self.Layout()

    def get_new_obj(self) -> Any:
        val_str: str = self.obj_txtctrl.GetValue()

        try:
            # convert string to integer
            new_obj = str_to_int(val_str)
        except Exception:
            new_obj = val_str  # this will probably result in a building error

        return new_obj


class ObjPanel_Flag(ObjPanel):
    true_strings = ["t", "true", "1"]
    false_strings = ["f", "false", "0"]

    def __init__(self, parent, entry: "EntryConstruct"):
        super().__init__(parent)
        self.entry = entry

        # Test if the obj of the entry is available
        if self.entry.obj is None:
            return

        # Obj
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.obj_txtctrl = wx.TextCtrl(
            self,
            wx.ID_ANY,
            self.entry.obj_str,
            style=wx.TE_PROCESS_ENTER,
        )
        hsizer.Add(self.obj_txtctrl, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)

        self.SetSizer(hsizer)
        self.Layout()

    def get_new_obj(self) -> Any:
        val_str: str = self.obj_txtctrl.GetValue()

        val_str = val_str.lower()
        if val_str in self.true_strings:
            new_obj = True
        elif val_str in self.false_strings:
            new_obj = False
        else:
            new_obj = val_str  # this will probably result in a building error

        return new_obj


class ObjPanel_Bytes(ObjPanel):
    def __init__(self, parent, entry: "EntryConstruct"):
        super().__init__(parent)
        self.entry = entry

        # Test if the obj of the entry is available
        if self.entry.obj is None:
            return

        # Obj
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.obj_txtctrl = wx.TextCtrl(
            self,
            wx.ID_ANY,
            self.entry.obj_str,
            style=wx.TE_PROCESS_ENTER,
        )
        hsizer.Add(self.obj_txtctrl, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)

        self.SetSizer(hsizer)
        self.Layout()

    def get_new_obj(self) -> Any:
        val_str: str = self.obj_txtctrl.GetValue()

        try:
            # convert string to bytes
            new_obj = str_to_bytes(val_str)
        except Exception:
            new_obj = val_str  # this will probably result in a building error

        return new_obj


@dataclasses.dataclass
class EnumItem:
    name: str
    value: int


class ObjPanel_Enum(ObjPanel):
    def __init__(self, parent, entry: Union["EntryTEnum", "EntryEnum"]):
        super().__init__(parent)
        self.entry = entry

        # Test if the obj of the entry is available
        if self.entry.obj is None:
            return

        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.obj_combobox = wx.ComboBox(
            self,
            style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER,
        )
        hsizer.Add(self.obj_combobox, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)

        items = self.entry.get_enum_items()
        for pos, item in enumerate(items):
            self.obj_combobox.Insert(
                item=f"{int_to_str(entry.model.integer_format, item.value)} ({item.name})",
                pos=pos,
                clientData=item,
            )
        item = self.entry.get_enum_item_from_obj()
        sel_item_str = (
            f"{int_to_str(entry.model.integer_format, item.value)} ({item.name})"
        )
        self.obj_combobox.SetStringSelection(sel_item_str)
        self.obj_combobox.SetValue(sel_item_str)  # show even if it is not in the list

        self.SetSizer(hsizer)
        self.Layout()

    def get_new_obj(self) -> Any:
        val_str: str = self.obj_combobox.GetValue()
        if len(val_str) == 0:
            val_str = "0"

        val_str = val_str.split()[0]
        new_obj = self.entry.conv_str_to_obj(val_str)
        return new_obj


@dataclasses.dataclass
class FlagsEnumItem:
    name: str
    value: int
    checked: bool


class FlagsEnumComboPopup(wx.ComboPopup):
    def __init__(
        self,
        combo_ctrl: wx.ComboCtrl,
        entry: Union["EntryTFlagsEnum", "EntryFlagsEnum"],
    ):
        super().__init__()
        self.combo_ctrl = combo_ctrl
        self.entry = entry
        self.clbx: wx.CheckListBox

    def on_motion(self, evt):
        item = self.clbx.HitTest(evt.GetPosition())
        if item != wx.NOT_FOUND:
            # only select if not selected prevents flickering
            if not self.clbx.IsSelected(item):
                self.clbx.Select(item)

    def on_left_down(self, evt):
        item = self.clbx.HitTest(evt.GetPosition())
        if item != wx.NOT_FOUND:
            # select the new item in the gui
            items = list(self.clbx.GetCheckedItems())
            if item in items:
                items.remove(item)
            else:
                items.append(item)
            self.clbx.SetCheckedItems(items)

            # refresh shown string
            self.combo_ctrl.SetValue(self.GetStringValue())

    def Create(self, parent):
        self.clbx = wx.CheckListBox(parent)
        self.clbx.Bind(wx.EVT_MOTION, self.on_motion)
        self.clbx.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        return True

    # Return the widget that is to be used for the popup
    def GetControl(self):
        return self.clbx

    # Return final size of popup. Called on every popup, just prior to OnPopup.
    # minWidth = preferred minimum width for window
    # prefHeight = preferred height. Only applies if > 0,
    # maxHeight = max height for window, as limited by screen size
    #   and should only be rounded down, if necessary.
    def GetAdjustedSize(self, minWidth, prefHeight, maxHeight):
        row_height = self.clbx.GetCharHeight() + 2
        row_count = self.clbx.GetCount()
        prefHeight = min(row_height * row_count + 4, prefHeight)
        return wx.ComboPopup.GetAdjustedSize(self, minWidth, prefHeight, maxHeight)

    def get_flagsenum_items(self) -> t.List["FlagsEnumItem"]:
        # read all flagsenum items and modify checked status
        flagsenum_items: t.List[FlagsEnumItem] = []
        for item in range(self.clbx.GetCount()):
            flagsenum_item: FlagsEnumItem = self.clbx.GetClientData(item)
            flagsenum_item.checked = self.clbx.IsChecked(item)
            flagsenum_items.append(flagsenum_item)
        return flagsenum_items

    def GetStringValue(self):
        flagsenum_items = self.get_flagsenum_items()
        temp_obj = self.entry.conv_flagsenum_items_to_obj(flagsenum_items)
        return self.entry.conv_obj_to_str(temp_obj)


class ObjPanel_FlagsEnum(ObjPanel):
    def __init__(self, parent, entry: Union["EntryTFlagsEnum", "EntryFlagsEnum"]):
        super().__init__(parent)
        self.entry = entry

        obj = self.entry.obj

        # Test if the obj of the entry is available
        if obj is None:
            return

        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.combo_ctrl = wx.ComboCtrl(self, style=wx.CB_READONLY)
        self.popup_ctrl = FlagsEnumComboPopup(self.combo_ctrl, self.entry)
        self.combo_ctrl.SetPopupControl(self.popup_ctrl)

        # Initialize CheckListBox
        items = self.entry.get_flagsenum_items_from_obj()
        for pos, item in enumerate(items):
            self.popup_ctrl.clbx.Insert(
                item=f"{int_to_str(entry.model.integer_format, item.value)} ({item.name})",
                pos=pos,
                clientData=item,
            )
            self.popup_ctrl.clbx.Check(pos, item.checked)

        self.combo_ctrl.SetValue(self.popup_ctrl.GetStringValue())

        hsizer.Add(self.combo_ctrl, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)

        self.SetSizer(hsizer)
        self.Layout()

    def get_new_obj(self) -> Any:
        flagsenum_items = self.popup_ctrl.get_flagsenum_items()
        new_obj = self.entry.conv_flagsenum_items_to_obj(flagsenum_items)
        return new_obj


class ObjPanel_Timestamp(ObjPanel):
    def __init__(self, parent, entry: "EntryTimestamp"):
        super().__init__(parent)
        self.entry = entry

        # Test if the obj of the entry is available
        if entry.obj is None:
            return
        if not isinstance(entry.obj, arrow.Arrow):
            return

        # Obj
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        dt = self.entry.obj.datetime
        wx_datetime = wx.DateTime(
            day=dt.day,
            month=dt.month - 1,  # in wx.adc.DatePickerCtrl the month start with 0
            year=dt.year,
            hour=dt.hour,
            minute=dt.minute,
            second=dt.second,
            millisec=dt.microsecond // 1000,
        )

        self.date_picker = wx.adv.DatePickerCtrl(
            self,
            wx.ID_ANY,
            wx_datetime,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY,
        )
        hsizer.Add(self.date_picker, 0, wx.LEFT, 0)

        self.time_picker = wx.adv.TimePickerCtrl(
            self,
            wx.ID_ANY,
            wx_datetime,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.adv.TP_DEFAULT,
        )
        hsizer.Add(self.time_picker, 0, wx.LEFT, 5)

        self.obj_txtctrl = wx.TextCtrl(
            self,
            wx.ID_ANY,
            self.entry.obj_str,
            wx.DefaultPosition,
            wx.DefaultSize,
            style=wx.TE_READONLY,
        )
        hsizer.Add(self.obj_txtctrl, 1, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.SetSizer(hsizer)
        self.Layout()

    def get_new_obj(self) -> Any:
        date: wx.DateTime = self.date_picker.GetValue()
        time: wx.DateTime = self.time_picker.GetValue()
        obj_type = type(self.entry.obj)
        new_obj = obj_type(
            year=date.year,
            month=date.month + 1,  # in wx.adc.DatePickerCtrl the month start with 0
            day=date.day,
            hour=time.hour,
            minute=time.minute,
            second=time.second,
        )
        return new_obj


# #####################################################################################################################
# DVC Entries #########################################################################################################
# #####################################################################################################################


class NameExcludedFromPath(str):
    pass


NameType = t.Union[None, str, NameExcludedFromPath]

# EntryConstruct ######################################################################################################
class EntryConstruct(object):
    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Construct[Any, Any]",
        name: NameType,
        docs: str,
    ):
        self.model = model
        self._parent = parent
        self._construct = construct
        self._name = name
        self._docs = docs

        # This is set from the model, when the dvc item for this entry is created.
        self._dvc_item = None
        self._dvc_item_expanded = False

    # default "parent" ########################################################
    @property
    def parent(self) -> Optional["EntryConstruct"]:
        return self._parent

    # default "construct" #####################################################
    @property
    def construct(self) -> "cs.Construct[Any, Any]":
        return self._construct

    # default "obj" ###########################################################
    @property
    def obj(self) -> Any:
        path = self.path
        obj = self.model.root_obj
        for p in path[1:]:
            if isinstance(obj, dict) or isinstance(obj, cst.DataclassMixin):
                obj = obj[p]
            elif isinstance(obj, list):
                obj = obj[int(p)]
        return obj

    @obj.setter
    def obj(self, val: Any):
        path = self.path
        obj = self.model.root_obj
        for p in path[1:-1]:
            if isinstance(obj, dict) or isinstance(obj, cst.DataclassMixin):
                obj = obj[p]
            elif isinstance(obj, list):
                obj = obj[int(p)]

        if isinstance(obj, dict) or isinstance(obj, cst.DataclassMixin):
            obj[path[-1]] = val
        elif isinstance(obj, list):
            obj[int(path[-1])] = val

    # default "obj_str" #######################################################
    @property
    def obj_str(self) -> str:
        return str(self.obj)

    # default "obj_metadata" ##################################################
    @property
    def obj_metadata(self) -> t.Optional[GuiMetaData]:
        return get_gui_metadata(self.obj)

    # default "name" ##########################################################
    @property
    def name(self) -> str:
        if self._name is not None:
            return self._name
        else:
            return ""

    # default "docs" ##########################################################
    @property
    def docs(self) -> str:
        return self._docs

    # default "typ_str" #######################################################
    @property
    def typ_str(self) -> str:
        return repr(self.construct)

    # default "subentries" ####################################################
    @property
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        return None

    # default "dvc_item" ######################################################
    @property
    def dvc_item(self) -> Any:
        return self._dvc_item

    @dvc_item.setter
    def dvc_item(self, val: Any):
        self._dvc_item = val

    # default "dvc_item_expanded" #############################################
    @property
    def dvc_item_expanded(self) -> bool:
        return self._dvc_item_expanded

    @dvc_item_expanded.setter
    def dvc_item_expanded(self, val: bool):
        self._dvc_item_expanded = val

    # default "dvc_item_expanded" #############################################
    def dvc_item_restore_expansion(self):
        """ Restore the expansion state, recursively """
        dvc_item = self.dvc_item
        subentries = self.subentries
        if subentries is not None:
            if dvc_item is not None:
                if self.dvc_item_expanded:
                    self.model.dvc.Expand(self.dvc_item)
                else:
                    self.model.dvc.Collapse(self.dvc_item)

            for subentry in subentries:
                if subentry.subentries is not None:
                    subentry.dvc_item_restore_expansion()

    # default "add_nonstruct_subentries_to_list" ##############################
    def create_flat_subentry_list(self, flat_subentry_list: List["EntryConstruct"]):
        """ Create a flat list with all subentires, recursively """
        subentries = self.subentries
        if subentries is not None:
            for subentry in subentries:
                subentry.create_flat_subentry_list(flat_subentry_list)
        else:
            flat_subentry_list.append(self)

    # default "create_obj_panel" ##############################################
    def create_obj_panel(self, parent) -> ObjPanel:
        """ This method is called, when the user clicks an entry """
        return ObjPanel_Default(parent, self)

    # default "modify_context_menu" ###########################################
    def modify_context_menu(self, menu: "construct_editor.ContextMenu"):
        """ This method is called, when the user right clicks an entry and a ContextMenu is created """
        pass

    # default "path" ##########################################################
    @property
    def path(self) -> List[str]:
        parent = self.parent
        if parent is not None:
            path = parent.path
        else:
            path = []

        # Append name if available and should not be excluded
        name = self.name
        if not isinstance(name, NameExcludedFromPath):
            if name != "":
                path.append(name)

        return path


# EntrySubconstruct ###################################################################################################
class EntrySubconstruct(EntryConstruct):
    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Subconstruct[Any, Any, Any, Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

        self.subentry = create_entry_from_construct(
            model, self, construct.subcon, None, ""
        )

    # pass throught "obj_str" to subentry #####################################
    @property
    def obj_str(self) -> Any:
        return self.subentry.obj_str

    # pass throught "typ_str" to subentry #####################################
    @property
    def typ_str(self) -> str:
        return self.subentry.typ_str

    # pass throught "subentries" to subentry ##################################
    @property
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        return self.subentry.subentries

    # pass throught "dvc_item" to subentry ####################################
    @property
    def dvc_item(self) -> Any:
        return self.subentry.dvc_item

    @dvc_item.setter
    def dvc_item(self, val: Any):
        self.subentry.dvc_item = val

    # pass throught "dvc_item_expanded" to subentry ###########################
    @property
    def dvc_item_expanded(self) -> bool:
        return self.subentry.dvc_item_expanded

    @dvc_item_expanded.setter
    def dvc_item_expanded(self, val: bool):
        self.subentry.dvc_item_expanded = val

    # pass throught "create_obj_panel" to subentry ############################
    def create_obj_panel(self, parent) -> ObjPanel:
        return self.subentry.create_obj_panel(parent)

    # pass throught "modify_context_menu" to subentry #########################
    def modify_context_menu(self, menu: "construct_editor.ContextMenu"):
        return self.subentry.modify_context_menu(menu)


# EntryAdapter ########################################################################################################
class AdapterPanelType(enum.Enum):
    Default = enum.auto()
    Integer = enum.auto()
    String = enum.auto()


def add_adapter_mapping(
    type_str: str,
    obj_panel: AdapterPanelType,
    adapter: t.Union[Type["cs.Construct[Any, Any]"], "cs.Construct[Any, Any]"],
):
    """ Add a Mapping for a custom adapter construct """

    class EntryAdapter(EntryConstruct):
        def __init__(
            self,
            model: "construct_editor.ConstructEditorModel",
            parent: Optional["EntryConstruct"],
            construct: "cs.Subconstruct[Any, Any, Any, Any]",
            name: NameType,
            docs: str,
        ):
            super().__init__(model, parent, construct, name, docs)

        @property
        def typ_str(self) -> str:
            return type_str

        @property
        def obj_str(self) -> Any:
            return str(self.obj)

        def create_obj_panel(self, parent) -> ObjPanel:
            if obj_panel == AdapterPanelType.Integer:
                return ObjPanel_Integer(parent, self)
            elif obj_panel == AdapterPanelType.String:
                return ObjPanel_String(parent, self)
            else:
                return ObjPanel_Default(parent, self)

    construct_entry_mapping[adapter] = EntryAdapter


# EntryStruct #########################################################################################################
class EntryStruct(EntryConstruct):
    construct: "cs.Struct[Any, Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Struct[Any, Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

        # change default row infos
        self._subentries = []

        # create sub entries
        for subcon in self.construct.subcons:
            subentry = create_entry_from_construct(model, self, subcon, None, "")
            self._subentries.append(subentry)

    @property
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        return self._subentries

    @property
    def typ_str(self) -> str:
        return "Struct"

    @property
    def obj_str(self) -> str:
        return ""

    def create_obj_panel(self, parent) -> ObjPanel:
        return ObjPanel_Default(parent, self)  # TODO: create panel for cs.Struct

    def modify_context_menu(self, menu: "construct_editor.ContextMenu"):
        menu.Append(wx.MenuItem(menu, wx.ID_ANY, kind=wx.ITEM_SEPARATOR))

        def on_expand_children_clicked(event: wx.MenuEvent):
            menu.parent.expand_children(self)

        def on_collapse_children_clicked(event: wx.MenuEvent):
            menu.parent.collapse_children(self)

        menu_item = wx.MenuItem(menu, wx.ID_ANY, "Expand Children")
        menu.Append(menu_item)
        menu.Bind(wx.EVT_MENU, on_expand_children_clicked, menu_item)

        menu_item = wx.MenuItem(menu, wx.ID_ANY, "Collapse Children")
        menu.Append(menu_item)
        menu.Bind(wx.EVT_MENU, on_collapse_children_clicked, menu_item)


# EntryArray ##########################################################################################################
class EntryArray(EntrySubconstruct):
    construct: t.Union[
        "cs.Array[Any, Any, Any, Any]", "cs.GreedyRange[Any, Any, Any, Any]"
    ]

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: t.Union[
            "cs.Array[Any, Any, Any, Any]", "cs.GreedyRange[Any, Any, Any, Any]"
        ],
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

        self._subentries = []

    @property
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        # get length of array
        try:
            array_len = len(self.obj)
        except Exception:
            if isinstance(self.construct, cs.Array) and isinstance(
                self.construct.count, int
            ):
                array_len = self.construct.count
            else:
                array_len = 1

        # append entries if not appended yet
        if len(self._subentries) != array_len:
            self._subentries.clear()
            for index in range(0, array_len):
                subentry = create_entry_from_construct(
                    self.model,
                    self,
                    self.construct.subcon,
                    str(index),
                    "",
                )
                self._subentries.append(subentry)

        return self._subentries

    @property
    def typ_str(self) -> str:
        obj = self.obj

        if isinstance(self.construct, cs.Array):
            try:
                metadata = get_gui_metadata(obj)
                count = evaluate(self.construct.count, metadata["context"])
                return f"Array[{count}]"
            except Exception:
                return f"Array[{self.construct.count}]"
        else:
            try:
                return f"Array[{len(self.obj)}]"
            except Exception:
                return f"GreedyRange"

    @property
    def obj_str(self) -> str:
        return ""

    def create_obj_panel(self, parent) -> ObjPanel:
        return ObjPanel_Default(parent, self)  # TODO: create panel for cs.Array

    def modify_context_menu(self, menu: "construct_editor.ContextMenu"):
        menu.Append(wx.MenuItem(menu, wx.ID_ANY, kind=wx.ITEM_SEPARATOR))

        def on_expand_children_clicked(event: wx.MenuEvent):
            menu.parent.expand_children(self)

        def on_collapse_children_clicked(event: wx.MenuEvent):
            menu.parent.collapse_children(self)

        menu_item = wx.MenuItem(menu, wx.ID_ANY, "Expand Children")
        menu.Append(menu_item)
        menu.Bind(wx.EVT_MENU, on_expand_children_clicked, menu_item)

        menu_item = wx.MenuItem(menu, wx.ID_ANY, "Collapse Children")
        menu.Append(menu_item)
        menu.Bind(wx.EVT_MENU, on_collapse_children_clicked, menu_item)

        # If the subentry has no subentries itself, it makes no sense to create a list view.
        temp_subentry = create_entry_from_construct(
            self.model, self, self.construct.subcon, None, ""
        )
        if temp_subentry.subentries is None:
            return

        menu.Append(wx.MenuItem(menu, wx.ID_ANY, kind=wx.ITEM_SEPARATOR))

        def on_menu_item_clicked(event: wx.MenuEvent):
            if self in self.model.list_viewed_entries:
                self.model.list_viewed_entries.remove(self)
            else:
                self.model.list_viewed_entries.append(self)
            self.dvc_item_expanded = True
            menu.parent.reload()

        menu_item = wx.MenuItem(menu, wx.ID_ANY, "Enable List View", kind=wx.ITEM_CHECK)
        menu.Append(menu_item)
        menu_item.Check(self in self.model.list_viewed_entries)
        menu.Bind(wx.EVT_MENU, on_menu_item_clicked, menu_item)


# EntryIfThenElse #####################################################################################################
class EntryIfThenElse(EntryConstruct):
    construct: "cs.IfThenElse[Any, Any, Any, Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.IfThenElse[Any, Any, Any, Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

        self._subentry_then = create_entry_from_construct(
            self.model,
            self,
            self.construct.thensubcon,
            NameExcludedFromPath(f"If {self.construct.condfunc} then"),
            "",
        )

        self._subentry_else = create_entry_from_construct(
            self.model,
            self,
            self.construct.elsesubcon,
            NameExcludedFromPath("Else"),
            "",
        )

        # change default row infos
        self._subentries: List[EntryConstruct] = [
            self._subentry_then,
            self._subentry_else,
        ]

    def _get_subentry(self) -> "Optional[EntryConstruct]":
        """ Evaluate the conditional function to detect the type of the subentry """
        obj = self.obj
        if obj is None:
            return None
        else:
            metadata = get_gui_metadata(obj)
            cond = evaluate(self.construct.condfunc, metadata["context"])
            if cond:
                return self._subentry_then
            else:
                return self._subentry_else

    @property
    def obj_str(self) -> str:
        subentry = self._get_subentry()
        if subentry is None:
            return ""
        else:
            return subentry.obj_str

    @property
    def typ_str(self) -> str:
        subentry = self._get_subentry()
        if subentry is None:
            return "IfThenElse"
        else:
            return subentry.typ_str

    @property
    def dvc_item(self) -> Any:
        subentry = self._get_subentry()
        if subentry is None:
            return super().dvc_item
        else:
            return subentry.dvc_item

    @dvc_item.setter
    def dvc_item(self, val: Any):
        subentry = self._get_subentry()
        if subentry is None:
            self._dvc_item = val
        else:
            subentry.dvc_item = val

    @property
    def dvc_item_expanded(self) -> bool:
        subentry = self._get_subentry()
        if subentry is None:
            return self._dvc_item_expanded
        else:
            return subentry.dvc_item_expanded

    @dvc_item_expanded.setter
    def dvc_item_expanded(self, val: bool):
        subentry = self._get_subentry()
        if subentry is None:
            self._dvc_item_expanded = val
        else:
            subentry.dvc_item_expanded = val

    @property
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        subentry = self._get_subentry()
        if subentry is None:
            return self._subentries
        else:
            return subentry.subentries

    def create_obj_panel(self, parent) -> ObjPanel:
        subentry = self._get_subentry()
        if subentry is None:
            return ObjPanel_Default(parent, self)
        else:
            return subentry.create_obj_panel(parent)

    def modify_context_menu(self, menu: "construct_editor.ContextMenu"):
        subentry = self._get_subentry()
        if subentry is None:
            return
        else:
            return subentry.modify_context_menu(menu)


# EntrySwitch #########################################################################################################
class EntrySwitch(EntryConstruct):
    construct: "cs.Switch[Any, Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Switch[Any, Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

        self._subentries: List[EntryConstruct] = []
        self._subentry_cases: Dict[str, EntryConstruct] = {}
        self._subentry_default: Optional[EntryConstruct] = None

        for key, value in self.construct.cases.items():
            subentry_case = create_entry_from_construct(
                self.model,
                self,
                value,
                NameExcludedFromPath(f"Case {self.construct.keyfunc} == {str(key)}"),
                "",
            )
            self._subentry_cases[key] = subentry_case
            self._subentries.append(subentry_case)

        if self.construct.default is not None:
            self._subentry_default = create_entry_from_construct(
                self.model,
                self,
                self.construct.default,
                NameExcludedFromPath("Default"),
                "",
            )
            self._subentries.append(self._subentry_default)

    def _get_subentry(self) -> "Optional[EntryConstruct]":
        """ Evaluate the conditional function to detect the type of the subentry """
        obj = self.obj
        if obj is None:
            return None
        else:
            metadata = get_gui_metadata(obj)
            key = evaluate(self.construct.keyfunc, metadata["context"])
            if key in self._subentry_cases:
                return self._subentry_cases[key]
            else:
                return self._subentry_default

    @property
    def obj_str(self) -> str:
        subentry = self._get_subentry()
        if subentry is None:
            return ""
        else:
            return subentry.obj_str

    @property
    def typ_str(self) -> str:
        subentry = self._get_subentry()
        if subentry is None:
            return "Switch"
        else:
            return subentry.typ_str

    @property
    def dvc_item(self) -> Any:
        subentry = self._get_subentry()
        if subentry is None:
            return super().dvc_item
        else:
            return subentry.dvc_item

    @dvc_item.setter
    def dvc_item(self, val: Any):
        subentry = self._get_subentry()
        if subentry is None:
            self._dvc_item = val
        else:
            subentry.dvc_item = val

    @property
    def dvc_item_expanded(self) -> bool:
        subentry = self._get_subentry()
        if subentry is None:
            return self._dvc_item_expanded
        else:
            return subentry.dvc_item_expanded

    @dvc_item_expanded.setter
    def dvc_item_expanded(self, val: bool):
        subentry = self._get_subentry()
        if subentry is None:
            self._dvc_item_expanded = val
        else:
            subentry.dvc_item_expanded = val

    @property
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        subentry = self._get_subentry()
        if subentry is None:
            return self._subentries
        else:
            return subentry.subentries

    def create_obj_panel(self, parent) -> ObjPanel:
        subentry = self._get_subentry()
        if subentry is None:
            return ObjPanel_Default(parent, self)
        else:
            return subentry.create_obj_panel(parent)

    def modify_context_menu(self, menu: "construct_editor.ContextMenu"):
        subentry = self._get_subentry()
        if subentry is None:
            return
        else:
            return subentry.modify_context_menu(menu)


# EntryFormatField ####################################################################################################
class EntryFormatField(EntryConstruct):
    construct: "cs.FormatField[Any, Any]"
    type_mapping = {
        ">B": ("Int8ub", int, 8, False),
        ">H": ("Int16ub", int, 16, False),
        ">L": ("Int32ub", int, 32, False),
        ">Q": ("Int64ub", int, 64, False),
        ">b": ("Int8sb", int, 8, True),
        ">h": ("Int16sb", int, 16, True),
        ">l": ("Int32sb", int, 32, True),
        ">q": ("Int64sb", int, 64, True),
        "<B": ("Int8ul", int, 8, False),
        "<H": ("Int16ul", int, 16, False),
        "<L": ("Int32ul", int, 32, False),
        "<Q": ("Int64ul", int, 64, False),
        "<b": ("Int8sl", int, 8, True),
        "<h": ("Int16sl", int, 16, True),
        "<l": ("Int32sl", int, 32, True),
        "<q": ("Int64sl", int, 64, True),
        "=B": ("Int8un", int, 8, False),
        "=H": ("Int16un", int, 16, False),
        "=L": ("Int32un", int, 32, False),
        "=Q": ("Int64un", int, 64, False),
        "=b": ("Int8sn", int, 8, True),
        "=h": ("Int16sn", int, 16, True),
        "=l": ("Int32sn", int, 32, True),
        "=q": ("Int64sn", int, 64, True),
        ">e": ("Float16b", float),
        "<e": ("Float16l", float),
        "=e": ("Float16n", float),
        ">f": ("Float32b", float),
        "<f": ("Float32l", float),
        "=f": ("Float32n", float),
        ">d": ("Float64b", float),
        "<d": ("Float64l", float),
        "=d": ("Float64n", float),
    }

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.FormatField[Any, Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

        # change default row infos
        self.type_infos = None
        if construct.fmtstr in self.type_mapping:
            self.type_infos = self.type_mapping[construct.fmtstr]

    def create_obj_panel(self, parent) -> ObjPanel:
        if self.type_infos[1] is int:
            return ObjPanel_Integer(parent, self)
        else:
            return ObjPanel_Default(parent, self)  # TODO: float

    @property
    def obj_str(self) -> str:
        obj = self.obj
        if (obj is None) or (self.type_infos[1] is not int):
            return str(obj)
        else:
            return int_to_str(self.model.integer_format, obj)

    @property
    def typ_str(self) -> str:
        if self.type_infos is not None:
            return self.type_infos[0]
        else:
            return "FormatField[{}]".format(repr(self.construct.fmtstr))


# EntryBytesInteger ###################################################################################################
class EntryBytesInteger(EntryConstruct):
    construct: "cs.BytesInteger[Any, Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.BytesInteger[Any, Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        if self.construct.length == 3:
            if self.construct.signed is False:
                if self.construct.swapped is False:
                    return "Int24ub"
                else:
                    return "Int24ul"
            else:
                if self.construct.swapped is False:
                    return "Int24sb"
                else:
                    return "Int24sl"
        else:
            return repr(self.construct)

    @property
    def obj_str(self) -> str:
        obj = self.obj
        if obj is None:
            return str(obj)
        else:
            return int_to_str(self.model.integer_format, obj)

    def create_obj_panel(self, parent) -> ObjPanel:
        if isinstance(self.construct.length, int):
            return ObjPanel_Integer(parent, self)
        else:
            return ObjPanel_Default(parent, self)


# EntryBitsInteger ####################################################################################################
class EntryBitsInteger(EntryConstruct):
    construct: "cs.BitsInteger[Any, Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.BitsInteger[Any, Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        # change default row infos
        return "BitsInteger[{}{}]".format(
            repr(self.construct.length),
            ", signed" if self.construct.signed is True else "",
        )

    @property
    def obj_str(self) -> str:
        obj = self.obj
        if obj is None:
            return str(obj)
        else:
            return int_to_str(self.model.integer_format, obj)

    def create_obj_panel(self, parent) -> ObjPanel:
        if isinstance(self.construct.length, int):
            return ObjPanel_Integer(parent, self)
        else:
            return ObjPanel_Default(parent, self)


# EntryBytes ##########################################################################################################
class EntryBytes(EntryConstruct):
    construct: t.Union["cs.Bytes[Any, Any]", "cs.Construct[bytes, bytes]"]

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: t.Union["cs.Bytes[Any, Any]", "cs.Construct[bytes, bytes]"],
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)
        self.ascii_view = False

    @property
    def obj_str(self) -> str:
        try:
            if self.ascii_view:
                chars = []
                for b in self.obj:
                    char = chr(b)
                    if char not in string.printable:
                        char = "."
                    chars.append(char)
                return "".join(chars)
            else:
                return self.obj.hex(" ")
        except Exception:
            return str(self.obj)

    @property
    def typ_str(self) -> str:
        obj = self.obj

        if isinstance(self.construct, cs.Bytes):
            try:
                metadata = get_gui_metadata(obj)
                length = evaluate(self.construct.length, metadata["context"])
                return f"Byte[{length}]"
            except Exception:
                return f"Byte[{self.construct.length}]"
        else:
            try:
                return f"Byte[{len(self.obj)}]"
            except Exception:
                return "GreedyBytes"

    def create_obj_panel(self, parent) -> ObjPanel:
        return ObjPanel_Bytes(parent, self)

    def modify_context_menu(self, menu: "construct_editor.ContextMenu"):
        menu.Append(wx.MenuItem(menu, wx.ID_ANY, kind=wx.ITEM_SEPARATOR))

        def on_menu_item_clicked(event: wx.MenuEvent):
            self.ascii_view = not self.ascii_view
            menu.parent.reload()

        menu_item = wx.MenuItem(menu, wx.ID_ANY, "ASCII View", kind=wx.ITEM_CHECK)
        menu.Append(menu_item)
        menu_item.Check(self.ascii_view)
        menu.Bind(wx.EVT_MENU, on_menu_item_clicked, menu_item)


# EntryTell ###########################################################################################################
class EntryTell(EntryConstruct):
    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Construct[Any, Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        return "Tell"


# EntrySeek ###########################################################################################################
class EntrySeek(EntryConstruct):
    construct: "cs.Seek"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Seek",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        return "Seek"

    @property
    def obj_str(self) -> str:
        return ""


# EntryPass ###########################################################################################################
class EntryPass(EntryConstruct):
    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Construct[None, None]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        return "Pass"

    @property
    def obj_str(self) -> str:
        return ""


# EntryComputed ###########################################################################################################
class EntryComputed(EntryConstruct):
    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Computed[Any, Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        return "Computed"

    @property
    def obj_str(self) -> str:
        if isinstance(self.obj, (bytes, bytearray, memoryview)):
            return self.obj.hex(" ")
        else:
            return str(self.obj)


# EntryTimestamp ###########################################################################################################
class EntryTimestamp(EntrySubconstruct):
    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.TimestampAdapter[Any, Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def obj_str(self) -> str:
        return str(self.obj)

    def create_obj_panel(self, parent) -> ObjPanel:
        return ObjPanel_Timestamp(parent, self)


# EntryTransparentSubcon ##############################################################################################
class EntryTransparentSubcon(EntrySubconstruct):
    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Subconstruct[Any, Any, Any, Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)


# EntryPeek ###########################################################################################################
class EntryPeek(EntrySubconstruct):
    construct: "cs.Peek"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Peek",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)


# EntryRawCopy #######################################################################################################
class EntryRawCopy(EntrySubconstruct):
    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.RawCopy[Any, Any, Any, Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

        # change default row infos


# EntryDataclassStruct ################################################################################################
class EntryDataclassStruct(EntrySubconstruct):
    construct: "cst.DataclassStruct[Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cst.DataclassStruct[Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        subentries = super().subentries
        if (subentries is not None) and self.construct.reverse:
            return list(reversed(subentries))
        return subentries

    @property
    def typ_str(self) -> str:
        return self.construct.dc_type.__name__


# EntryFlag ####################################################################################################
class EntryFlag(EntryConstruct):
    construct: "cs.FormatField[Any, Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.FormatField[Any, Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    def create_obj_panel(self, parent) -> ObjPanel:
        return ObjPanel_Flag(parent, self)

    @property
    def obj_str(self) -> str:
        obj = self.obj
        return str(bool(obj))

    @property
    def typ_str(self) -> str:
        return "Flag"


# EntryEnum ###########################################################################################################
class EntryEnum(EntrySubconstruct):
    construct: "cs.Enum"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Enum",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        return super().typ_str + " as Enum"

    @property
    def obj_str(self) -> str:
        try:
            return f"{int_to_str(self.model.integer_format, int(self.obj))} ({str(self.obj)})"
        except Exception:
            return str(self.obj)

    def create_obj_panel(self, parent) -> ObjPanel:
        return ObjPanel_Enum(parent, self)

    def get_enum_items(self) -> t.List[EnumItem]:
        """ Get items to show in the ComboBox """
        items: t.List[EnumItem] = []
        enums = self.construct.encmapping
        for name, value in enums.items():
            items.append(EnumItem(name=name, value=value))
        return items

    def get_enum_item_from_obj(self) -> EnumItem:
        """ Get items to select in the ComboBox """
        obj = self.obj
        if isinstance(obj, int):
            if obj in self.construct.decmapping:
                return EnumItem(
                    name=str(self.construct.decmapping[obj]), value=int(obj)
                )
            else:
                return EnumItem(name=str(obj), value=int(obj))
        else:
            return EnumItem(name=str(obj), value=int(self.construct.encmapping[obj]))

    def conv_str_to_obj(self, s: str) -> Any:
        """ Convert string (enum name or integer value) to object """
        try:
            if s in self.construct.encmapping:
                value = self.construct.encmapping[s]  # type: ignore
            else:
                value = str_to_int(s)

            if value in self.construct.decmapping:
                new_obj = self.construct.decmapping[value]
            else:
                new_obj = cs.EnumInteger(value)
        except Exception:
            new_obj = s  # this will probably result in a binary-build-error
        return new_obj


# EntryFlagsEnum ######################################################################################################
class EntryFlagsEnum(EntrySubconstruct):
    construct: "cs.FlagsEnum"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.FlagsEnum",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        return super().typ_str + " as Flags"

    @property
    def obj_str(self) -> str:
        return self.conv_obj_to_str(self.obj)

    def create_obj_panel(self, parent) -> ObjPanel:
        return ObjPanel_FlagsEnum(parent, self)

    def conv_obj_to_str(self, obj: Any) -> str:
        try:
            val = 0
            flags = []
            for flag in self.construct.flags.keys():
                if obj[flag] is True:
                    flags.append(flag)
                    val |= self.construct.flags[flag]
            return f"{int_to_str(self.model.integer_format, int(val))} ({' | '.join(flags)})"
        except Exception:
            return str(self.obj)

    def get_flagsenum_items_from_obj(self) -> t.List[FlagsEnumItem]:
        """ Get items to show in the ComboBox """
        items: t.List[FlagsEnumItem] = []
        flags = self.construct.flags
        obj = self.obj
        for flag in flags.keys():
            items.append(
                FlagsEnumItem(name=str(flag), value=flags[flag], checked=obj[flag])
            )
        return items

    def conv_flagsenum_items_to_obj(self, items: t.List[FlagsEnumItem]) -> Any:
        """ Convert flagsenum items to object """
        new_obj = cs.Container()
        for item in items:
            if item.checked:
                new_obj[item.name] = True
            else:
                new_obj[item.name] = False
        return new_obj


# EntryTEnum ##########################################################################################################
class EntryTEnum(EntrySubconstruct):
    construct: "cst.TEnum[Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cst.TEnum[Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        return super().typ_str + " as Enum"

    @property
    def obj_str(self) -> str:
        try:
            return f"{int_to_str(self.model.integer_format, int(self.obj.value))} ({str(self.obj)})"
        except Exception:
            return str(self.obj)

    def create_obj_panel(self, parent) -> ObjPanel:
        return ObjPanel_Enum(parent, self)

    def get_enum_items(self) -> t.List[EnumItem]:
        """ Get items to show in the ComboBox """
        items: t.List[EnumItem] = []
        enum_type: t.Type[cst.EnumBase] = self.construct.enum_type
        for e in enum_type:
            items.append(EnumItem(name=str(e), value=e.value))
        return items

    def get_enum_item_from_obj(self) -> EnumItem:
        """ Get items to select in the ComboBox """
        obj: cst.EnumBase = self.obj
        return EnumItem(name=str(obj), value=obj.value)

    def conv_str_to_obj(self, s: str) -> Any:
        """ Convert string (enum name or integer value) to object """
        enum_type: t.Type[cst.EnumBase] = self.construct.enum_type
        try:
            try:
                new_obj = enum_type[s]
            except KeyError:
                value = str_to_int(s)
                new_obj = enum_type(value)
        except Exception:
            new_obj = s  # this will probably result in a binary-build-error
        return new_obj


# EntryTFlagsEnum #####################################################################################################
class EntryTFlagsEnum(EntrySubconstruct):
    construct: "cst.TFlagsEnum[Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cst.TFlagsEnum[Any]",
        name: NameType,
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        return super().typ_str + " as Flags"

    @property
    def obj_str(self) -> str:
        return self.conv_obj_to_str(self.obj)

    def create_obj_panel(self, parent) -> ObjPanel:
        return ObjPanel_FlagsEnum(parent, self)

    def conv_obj_to_str(self, obj: Any) -> str:
        try:
            flags = []
            for flag in self.construct.enum_type:
                if flag & obj == flag:
                    flags.append(flag.name)

            return f"{int_to_str(self.model.integer_format, int(obj))} ({' | '.join(flags)})"
        except Exception:
            return str(self.obj)

    def get_flagsenum_items_from_obj(self) -> t.List[FlagsEnumItem]:
        """ Get items to show in the ComboBox """
        items: t.List[FlagsEnumItem] = []
        enum_type: t.Type[cst.FlagsEnumBase] = self.construct.enum_type
        obj: cst.FlagsEnumBase = self.obj
        for flag in enum_type:
            items.append(
                FlagsEnumItem(
                    name=str(flag),
                    value=flag.value,
                    checked=True if flag & obj == flag else False,
                )
            )
        return items

    def conv_flagsenum_items_to_obj(self, items: t.List[FlagsEnumItem]) -> Any:
        """ Convert flagsenum items to object """
        enum_type: t.Type[cst.FlagsEnumBase] = self.construct.enum_type
        new_obj = enum_type(0)
        for item in items:
            if item.checked:
                new_obj |= enum_type(item.value)
        return new_obj


# #####################################################################################################################
# Entry Mapping #######################################################################################################
# #####################################################################################################################
construct_entry_mapping: t.Dict[
    t.Union[Type["cs.Construct[Any, Any]"], "cs.Construct[Any, Any]"],
    Type[EntryConstruct],
] = {
    # #########################################################################
    # wrapper from: construct #################################################
    # #########################################################################
    # bytes and bits ############################
    cs.Bytes: EntryBytes,
    cs.GreedyBytes: EntryBytes,
    # cs.Bitwise
    # cs.Bytewise
    #
    # integers and floats #######################
    cs.FormatField: EntryFormatField,
    cs.BytesInteger: EntryBytesInteger,
    cs.BitsInteger: EntryBitsInteger,
    #
    # strings ###################################
    # cs.StringEncoded
    #
    # mappings ##################################
    cs.Flag: EntryFlag,
    cs.Enum: EntryEnum,
    cs.FlagsEnum: EntryFlagsEnum,
    # cs.Mapping
    #
    # structures and sequences ##################
    cs.Struct: EntryStruct,
    # cs.Sequence
    #
    # arrays ranges and repeaters ###############
    cs.Array: EntryArray,
    cs.GreedyRange: EntryArray,
    # cs.RepeatUntil
    #
    # specials ##################################
    # cs.Renamed  # this is skipped
    #
    # miscellaneous #############################
    cs.Const: EntryTransparentSubcon,
    cs.Computed: EntryComputed,
    # cs.Index
    # cs.Rebuild
    cs.Default: EntryTransparentSubcon,
    # cs.Check
    # cs.Error
    # cs.FocusedSeq
    # cs.Pickled
    # cs.Numpy
    # cs.NamedTuple
    cs.TimestampAdapter: EntryTimestamp,
    # cs.Hex
    # cs.HexDump
    #
    # conditional ###############################
    # cs.Union
    # cs.Select
    cs.IfThenElse: EntryIfThenElse,
    cs.Switch: EntrySwitch,
    # cs.StopIf
    #
    # alignment and padding #####################
    cs.Padded: EntryTransparentSubcon,
    cs.Aligned: EntryTransparentSubcon,
    #
    # stream manipulation #######################
    cs.Pointer: EntryTransparentSubcon,
    cs.Peek: EntryPeek,
    cs.Seek: EntrySeek,
    cs.Tell: EntryTell,
    cs.Pass: EntryPass,
    # cs.Terminated
    #
    # tunneling and byte/bit swapping ###########
    cs.RawCopy: EntryRawCopy,
    # cs.Prefixed
    cs.FixedSized: EntryTransparentSubcon,
    # cs.NullTerminated
    # cs.NullStripped
    # cs.RestreamData
    cs.Transformed: EntryTransparentSubcon,
    cs.Restreamed: EntryTransparentSubcon,
    # cs.ProcessXor
    # cs.ProcessRotateLeft
    # cs.Checksum
    # cs.Compressed
    # cs.CompressedLZ4
    # cs.Rebuffered
    #
    # lazy equivalents ##########################
    # cs.Lazy
    # cs.LazyStruct
    # cs.LazyArray
    # cs.LazyBound
    # #########################################################################
    #
    #
    # #########################################################################
    # wrapper from: construct_typing ##########################################
    # #########################################################################
    cst.DataclassStruct: EntryDataclassStruct,
    cst.TEnum: EntryTEnum,
    cst.TFlagsEnum: EntryTFlagsEnum,
    # #########################################################################
    #
    #
    # #########################################################################
    # wrapper from: construct_editor ##########################################
    # #########################################################################
    # IncludeGuiMetaData  # this is skipped
    # #########################################################################
}


def create_entry_from_construct(
    model: "construct_editor.ConstructEditorModel",
    parent: Optional["EntryConstruct"],
    subcon: "cs.Construct[Any, Any]",
    name: NameType,
    docs: str,
) -> "EntryConstruct":

    # Process and then skip Renamed, to fasten up large arrays
    if isinstance(subcon, cs.Renamed):
        if subcon.name is not None:
            name = subcon.name

        if subcon.docs != "":
            docs = subcon.docs

        return create_entry_from_construct(model, parent, subcon.subcon, name, docs)

    # Skip IncludeGuiMetaData, to fasten up large arrays
    if isinstance(subcon, IncludeGuiMetaData):
        return create_entry_from_construct(model, parent, subcon.subcon, name, docs)

    # check for instance-mappings
    if subcon in construct_entry_mapping:
        return construct_entry_mapping[subcon](model, parent, subcon, name, docs)

    # check for class-mappings
    if type(subcon) in construct_entry_mapping:
        return construct_entry_mapping[type(subcon)](model, parent, subcon, name, docs)

    # iterate through all mappings and check if the subcon inherits from a known mapping
    for key, value in construct_entry_mapping.items():
        if isinstance(key, type) and isinstance(subcon, key):  # type: ignore
            return value(model, parent, subcon, name, docs)

    # use fallback, if no entry found in the mapping
    if isinstance(subcon, cs.Construct):
        return EntryConstruct(model, parent, subcon, name, docs)

    raise ValueError(f"subcon type {repr(subcon)} is not implemented")
