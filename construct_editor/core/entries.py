# -*- coding: utf-8 -*-
import dataclasses
import enum
import io
import string
import typing as t
from typing import Any, Dict, List, Optional, Type

import construct as cs
import construct_typed as cst

import construct_editor.core.model as model
from construct_editor.core.context_menu import (
    ButtonMenuItem,
    CheckboxMenuItem,
    ContextMenu,
    SeparatorMenuItem,
)
from construct_editor.core.preprocessor import (
    GuiMetaData,
    IncludeGuiMetaData,
    get_gui_metadata,
)


def evaluate(param, context):
    return param(context) if callable(param) else param


def int_to_str(integer_format: "model.IntegerFormat", val: int) -> str:
    if isinstance(val, str):
        return val  # tolerate string
    if integer_format is model.IntegerFormat.Hex:
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


@dataclasses.dataclass
class ObjViewSettings_Default:
    entry: "EntryConstruct"


@dataclasses.dataclass
class ObjViewSettings_String:
    entry: "EntryConstruct"


@dataclasses.dataclass
class ObjViewSettings_Integer:
    entry: "EntryConstruct"


@dataclasses.dataclass
class ObjViewSettings_Flag:
    entry: "EntryConstruct"


@dataclasses.dataclass
class ObjViewSettings_Bytes:
    entry: "EntryConstruct"


@dataclasses.dataclass
class ObjViewSettings_Enum:
    entry: t.Union["EntryEnum", "EntryTEnum"]


@dataclasses.dataclass
class ObjViewSettings_FlagsEnum:
    entry: t.Union["EntryFlagsEnum", "EntryTFlagsEnum"]


@dataclasses.dataclass
class ObjViewSettings_Timestamp:
    entry: "EntryTimestamp"


ObjViewSettings = t.Union[
    ObjViewSettings_Default,
    ObjViewSettings_String,
    ObjViewSettings_Integer,
    ObjViewSettings_Flag,
    ObjViewSettings_Bytes,
    ObjViewSettings_Enum,
    ObjViewSettings_FlagsEnum,
    ObjViewSettings_Timestamp,
]


def _convert_restreamed(stream: cs.RestreamedBytesIO) -> io.BytesIO:
    """
    Helper method to convert a `RestreamedBytesIO` to a normal `BytesIO`.
    This is eg. nessesary for:
      - `cs.Bitwise(cs.GreedyRange(cs.Bit))`
      - `cs.BitsSwapped(cs.Bitwise(cs.GreedyRange(cs.Bit)))`
    """

    def reset_substream_recursively(stream: t.Union[io.BytesIO, cs.RestreamedBytesIO]):
        if isinstance(stream, cs.RestreamedBytesIO):
            if stream.substream is None:
                raise RuntimeError(
                    "stream.substream has to be io.BytesIO or cs.RestreamedBytesIO"
                )
            return reset_substream_recursively(stream.substream)
        else:
            stream.seek(0)

    # check if there is already a cached version
    bytes_io_stream: t.Optional[io.BytesIO] = getattr(
        stream, "_construct_bytes_io", None
    )

    if bytes_io_stream is None:
        # reset substream recursively, so that the whole RestreamedBytesIO can be read again
        reset_substream_recursively(stream)

        # read the entire RestreamedBytesIO
        data = stream.read()

        # create a new BytesIO with the data of the RestreamedBytesIO
        bytes_io_stream = io.BytesIO(data)

        # cache the created stream, so that we dont have to do it again
        setattr(stream, "_construct_bytes_io", bytes_io_stream)

    return bytes_io_stream


@dataclasses.dataclass
class EnumItem:
    name: str
    value: int


@dataclasses.dataclass
class FlagsEnumItem:
    name: str
    value: int
    checked: bool


@dataclasses.dataclass
class StreamInfo:
    stream: io.BytesIO
    path_str: str
    byte_range: t.Tuple[int, int]
    bitstream: bool


class NameExcludedFromPath(str):
    pass


