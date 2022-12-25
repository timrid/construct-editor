import enum
import typing as t

import construct as cs

import construct_editor.core.entries as entries
import construct_editor.core.model as model
import construct_editor.core.preprocessor as preprocessor


def add_custom_transparent_subconstruct(
    subconstruct: t.Type["cs.Subconstruct[t.Any,t.Any,t.Any, t.Any]"],
):
    """
    Add compatibility of an custom `cs.Subconstruct` to the construct-editor.
    """
    preprocessor.custom_subconstructs.append(subconstruct)
    entries.construct_entry_mapping[subconstruct] = entries.EntryTransparentSubcon


def add_custom_tunnel(
    tunnel: t.Type["cs.Tunnel[t.Any, t.Any]"],
    type_str: str,
):
    """
    Add compatibility of an custom `cs.Tunnel` to the construct-editor.
    """

    class EntryTunnel(entries.EntrySubconstruct):
        def __init__(
            self,
            model: "model.ConstructEditorModel",
            parent: t.Optional["entries.EntryConstruct"],
            construct: "cs.Compressed[t.Any, t.Any]",
            name: entries.NameType,
            docs: str,
        ):
            super().__init__(model, parent, construct, name, docs)

        @property
        def typ_str(self) -> str:
            return f"{type_str}[{self.subentry.typ_str}]"

    entries.construct_entry_mapping[tunnel] = EntryTunnel


class AdapterObjEditorType(enum.Enum):
    Default = enum.auto()
    Integer = enum.auto()
    String = enum.auto()


def add_custom_adapter(
    adapter: t.Union[
        t.Type["cs.Adapter[t.Any,t.Any,t.Any, t.Any]"],  # for cs.Adapter
        "cs.Adapter[t.Any,t.Any,t.Any, t.Any]",  # for cs.ExprAdapter
    ],
    type_str: str,
    obj_editor_type: AdapterObjEditorType,
):
    """
    Add compatibility of an custom `cs.Adapter` or `cs.ExprAdapter` to the construct-editor.
    """

    class EntryAdapter(entries.EntryConstruct):
        def __init__(
            self,
            model: "model.ConstructEditorModel",
            parent: t.Optional["entries.EntryConstruct"],
            construct: "cs.Subconstruct[t.Any, t.Any, t.Any, t.Any]",
            name: entries.NameType,
            docs: str,
        ):
            super().__init__(model, parent, construct, name, docs)

        @property
        def typ_str(self) -> str:
            return type_str

        @property
        def obj_str(self) -> t.Any:
            return str(self.obj)

        @property
        def obj_view_settings(self) -> entries.ObjViewSettings:
            if obj_editor_type == AdapterObjEditorType.Integer:
                return entries.ObjViewSettings_Integer(self)
            elif obj_editor_type == AdapterObjEditorType.String:
                return entries.ObjViewSettings_String(self)
            else:
                return entries.ObjViewSettings_Default(self)

    entries.construct_entry_mapping[adapter] = EntryAdapter
