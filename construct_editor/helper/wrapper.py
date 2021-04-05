from typing import Any, Dict, List, Optional, Type, Union
import typing as t

import construct as cs
import construct_typed as cst

import arrow
import wx
import wx.adv
from construct_editor.helper.preprocessor import (
    IncludeGuiMetaData,
    GuiMetaData,
    get_gui_metadata,
    add_gui_metadata,
)

import construct_editor.widgets.construct_editor as construct_editor


def evaluate(param, context):
    return param(context) if callable(param) else param


def int_to_str(val: int) -> str:
    if val < 10:
        return f"{val}"
    else:
        return f"{val}   /   0x{val:X}"


# #####################################################################################################################
# GUI Elements ########################################################################################################
# #####################################################################################################################
def create_obj_panel_default_class(entry: "EntryConstruct") -> Type[wx.Panel]:
    class ObjPanel(wx.Panel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # Test if the obj of the entry is available
            if entry.obj is None:
                return

            # Obj
            hsizer = wx.BoxSizer(wx.HORIZONTAL)
            self.obj_txt = wx.TextCtrl(
                self,
                wx.ID_ANY,
                entry.obj_str,
                wx.DefaultPosition,
                wx.Size(-1, -1),
                wx.TE_READONLY,
            )
            hsizer.Add(self.obj_txt, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)

            self.SetSizer(hsizer)
            self.Layout()

    return ObjPanel


def create_obj_panel_integer_class_factory(entry: "EntryConstruct"):
    class ObjPanel(wx.Panel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # Test if the obj of the entry is available
            if entry.obj is None:
                return

            # Obj
            hsizer = wx.BoxSizer(wx.HORIZONTAL)
            self.obj_txtctrl = wx.TextCtrl(
                self, wx.ID_ANY, entry.obj_str, wx.DefaultPosition, wx.DefaultSize, 0
            )
            hsizer.Add(self.obj_txtctrl, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)

            self.SetSizer(hsizer)
            self.Layout()

            # Connect Events
            self.obj_txtctrl.Bind(wx.EVT_TEXT, self._on_obj_changed)

        def _on_obj_changed(self, event):
            val_str: str = self.obj_txtctrl.GetValue()
            if len(val_str) == 0:
                val_str = "0"

            try:
                new_value = int(
                    val_str, base=0
                )  # base=0 means, that eg. 0x, 0b prefixes are allowed
            except Exception:
                new_value = val_str  # this will probably result in a building error

            metadata = get_gui_metadata(entry.obj)
            if metadata is not None:
                entry.obj = add_gui_metadata(new_value, metadata)
            else:
                entry.obj = new_value

            entry.model.ItemChanged(entry.dvc_item)
            if entry.model._on_obj_changed is not None:
                entry.model._on_obj_changed()

    return ObjPanel


def create_obj_panel_enum_class_factory(entry: Union["EntryTEnum", "EntryEnum"]):
    class ObjPanel(wx.Panel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # Test if the obj of the entry is available
            if entry.obj is None:
                return

            # Obj
            hsizer = wx.BoxSizer(wx.HORIZONTAL)

            if isinstance(entry, EntryTEnum):
                choices = [f"{e.value} ({str(e)})" for e in entry.construct.enum_type]
            elif isinstance(entry, EntryEnum):
                choices = [
                    f"{value} ({str(name)})"
                    for value, name in entry.construct.decmapping.items()
                ]

            selection = entry.obj_str
            self.obj_combobox = wx.ComboBox(
                self,
                wx.ID_ANY,
                selection,
                wx.DefaultPosition,
                wx.DefaultSize,
                choices,
                wx.CB_DROPDOWN,
            )
            hsizer.Add(self.obj_combobox, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)

            self.SetSizer(hsizer)
            self.Layout()

            # Connect Events
            self.obj_combobox.Bind(wx.EVT_COMBOBOX, self._on_obj_changed)
            self.obj_combobox.Bind(wx.EVT_TEXT, self._on_obj_changed)

        def _on_obj_changed(self, event):
            val_str: str = self.obj_combobox.GetValue()
            if len(val_str) == 0:
                val_str = "0"

            val_int = int(val_str.split()[0])
            try:
                if isinstance(entry, EntryTEnum):
                    enum_type = entry.construct.enum_type
                    new_value = enum_type(val_int)
                elif isinstance(entry, EntryEnum):
                    new_value = entry.construct.decmapping[val_int]
            except Exception:
                new_value = val_int  # this will probably result in a building error

            metadata = get_gui_metadata(entry.obj)
            if metadata is not None:
                entry.obj = add_gui_metadata(new_value, metadata)
            else:
                entry.obj = new_value

            entry.model.ItemChanged(entry.dvc_item)
            if entry.model._on_obj_changed is not None:
                entry.model._on_obj_changed()

    return ObjPanel


class FlagsEnumComboPopup(wx.ComboPopup):
    def __init__(self, entry: "EntryFlagsEnum", on_obj_changed: t.Callable[[], None]):
        super().__init__()
        self.entry = entry
        self.on_obj_changed = on_obj_changed
        self.clbx: Optional[wx.CheckListBox] = None

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

            # remove unused characters from the checked items
            items_str = []
            for item_str in self.clbx.GetCheckedStrings():
                items_str.append(item_str.split()[1].strip("()"))

            # change the object of the entry
            obj = self.entry.obj
            for key in obj.keys():
                if key.startswith("_"):
                    continue
                if key in items_str:
                    obj[key] = True
                else:
                    obj[key] = False

            # call callback
            self.on_obj_changed()

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
        return wx.ComboPopup.GetAdjustedSize(self, minWidth, 110, maxHeight)


def create_obj_panel_flags_enum_class_factory(entry: "EntryFlagsEnum"):
    class ObjPanel(wx.Panel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            obj = entry.obj

            # Test if the obj of the entry is available
            if obj is None:
                return

            # Obj
            hsizer = wx.BoxSizer(wx.HORIZONTAL)

            choices = [
                f"{value} ({str(name)})"
                for name, value in entry.construct.flags.items()
            ]
            checked_items = []
            for key in obj.keys():
                if key.startswith("_"):
                    continue
                if obj[key]:
                    checked_items.append(len(checked_items))

            self.combo_ctrl = wx.ComboCtrl(self, style=wx.CB_READONLY)
            self.popup_ctrl = FlagsEnumComboPopup(entry, self._on_obj_changed)
            self.combo_ctrl.SetPopupControl(self.popup_ctrl)

            self.popup_ctrl.clbx.InsertItems(choices, 0)
            self.popup_ctrl.clbx.SetCheckedItems(checked_items)
            self.combo_ctrl.SetValue(entry.obj_str)

            hsizer.Add(self.combo_ctrl, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 0)

            self.SetSizer(hsizer)
            self.Layout()

        def _on_obj_changed(self):
            self.combo_ctrl.SetValue(entry.obj_str)

            entry.model.ItemChanged(entry.dvc_item)
            if entry.model._on_obj_changed is not None:
                entry.model._on_obj_changed()

    return ObjPanel


def create_obj_panel_timestamp_class_factory(entry: "EntryTimestamp"):
    class ObjPanel(wx.Panel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # Test if the obj of the entry is available
            if entry.obj is None:
                return
            if not isinstance(entry.obj, arrow.Arrow):
                return

            # Obj
            hsizer = wx.BoxSizer(wx.HORIZONTAL)
            dt = entry.obj.datetime
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
                entry.obj_str,
                wx.DefaultPosition,
                wx.DefaultSize,
                wx.TE_READONLY,
            )
            hsizer.Add(self.obj_txtctrl, 1, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)

            self.SetSizer(hsizer)
            self.Layout()

            # Connect Events
            self.date_picker.Bind(wx.adv.EVT_DATE_CHANGED, self._on_obj_changed)
            self.time_picker.Bind(wx.adv.EVT_TIME_CHANGED, self._on_obj_changed)

        def _on_obj_changed(self, event):
            date: wx.DateTime = self.date_picker.GetValue()
            time: wx.DateTime = self.time_picker.GetValue()
            new_value = arrow.Arrow(
                year=date.year,
                month=date.month + 1,  # in wx.adc.DatePickerCtrl the month start with 0
                day=date.day,
                hour=time.hour,
                minute=time.minute,
                second=time.second,
            )

            metadata = get_gui_metadata(entry.obj)
            if metadata is not None:
                entry.obj = add_gui_metadata(new_value, metadata)
            else:
                entry.obj = new_value

            self.obj_txtctrl.SetValue(entry.obj_str)

            entry.model.ItemChanged(entry.dvc_item)
            if entry.model._on_obj_changed is not None:
                entry.model._on_obj_changed()

    return ObjPanel


# #####################################################################################################################
# DVC Entries #########################################################################################################
# #####################################################################################################################

# EntryConstruct ######################################################################################################
class EntryConstruct(object):
    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Construct[Any, Any]",
        root_obj: Optional[Any],
    ):
        self.model = model
        self._parent = parent
        self._construct = construct

        # This is only set at the root entry. Otherwise it is None.
        self._root_obj = root_obj

        # This is set from the model, when the dvc item for this entry is created.
        self._dvc_item = None

    # default "parent" ########################################################
    @property
    def parent(self) -> Optional["EntryConstruct"]:
        return self._parent

    # default "construct" #####################################################
    @property
    def construct(self) -> "cs.Construct[Any, Any]":
        return self._construct

    # default "root_obj" ######################################################
    @property
    def root_obj(self) -> Any:
        if self._root_obj is not None:
            return self._root_obj
        if self.parent is not None:
            return self.parent.root_obj
        return None

    # default "obj" ###########################################################
    @property
    def obj(self) -> Any:
        path = self.path
        obj = self.root_obj
        for p in path:
            if isinstance(obj, dict):
                obj = obj[p]
            elif isinstance(obj, list):
                obj = obj[int(p)]
        return obj

    @obj.setter
    def obj(self, val: Any):
        path = self.path
        obj = self.root_obj
        for p in path[:-1]:
            if isinstance(obj, dict):
                obj = obj[p]
            elif isinstance(obj, list):
                obj = obj[int(p)]

        if isinstance(obj, dict):
            obj[path[-1]] = val
        elif isinstance(obj, list):
            obj[int(path[-1])] = val

    # default "name" ##########################################################
    @property
    def name(self) -> str:
        if self.construct.name is not None:
            return self.construct.name
        else:
            return ""

    # default "docs" ##########################################################
    @property
    def docs(self) -> str:
        return self.construct.docs

    # default "obj_str" #######################################################
    @property
    def obj_str(self) -> str:
        return str(self.obj)

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
    def dvc_item(self, val) -> Any:
        self._dvc_item = val

    # default "obj_panel_class" ###############################################
    @property
    def obj_panel_class(self) -> Type[wx.Panel]:
        return create_obj_panel_default_class(self)

    # default "path" ##########################################################
    @property
    def path(self) -> List[str]:
        parent = self.parent
        if parent is not None:
            path = parent.path

            # Append name if available
            name = self.name
            if name != "":
                path.append(name)
        else:
            path = []

        return path


# EntrySubconstruct ###################################################################################################
class EntrySubconstruct(EntryConstruct):
    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Subconstruct[Any, Any, Any, Any]",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

        self.subentry = model.create_construct_entry(self, construct.subcon, None)

    # pass throught "obj_str" to subentry #####################################
    @property
    def obj_str(self) -> Any:
        return self.subentry.obj_str

    # pass throught "typ_str" to subentry #####################################
    @property
    def typ_str(self) -> Any:
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

    # default "obj_panel_class" ###############################################
    @property
    def obj_panel_class(self) -> Type[wx.Panel]:
        return self.subentry.obj_panel_class


# EntryStruct #########################################################################################################
class EntryStruct(EntryConstruct):
    construct: "cs.Struct[Any, Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Struct[Any, Any]",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

        # change default row infos
        self._subentries = []

        # create sub entries
        for subcon in self.construct.subcons:
            subentry = self.model.create_construct_entry(
                self,
                subcon,
                None,
            )
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

    @property
    def obj_panel_class(self) -> Type[wx.Panel]:
        return create_obj_panel_default_class(self)  # TODO: create panel for cs.Struct


# EntryArray ##########################################################################################################
class EntryArray(EntrySubconstruct):
    construct: "cs.Array[Any, Any, Any, Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Array[Any, Any, Any, Any]",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

        self._subentries = []

    @property
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        # get length of array
        try:
            array_len = len(self.obj)
        except Exception:
            if isinstance(self.construct.count, int):
                array_len = self.construct.count
            else:
                array_len = 1

        # append entries if not appended yet
        if len(self._subentries) != array_len:
            self._subentries.clear()
            for index in range(0, array_len):
                self.insert_entry(index)

        return self._subentries

    def insert_entry(self, index: int):
        subentry = self.model.create_construct_entry(
            self,
            cs.Renamed(self.construct.subcon, newname=str(index)),
            None,
        )
        self._subentries.append(subentry)

    @property
    def typ_str(self) -> str:
        try:
            return f"Array[{len(self.obj)}]"
        except Exception:
            return f"Array[{str(self.construct.count)}]"

    @property
    def obj_str(self) -> str:
        return ""

    @property
    def obj_panel_class(self) -> Type[wx.Panel]:
        return create_obj_panel_default_class(self)  # TODO: create panel for cs.Array


# EntryGreedyRange ####################################################################################################
class EntryGreedyRange(EntrySubconstruct):
    construct: "cs.GreedyRange[Any, Any, Any, Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.GreedyRange[Any, Any, Any, Any]",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

        self._subentries = []

    @property
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        # get length of array
        try:
            array_len = len(self.obj)
        except Exception:
            array_len = 1

        # append entries if not appended yet
        if len(self._subentries) != array_len:
            self._subentries.clear()
            for index in range(0, array_len):
                self.insert_entry(index)

        return self._subentries

    def insert_entry(self, index: int):
        subentry = self.model.create_construct_entry(
            self,
            cs.Renamed(self.construct.subcon, newname=str(index)),
            None,
        )
        self._subentries.append(subentry)

    @property
    def typ_str(self) -> str:
        try:
            return f"GreedyRange[{len(self.obj)}]"
        except Exception:
            return f"GreedyRange"

    @property
    def obj_str(self) -> str:
        return ""

    @property
    def obj_panel_class(self) -> Type[wx.Panel]:
        return create_obj_panel_default_class(self)  # TODO: create panel for cs.Array


# EntryIfThenElse #####################################################################################################
class EntryIfThenElse(EntryConstruct):
    construct: "cs.IfThenElse[Any, Any, Any, Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.IfThenElse[Any, Any, Any, Any]",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

        self._subentry_then = EntryRenamed(
            self.model,
            self,
            cs.Renamed(
                self.construct.thensubcon, newname=f"If {self.construct.condfunc} then"
            ),
            None,
            exclude_from_path=True,
        )
        self._subentry_else = EntryRenamed(
            self.model,
            self,
            cs.Renamed(self.construct.elsesubcon, newname=f"Else"),
            None,
            exclude_from_path=True,
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
            cond = evaluate(self.construct.condfunc, metadata.context)
            if cond:
                return self._subentry_then.subentry
            else:
                return self._subentry_else.subentry

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
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        subentry = self._get_subentry()
        if subentry is None:
            return self._subentries
        else:
            return subentry.subentries

    @property
    def obj_panel_class(self) -> Type[wx.Panel]:
        subentry = self._get_subentry()
        if subentry is None:
            return create_obj_panel_default_class(self)
        else:
            return subentry.obj_panel_class


# EntrySwitch #########################################################################################################
class EntrySwitch(EntryConstruct):
    construct: "cs.Switch[Any, Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Switch[Any, Any]",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

        self._subentries: List[EntryConstruct] = []
        self._subentry_cases: Dict[str, EntryConstruct] = {}
        self._subentry_default: Optional[EntryConstruct] = None
        self.construct.cases
        self.construct.default

        for key, value in self.construct.cases.items():
            subentry_case = EntryRenamed(
                self.model,
                self,
                cs.Renamed(
                    value, newname=f"Case {self.construct.keyfunc} == {str(key)}"
                ),
                None,
                exclude_from_path=True,
            )
            self._subentry_cases[key] = subentry_case
            self._subentries.append(subentry_case)

        if self.construct.default is not None:
            self._subentry_default = EntryRenamed(
                self.model,
                self,
                cs.Renamed(self.construct.default, newname=f"Default"),
                None,
                exclude_from_path=True,
            )
            self._subentries.append(self._subentry_default)

    def _get_subentry(self) -> "Optional[EntryConstruct]":
        """ Evaluate the conditional function to detect the type of the subentry """
        obj = self.obj
        if obj is None:
            return None
        else:
            metadata = get_gui_metadata(obj)
            key = evaluate(self.construct.keyfunc, metadata.context)
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
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        subentry = self._get_subentry()
        if subentry is None:
            return self._subentries
        else:
            return subentry.subentries

    @property
    def obj_panel_class(self) -> Type[wx.Panel]:
        subentry = self._get_subentry()
        if subentry is None:
            return create_obj_panel_default_class(self)
        else:
            return subentry.obj_panel_class


# EntryFormatField ####################################################################################################
class EntryFormatField(EntryConstruct):
    construct: "cs.FormatField[Any, Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.FormatField[Any, Any]",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

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

        # change default row infos
        self.type_infos = None
        if construct.fmtstr in type_mapping:
            self.type_infos = type_mapping[construct.fmtstr]

    @property
    def obj_panel_class(self) -> Type[wx.Panel]:
        if self.type_infos[1] is int:
            return create_obj_panel_integer_class_factory(self)
        else:
            return create_obj_panel_default_class(self)  # TODO: float

    @property
    def obj_str(self) -> str:
        obj = self.obj
        if (obj is None) or (self.type_infos[1] is not int):
            return str(obj)
        else:
            return int_to_str(obj)

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
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

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
            return int_to_str(obj)

    @property
    def obj_panel_class(self) -> Type[wx.Panel]:
        if isinstance(self.construct.length, int):
            return create_obj_panel_integer_class_factory(self)
        else:
            return create_obj_panel_default_class(self)


# EntryBitsInteger ####################################################################################################
class EntryBitsInteger(EntryConstruct):
    construct: "cs.BitsInteger[Any, Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.BitsInteger[Any, Any]",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

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
            return int_to_str(obj)

    @property
    def obj_panel_class(self) -> Type[wx.Panel]:
        if isinstance(self.construct.length, int):
            return create_obj_panel_integer_class_factory(self)
        else:
            return create_obj_panel_default_class(self)


# EntryBytes ##########################################################################################################
class EntryBytes(EntryConstruct):
    construct: "cs.Bytes[Any, Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Bytes[Any, Any]",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

    @property
    def obj_str(self) -> str:
        try:
            return self.obj.hex(" ")
        except Exception:
            return str(self.obj)

    @property
    def typ_str(self) -> str:
        # change default row infos
        try:
            return "Byte[{}]".format(len(self.obj))
        except Exception:
            return "Byte[{}]".format(str(self.construct.length))


# EntryRenamed ########################################################################################################
class EntryRenamed(EntrySubconstruct):
    construct: "cs.Renamed[Any, Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Renamed[Any, Any]",
        root_obj: Optional[Any],
        exclude_from_path: bool = False,
    ):
        super().__init__(model, parent, construct, root_obj)
        self._exclude_from_path = exclude_from_path

        # This is for the case, when nesting Renamed like this: `Renamed(Renamed(Int8sb, newname=...), newdocs=...)`
        # because both Renamed elements have the same name, but we only need it one time. So all other cases
        # are excluded.
        if self.construct.name == self.construct.subcon.name:
            self._exclude_from_path = True

    # modified "path" #########################################################
    @property
    def path(self) -> List[str]:
        if self._exclude_from_path:
            if self.parent is not None:
                return self.parent.path
            else:
                return []
        else:
            return super().path


# EntryTell ###########################################################################################################
class EntryTell(EntryConstruct):
    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Construct[Any, Any]",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

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
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

    @property
    def typ_str(self) -> str:
        return "Seek"

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
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

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
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

    @property
    def obj_str(self) -> str:
        if isinstance(self.obj, (arrow.Arrow)):
            return self.obj.format("YYYY-MM-DD HH:mm:ss ZZ")
        else:
            return str(self.obj)

    @property
    def obj_panel_class(self) -> Type[wx.Panel]:
        return create_obj_panel_timestamp_class_factory(self)


# EntryTransparentSubcon ##############################################################################################
class EntryTransparentSubcon(EntrySubconstruct):
    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Subconstruct[Any, Any, Any, Any]",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)


# EntryPeek ###########################################################################################################
class EntryPeek(EntrySubconstruct):
    construct: "cs.Peek"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Peek",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)


# EntryRawCopy #######################################################################################################
class EntryRawCopy(EntrySubconstruct):
    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.RawCopy[Any, Any, Any, Any]",
        root_obj: Optional[Any],
    ):
        subcon_obj = None
        if self.obj is not None:
            subcon_obj = root_obj.obj
        super().__init__(model, parent, construct, subcon_obj)

        # change default row infos


# EntryTStruct #######################################################################################################
class EntryTStruct(EntrySubconstruct):
    construct: "cst.TStruct[Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cst.TStruct[Any]",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

    @property
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        subentries = super().subentries
        if (subentries is not None) and self.construct.reverse:
            return list(reversed(subentries))
        return subentries

    @property
    def typ_str(self) -> str:
        return "TStruct"


# EntryTBitStruct #######################################################################################################
class EntryTBitStruct(EntrySubconstruct):
    construct: "cst.TBitStruct[Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cst.TBitStruct[Any]",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

    @property
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        subentries = super().subentries
        if (subentries is not None) and self.construct.reverse:
            return list(reversed(subentries))
        return subentries

    @property
    def typ_str(self) -> str:
        return "TBitStruct"


# EntryEnum ###########################################################################################################
class EntryEnum(EntrySubconstruct):
    construct: "cs.Enum"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Enum",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

    @property
    def typ_str(self) -> Any:
        return super().typ_str + " as Enum"

    @property
    def obj_str(self) -> str:
        try:
            return f"{int(self.obj)} ({str(self.obj)})"
        except Exception:
            return str(self.obj)

    @property
    def obj_panel_class(self) -> Type[wx.Panel]:
        return create_obj_panel_enum_class_factory(self)


# EntryFlagsEnum ######################################################################################################
class EntryFlagsEnum(EntrySubconstruct):
    construct: "cs.FlagsEnum"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.FlagsEnum",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

    @property
    def typ_str(self) -> Any:
        return super().typ_str + " as Flags"

    @property
    def obj_str(self) -> str:
        try:
            obj = self.obj
            flags = []
            for key, value in obj.items():
                if key.startswith("_"):
                    continue
                if obj[key]:
                    flags.append(key)
            return " | ".join(flags)
        except Exception:
            return str(self.obj)

    @property
    def obj_panel_class(self) -> Type[wx.Panel]:
        return create_obj_panel_flags_enum_class_factory(self)


# EntryTEnum ##########################################################################################################
class EntryTEnum(EntrySubconstruct):
    construct: "cst.TEnum[Any]"

    def __init__(
        self,
        model: "construct_editor.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cst.TEnum[Any]",
        root_obj: Optional[Any],
    ):
        super().__init__(model, parent, construct, root_obj)

    @property
    def typ_str(self) -> Any:
        return super().typ_str + " as Enum"

    @property
    def obj_str(self) -> str:
        try:
            return f"{self.obj.value} ({str(self.obj)})"
        except Exception:
            return str(self.obj)

    @property
    def obj_panel_class(self) -> Type[wx.Panel]:
        return create_obj_panel_enum_class_factory(self)


# #####################################################################################################################
# Entry Mapping #######################################################################################################
# #####################################################################################################################
entry_mapping_construct: Dict[Type["cs.Construct[Any, Any]"], Type[EntryConstruct]] = {
    # wrapper from: construct #################################################
    cs.Array: EntryArray,
    cs.GreedyRange: EntryGreedyRange,
    cs.Struct: EntryStruct,
    cs.IfThenElse: EntryIfThenElse,
    cs.Switch: EntrySwitch,
    cs.FormatField: EntryFormatField,
    cs.BitsInteger: EntryBitsInteger,
    cs.BytesInteger: EntryBytesInteger,
    cs.Bytes: EntryBytes,
    cs.Renamed: EntryRenamed,
    type(cs.Tell): EntryTell,
    cs.Default: EntryTransparentSubcon,
    cs.Pointer: EntryTransparentSubcon,
    cs.Peek: EntryPeek,
    cs.Seek: EntrySeek,
    cs.Transformed: EntryTransparentSubcon,
    cs.Restreamed: EntryTransparentSubcon,
    cs.RawCopy: EntryRawCopy,
    cs.Computed: EntryComputed,
    cs.TimestampAdapter: EntryTimestamp,
    cs.Enum: EntryEnum,
    cs.FlagsEnum: EntryFlagsEnum,
    cs.Const: EntryTransparentSubcon,
    # #########################################################################
    #
    #
    # wrapper from: construct_typing ##########################################
    cst.TStruct: EntryTStruct,
    cst.TBitStruct: EntryTBitStruct,
    cst.TEnum: EntryTEnum,
    # #########################################################################
    #
    #
    # wrapper from: construct_wxpython #########################################
    IncludeGuiMetaData: EntryTransparentSubcon,
    # #########################################################################
}