class ListIndexName(str):
    pass


NameType = t.Union[str, NameExcludedFromPath, ListIndexName]

PathType = t.List[t.Union[str, ListIndexName]]


def create_path_str(path: PathType) -> str:
    path_str = ""
    for p in path:
        if isinstance(p, ListIndexName):
            path_str += f"{p}"
        else:
            path_str += f".{p}"
    if path_str.startswith("."):
        path_str = path_str[1:]
    return path_str


# #####################################################################################################################
# Construct Entries ###################################################################################################
# #####################################################################################################################

# EntryConstruct ######################################################################################################
class EntryConstruct(object):
    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Construct[Any, Any]",
        name: t.Optional[NameType],
        docs: str,
    ):
        self.model = model
        self._parent = parent
        self._construct = construct
        self._name = name
        self._docs = docs

        # Flag, if this entry is an own row in the view.
        # This is nessesarry, because most `subcon` in an `Subconstruct` is not
        # visible as an own row in the view. So to detect the visible row of an
        # entry we can iterate through the parents till we find an visible row.
        self._visible_row: bool = False

        # Flag if this row is expanded or not.
        # Only valid, if self._visible_row is True. This is needed because the
        # expansion state is sometimes not saved in the view itself while reloading
        # the view (eg. in wxPython).
        self._row_expanded: bool = False

    def get_debug_infos(self) -> str:
        s = ""
        s += f"{create_path_str(self.path)}\n"
        s += f"  - name={str(self.name)}\n"
        s += f"  - construct={str(self.construct)}\n"
        s += f"  - entry={self}\n"
        s += f"  - parent={self.parent}\n"
        s += f"  - subentries={self.subentries}"
        s += f"  - visible_row={str(self.visible_row)}\n"
        s += f"  - row_expanded={self.row_expanded}\n"
        s += f"  - visible_row_entry={str(self.get_visible_row_entry())}\n"
        return s

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
                obj = obj[int(p.strip("[]"))]
        return obj

    @obj.setter
    def obj(self, val: Any):
        path = self.path
        obj = self.model.root_obj
        for p in path[1:-1]:
            if isinstance(obj, dict) or isinstance(obj, cst.DataclassMixin):
                obj = obj[p]
            elif isinstance(obj, list):
                obj = obj[int(p.strip("[]"))]

        if isinstance(obj, dict) or isinstance(obj, cst.DataclassMixin):
            obj[path[-1]] = val
        elif isinstance(obj, list):
            obj[int(path[-1].strip("[]"))] = val

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
    def name(self) -> NameType:
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

    # default "visible_row" ###################################################
    @property
    def visible_row(self) -> bool:
        return self._visible_row

    @visible_row.setter
    def visible_row(self, val: bool):
        self._visible_row = val

    # default "get_visible_row_entry" #########################################
    def get_visible_row_entry(self) -> t.Optional["EntryConstruct"]:
        """
        Get the entry that represents the visible row.
        If this is not an visible row, iterate throud all parents till we find
        the visible row.
        """
        # Check if this is the visible row
        if self._visible_row is True:
            return self

        # Check if a parent is available. If not this is the root object
        if self.parent is None:
            return None

        # Recusivly check all parents
        return self.parent.get_visible_row_entry()

    # default "row_expanded" ##################################################
    @property
    def row_expanded(self) -> bool:
        return self._row_expanded

    @row_expanded.setter
    def row_expanded(self, val: bool):
        self._row_expanded = val

    # default "obj_view_settings" #############################################
    @property
    def obj_view_settings(self) -> ObjViewSettings:
        """Settings for the view of an entry (eg. renderer and editor)."""
        return ObjViewSettings_Default(self)

    # default "modify_context_menu" ###########################################
    def modify_context_menu(self, menu: ContextMenu):
        """This method is called, when the user right clicks an entry and a ContextMenu is created"""
        pass

    # default "path" ##########################################################
    @property
    def path(self) -> PathType:
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

    def get_stream_infos(
        self, child_stream: t.Optional[t.BinaryIO] = None
    ) -> t.List[StreamInfo]:
        """
        Get infos about the current and parent streams.
        """
        stream_infos: t.List[StreamInfo] = []

        # If no GUI-Metadata is available, StreamInfos cannot be created
        metadata = self.obj_metadata
        if metadata is None:
            return stream_infos

        stream = metadata["stream"]

        # Add StreamInfos from parent, if a parent exists
        if self.parent is not None:
            stream_infos.extend(self.parent.get_stream_infos(stream))

        # Create new StreamInfo for the stream
        if child_stream != stream:
            bitstream = getattr(stream, "_construct_bitstream_flag", False)

            # Some special handling for RestreamedBytesIO
            if isinstance(stream, cs.RestreamedBytesIO):
                stream = _convert_restreamed(stream)

            if not isinstance(stream, io.BytesIO):
                raise RuntimeError("stream has to be io.BytesIO")

            stream_infos.append(
                StreamInfo(
                    stream=stream,
                    path_str=create_path_str(self.path[:-1]),
                    byte_range=(metadata["byte_range"]),
                    bitstream=bitstream,
                )
            )

        return stream_infos


# EntrySubconstruct ###################################################################################################
class EntrySubconstruct(EntryConstruct):
    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Subconstruct[Any, Any, Any, Any]",
        name: t.Optional[NameType],
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

    # pass throught "obj_view_settings" to subentry ###########################
    @property
    def obj_view_settings(self) -> ObjViewSettings:
        return self.subentry.obj_view_settings

    # pass throught "modify_context_menu" to subentry #########################
    def modify_context_menu(self, menu: ContextMenu):
        return self.subentry.modify_context_menu(menu)


# EntryStruct #########################################################################################################
class EntryStruct(EntryConstruct):
    construct: "cs.Struct[Any, Any]"

    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Struct[Any, Any]",
        name: t.Optional[NameType],
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

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        return ObjViewSettings_Default(self)  # TODO: create panel for cs.Struct

    def modify_context_menu(self, menu: ContextMenu):
        def on_expand_children_clicked():
            menu.parent.expand_children(self)

        def on_collapse_children_clicked():
            menu.parent.collapse_children(self)

        menu.add_menu_item(SeparatorMenuItem())
        menu.add_menu_item(
            ButtonMenuItem(
                "Expand Children",
                None,
                True,
                on_expand_children_clicked,
            )
        )
        menu.add_menu_item(
            ButtonMenuItem(
                "Collapse Children",
                None,
                True,
                on_collapse_children_clicked,
            )
        )


# EntryArray ##########################################################################################################
class EntryArray(EntrySubconstruct):
    construct: t.Union[
        "cs.Array[Any, Any, Any, Any]", "cs.GreedyRange[Any, Any, Any, Any]"
    ]

    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: t.Union[
            "cs.Array[Any, Any, Any, Any]", "cs.GreedyRange[Any, Any, Any, Any]"
        ],
        name: t.Optional[NameType],
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
                    ListIndexName(f"[{index}]"),
                    "",
                )
                self._subentries.append(subentry)

        return self._subentries

    @property
    def typ_str(self) -> str:
        try:
            obj = self.obj
            return f"Array[{len(obj)}]"
        except Exception:
            if isinstance(self.construct, cs.Array):
                return f"Array[{self.construct.count}]"
            else:
                return "GreedyRange"

    @property
    def obj_str(self) -> str:
        return ""

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        return ObjViewSettings_Default(self)  # TODO: create panel for cs.Array

    def modify_context_menu(self, menu: ContextMenu):
        def on_expand_children_clicked():
            menu.parent.expand_children(self)

        def on_collapse_children_clicked():
            menu.parent.collapse_children(self)

        menu.add_menu_item(SeparatorMenuItem())
        menu.add_menu_item(
            ButtonMenuItem(
                "Expand Children",
                None,
                True,
                on_expand_children_clicked,
            )
        )
        menu.add_menu_item(
            ButtonMenuItem(
                "Collapse Children",
                None,
                True,
                on_collapse_children_clicked,
            )
        )

        # If the subentry has no subentries itself, it makes no sense to create a list view.
        temp_subentry = create_entry_from_construct(
            self.model, self, self.construct.subcon, None, ""
        )
        if temp_subentry.subentries is None:
            return

        def on_menu_item_clicked(checked: bool):
            if menu.parent.is_list_view_enabled(self):
                menu.parent.disable_list_view(self)
            else:
                menu.parent.enable_list_view(self)

        menu.add_menu_item(SeparatorMenuItem())
        menu.add_menu_item(
            CheckboxMenuItem(
                "Enable List View",
                None,
                True,
                menu.parent.is_list_view_enabled(self),
                on_menu_item_clicked,
            )
        )


# EntryIfThenElse #####################################################################################################
class EntryIfThenElse(EntryConstruct):
    construct: "cs.IfThenElse[Any, Any]"

    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.IfThenElse[Any, Any]",
        name: t.Optional[NameType],
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
        """Evaluate the conditional function to detect the type of the subentry"""
        obj = self.obj
        if obj is None:
            return None

        metadata = get_gui_metadata(obj)
        if metadata is None:
            return None

        ctx = metadata["context"]
        cond = evaluate(self.construct.condfunc, ctx)
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
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        subentry = self._get_subentry()
        if subentry is None:
            return self._subentries
        else:
            return subentry.subentries

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        subentry = self._get_subentry()
        if subentry is None:
            return ObjViewSettings_Default(self)
        else:
            return subentry.obj_view_settings

    def modify_context_menu(self, menu: ContextMenu):
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
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Switch[Any, Any]",
        name: t.Optional[NameType],
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
        """Evaluate the conditional function to detect the type of the subentry"""
        obj = self.obj
        if obj is None:
            return None

        metadata = get_gui_metadata(obj)
        if metadata is None:
            return None

        ctx = metadata["context"]
        key = evaluate(self.construct.keyfunc, ctx)
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
    def obj_view_settings(self) -> ObjViewSettings:
        subentry = self._get_subentry()
        if subentry is None:
            return ObjViewSettings_Default(self)
        else:
            return subentry.obj_view_settings

    def modify_context_menu(self, menu: ContextMenu):
        subentry = self._get_subentry()
        if subentry is None:
            return
        else:
            return subentry.modify_context_menu(menu)


# EntryFormatField ####################################################################################################
@dataclasses.dataclass
class FormatFieldInt:
    name: str
    bits: int
    signed: bool


@dataclasses.dataclass()
class FormatFieldFloat:
    name: str


class EntryFormatField(EntryConstruct):
    construct: "cs.FormatField[Any, Any]"
    type_mapping: t.Dict[str, t.Union[FormatFieldInt, FormatFieldFloat]] = {
        ">B": FormatFieldInt("Int8ub", 8, False),
        ">H": FormatFieldInt("Int16ub", 16, False),
        ">L": FormatFieldInt("Int32ub", 32, False),
        ">Q": FormatFieldInt("Int64ub", 64, False),
        ">b": FormatFieldInt("Int8sb", 8, True),
        ">h": FormatFieldInt("Int16sb", 16, True),
        ">l": FormatFieldInt("Int32sb", 32, True),
        ">q": FormatFieldInt("Int64sb", 64, True),
        "<B": FormatFieldInt("Int8ul", 8, False),
        "<H": FormatFieldInt("Int16ul", 16, False),
        "<L": FormatFieldInt("Int32ul", 32, False),
        "<Q": FormatFieldInt("Int64ul", 64, False),
        "<b": FormatFieldInt("Int8sl", 8, True),
        "<h": FormatFieldInt("Int16sl", 16, True),
        "<l": FormatFieldInt("Int32sl", 32, True),
        "<q": FormatFieldInt("Int64sl", 64, True),
        "=B": FormatFieldInt("Int8un", 8, False),
        "=H": FormatFieldInt("Int16un", 16, False),
        "=L": FormatFieldInt("Int32un", 32, False),
        "=Q": FormatFieldInt("Int64un", 64, False),
        "=b": FormatFieldInt("Int8sn", 8, True),
        "=h": FormatFieldInt("Int16sn", 16, True),
        "=l": FormatFieldInt("Int32sn", 32, True),
        "=q": FormatFieldInt("Int64sn", 64, True),
        ">e": FormatFieldFloat("Float16b"),
        "<e": FormatFieldFloat("Float16l"),
        "=e": FormatFieldFloat("Float16n"),
        ">f": FormatFieldFloat("Float32b"),
        "<f": FormatFieldFloat("Float32l"),
        "=f": FormatFieldFloat("Float32n"),
        ">d": FormatFieldFloat("Float64b"),
        "<d": FormatFieldFloat("Float64l"),
        "=d": FormatFieldFloat("Float64n"),
    }

    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.FormatField[Any, Any]",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

        # change default row infos
        self.type_infos = None
        if construct.fmtstr in self.type_mapping:
            self.type_infos = self.type_mapping[construct.fmtstr]

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        if isinstance(self.type_infos, FormatFieldInt):
            return ObjViewSettings_Integer(self)
        elif isinstance(self.type_infos, FormatFieldFloat):
            return ObjViewSettings_Default(self)  # TODO: ObjEditor_Float
        else:
            return ObjViewSettings_Default(self)

    @property
    def obj_str(self) -> str:
        obj = self.obj
        if isinstance(self.type_infos, FormatFieldInt) and (obj is not None):
            return int_to_str(self.model.integer_format, obj)
        elif isinstance(self.type_infos, FormatFieldFloat) and (obj is not None):
            return str(obj)  # TODO: float_to_str
        else:
            return str(obj)

    @property
    def typ_str(self) -> str:
        if self.type_infos is not None:
            return self.type_infos.name
        else:
            return "FormatField[{}]".format(repr(self.construct.fmtstr))


# EntryBytesInteger ###################################################################################################
class EntryBytesInteger(EntryConstruct):
    construct: "cs.BytesInteger[Any, Any]"

    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.BytesInteger[Any, Any]",
        name: t.Optional[NameType],
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

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        if isinstance(self.construct.length, int):
            return ObjViewSettings_Integer(self)
        else:
            return ObjViewSettings_Default(self)


# EntryBitsInteger ####################################################################################################
class EntryBitsInteger(EntryConstruct):
    construct: "cs.BitsInteger[Any, Any]"

    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.BitsInteger[Any, Any]",
        name: t.Optional[NameType],
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

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        if isinstance(self.construct.length, int):
            return ObjViewSettings_Integer(self)
        else:
            return ObjViewSettings_Default(self)


# EntryComputed #######################################################################################################
class EntryStringEncoded(EntrySubconstruct):
    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.StringEncoded[Any, Any]",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)  # type: ignore

    @property
    def typ_str(self) -> str:
        return f"StringEncoded[{self.subentry.typ_str}]"

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        return ObjViewSettings_String(self)


# EntryBytes ##########################################################################################################
class EntryBytes(EntryConstruct):
    construct: t.Union["cs.Bytes[Any, Any]", "cs.Construct[bytes, bytes]"]

    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: t.Union["cs.Bytes[Any, Any]", "cs.Construct[bytes, bytes]"],
        name: t.Optional[NameType],
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
        try:
            obj = self.obj
            return f"Byte[{len(obj)}]"
        except Exception:
            if isinstance(self.construct, cs.Bytes):
                return f"Byte[{self.construct.length}]"
            else:
                return "GreedyBytes"

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        return ObjViewSettings_Bytes(self)

    def modify_context_menu(self, menu: ContextMenu):
        def on_ascii_view_clicked(checked: bool):
            self.ascii_view = not self.ascii_view
            menu.parent.reload()

        menu.add_menu_item(SeparatorMenuItem())
        menu.add_menu_item(
            CheckboxMenuItem(
                "ASCII View",
                None,
                True,
                self.ascii_view,
                on_ascii_view_clicked,
            )
        )


# EntryTell ###########################################################################################################
class EntryTell(EntryConstruct):
    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Construct[Any, Any]",
        name: t.Optional[NameType],
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
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Seek",
        name: t.Optional[NameType],
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
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Construct[None, None]",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        return "Pass"

    @property
    def obj_str(self) -> str:
        return ""


# EntryConst #######################################################################################################
class EntryConst(EntrySubconstruct):
    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Const[Any, Any, Any, Any]",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        return ObjViewSettings_Default(self)


# EntryComputed #######################################################################################################
class EntryComputed(EntryConstruct):
    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Computed[Any, Any]",
        name: t.Optional[NameType],
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


# EntryDefault ########################################################################################################
class EntryDefault(EntrySubconstruct):
    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Subconstruct[Any, Any, Any, Any]",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    def modify_context_menu(self, menu: ContextMenu):
        def on_default_clicked():
            # TODO: This is not working correctly...
            self.obj = None
            menu.parent.reload()

        menu.add_menu_item(SeparatorMenuItem())
        menu.add_menu_item(
            ButtonMenuItem(
                "Set to default",
                None,
                True,
                on_default_clicked,
            )
        )


# EntryFocusedSeq ###################################################################################################
class EntryFocusedSeq(EntryConstruct):
    construct: "cs.FocusedSeq"

    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.FocusedSeq",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

        # change default row infos
        self._subentries: t.Dict[str, EntryConstruct] = {}

        # create sub entries
        for subcon in self.construct.subcons:
            if subcon.name is None:
                continue

            name = subcon.name

            # remove name of subcon
            if isinstance(subcon, cs.Renamed):
                subcon = subcon.subcon

            subentry = create_entry_from_construct(
                model,
                self,
                subcon,
                NameExcludedFromPath(name),
                "",
            )
            self._subentries[name] = subentry

    def _get_subentry(self) -> "Optional[EntryConstruct]":
        """Evaluate the conditional function to detect the type of the subentry"""
        obj = self.obj
        if obj is None:
            return None

        metadata = get_gui_metadata(obj)
        if metadata is None:
            return None

        ctx = metadata["context"]
        parsebuildfrom = evaluate(self.construct.parsebuildfrom, ctx)
        subentry = self._subentries[parsebuildfrom]
        return subentry

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
            return "FocusedSeq"
        else:
            return subentry.typ_str

    @property
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        subentry = self._get_subentry()
        if subentry is None:
            return list(self._subentries.values())
        else:
            return subentry.subentries

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        subentry = self._get_subentry()
        if subentry is None:
            return ObjViewSettings_Default(self)
        else:
            return subentry.obj_view_settings

    def modify_context_menu(self, menu: ContextMenu):
        subentry = self._get_subentry()
        if subentry is None:
            return
        else:
            return subentry.modify_context_menu(menu)


# EntrySelect ###################################################################################################
class EntrySelect(EntryConstruct):
    construct: "cs.Select"

    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Select",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

        # change default row infos
        self._subentries: t.Dict[int, EntryConstruct] = {}

        # create sub entries
        for idx, subcon in enumerate(self.construct.subcons):
            subentry = create_entry_from_construct(
                model,
                self,
                subcon,
                NameExcludedFromPath(f"Option {idx}"),
                "",
            )
            self._subentries[id(subentry.construct)] = subentry

    def _get_subentry(self) -> "Optional[EntryConstruct]":
        """Evaluate the conditional function to detect the type of the subentry"""
        obj = self.obj
        if obj is None:
            return None

        metadata = get_gui_metadata(obj)
        if metadata is None:
            return None

        # we are not interested in the metadata of the
        # cs.Select, but of its childs
        metadata = metadata["child_gui_metadata"]
        if metadata is None:
            return None
        if id(metadata["construct"]) not in self._subentries:
            print("error")
        subentry = self._subentries[id(metadata["construct"])]
        return subentry

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
            return "Select"
        else:
            return subentry.typ_str

    @property
    def subentries(self) -> Optional[List["EntryConstruct"]]:
        subentry = self._get_subentry()
        if subentry is None:
            return list(self._subentries.values())
        else:
            return subentry.subentries

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        subentry = self._get_subentry()
        if subentry is None:
            return ObjViewSettings_Default(self)
        else:
            return subentry.obj_view_settings

    def modify_context_menu(self, menu: ContextMenu):
        subentry = self._get_subentry()
        if subentry is None:
            return
        else:
            return subentry.modify_context_menu(menu)


# EntryTimestamp ######################################################################################################
class EntryTimestamp(EntrySubconstruct):
    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.TimestampAdapter[Any, Any]",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def obj_str(self) -> str:
        return str(self.obj)

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        return ObjViewSettings_Timestamp(self)


# EntryTransparentSubcon ##############################################################################################
class EntryTransparentSubcon(EntrySubconstruct):
    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Subconstruct[Any, Any, Any, Any]",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)


# EntryNullStripped ###################################################################################################
class EntryNullStripped(EntrySubconstruct):
    construct: "cs.NullStripped[Any, Any]"

    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.NullStripped[Any, Any]",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        return f"NullStripped[{self.subentry.typ_str}, Pad={self.construct.pad}]"


# EntryNullTerminated #################################################################################################
class EntryNullTerminated(EntrySubconstruct):
    construct: "cs.NullTerminated[Any, Any]"

    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.NullTerminated[Any, Any]",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        return f"NullTerminated[{self.subentry.typ_str}, Term={self.construct.term}]"


# EntryChecksumSubcon #################################################################################################
class EntryChecksumSubcon(EntrySubconstruct):
    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Checksum[Any, Any, Any]",
        name: t.Optional[NameType],
        docs: str,
    ):
        # Don't access EntrySubconstruct's __init__() via super(), because "subcon" is no member of "cs.Checksum"
        # So we call directly the parents parent __init__() method
        EntryConstruct.__init__(self, model, parent, construct, name, docs)

        self.subentry = create_entry_from_construct(
            model, self, construct.checksumfield, None, ""
        )


# EntryCompressed #####################################################################################################
class EntryCompressed(EntrySubconstruct):
    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Compressed[Any, Any]",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        return f"Compressed[{self.subentry.typ_str}]"


# EntryPeek ###########################################################################################################
class EntryPeek(EntrySubconstruct):
    construct: "cs.Peek"

    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Peek",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)


# EntryRawCopy #######################################################################################################
class EntryRawCopy(EntrySubconstruct):
    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.RawCopy[Any, Any, Any, Any]",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

        # change default row infos


# EntryDataclassStruct ################################################################################################
class EntryDataclassStruct(EntrySubconstruct):
    construct: "cst.DataclassStruct[Any]"

    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cst.DataclassStruct[Any]",
        name: t.Optional[NameType],
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
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.FormatField[Any, Any]",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        return ObjViewSettings_Flag(self)

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
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.Enum",
        name: t.Optional[NameType],
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

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        return ObjViewSettings_Enum(self)

    def get_enum_items(self) -> t.List[EnumItem]:
        """Get items to show in the ComboBox"""
        items: t.List[EnumItem] = []
        enums = self.construct.encmapping
        for name, value in enums.items():
            items.append(EnumItem(name=name, value=value))
        return items

    def get_enum_item_from_obj(self) -> EnumItem:
        """Get items to select in the ComboBox"""
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
        """Convert string (enum name or integer value) to object"""
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
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cs.FlagsEnum",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        return super().typ_str + " as Flags"

    @property
    def obj_str(self) -> str:
        return self.conv_obj_to_str(self.obj)

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        return ObjViewSettings_FlagsEnum(self)

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
        """Get items to show in the ComboBox"""
        items: t.List[FlagsEnumItem] = []
        flags = self.construct.flags
        obj = self.obj
        for flag in flags.keys():
            items.append(
                FlagsEnumItem(name=str(flag), value=flags[flag], checked=obj[flag])
            )
        return items

    def conv_flagsenum_items_to_obj(self, items: t.List[FlagsEnumItem]) -> Any:
        """Convert flagsenum items to object"""
        new_obj = cs.Container()
        for item in items:
            if item.checked:
                new_obj[item.name] = True
            else:
                new_obj[item.name] = False
        return new_obj


# EntryTEnum ##########################################################################################################
def get_enum_name(e: cst.EnumBase):
    return f"{e.__class__.__name__}.{e.name}"


class EntryTEnum(EntrySubconstruct):
    construct: "cst.TEnum[Any]"

    def __init__(
        self,
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cst.TEnum[Any]",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        return super().typ_str + " as Enum"

    @property
    def obj_str(self) -> str:
        try:
            obj: cst.EnumBase = self.obj
            return f"{int_to_str(self.model.integer_format, int(obj.value))} ({get_enum_name(obj)})"
        except Exception:
            return str(self.obj)

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        return ObjViewSettings_Enum(self)

    def get_enum_items(self) -> t.List[EnumItem]:
        """Get items to show in the ComboBox"""
        items: t.List[EnumItem] = []
        enum_type: t.Type[cst.EnumBase] = self.construct.enum_type
        for e in enum_type:
            items.append(
                EnumItem(name=get_enum_name(e), value=e.value)
            )
        return items

    def get_enum_item_from_obj(self) -> EnumItem:
        """Get items to select in the ComboBox"""
        obj: cst.EnumBase = self.obj
        return EnumItem(name=get_enum_name(obj), value=obj.value)

    def conv_str_to_obj(self, s: str) -> Any:
        """Convert string (enum name or integer value) to object"""
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
        model: "model.ConstructEditorModel",
        parent: Optional["EntryConstruct"],
        construct: "cst.TFlagsEnum[Any]",
        name: t.Optional[NameType],
        docs: str,
    ):
        super().__init__(model, parent, construct, name, docs)

    @property
    def typ_str(self) -> str:
        return super().typ_str + " as Flags"

    @property
    def obj_str(self) -> str:
        return self.conv_obj_to_str(self.obj)

    @property
    def obj_view_settings(self) -> ObjViewSettings:
        return ObjViewSettings_FlagsEnum(self)

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
        """Get items to show in the ComboBox"""
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
        """Convert flagsenum items to object"""
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
    cs.StringEncoded: EntryStringEncoded,
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
    cs.Const: EntryConst,
    cs.Computed: EntryComputed,
    # cs.Index
    # cs.Rebuild
    cs.Default: EntryDefault,
    # cs.Check
    # cs.Error
    cs.FocusedSeq: EntryFocusedSeq,
    # cs.Pickled
    # cs.Numpy
    # cs.NamedTuple
    cs.TimestampAdapter: EntryTimestamp,
    # cs.Hex
    # cs.HexDump
    #
    # conditional ###############################
    # cs.Union
    cs.Select: EntrySelect,
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
    cs.Prefixed: EntryTransparentSubcon,
    cs.FixedSized: EntryTransparentSubcon,
    cs.NullTerminated: EntryNullTerminated,
    cs.NullStripped: EntryNullStripped,
    # cs.RestreamData
    cs.Transformed: EntryTransparentSubcon,
    cs.Restreamed: EntryTransparentSubcon,
    # cs.ProcessXor
    # cs.ProcessRotateLeft
    cs.Checksum: EntryChecksumSubcon,
    cs.Compressed: EntryCompressed,
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
    model: "model.ConstructEditorModel",
    parent: Optional["EntryConstruct"],
    subcon: "cs.Construct[Any, Any]",
    name: t.Optional[NameType],
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
