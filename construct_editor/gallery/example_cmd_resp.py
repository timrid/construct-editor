import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem
import copy


class DefaultSizedError(cs.ConstructError):
    pass


class DefaultSized(cs.Subconstruct):
    r"""
    Returns a size when calling sizeof of GreedyBytes. Parsing and building is not changed.

    :param subcon: Construct instance
    :param default_size: size that should be returned

    :raises DefaultSizedError: anouter GreedyBytes than GreedyBytes is passed

    Example::

        >>> d = DefaultSized(GreedyBytes)
        >>> d.sizeof()
        0
    """

    def __init__(self, subcon, default_size=0):
        if subcon is not cs.GreedyBytes:
            raise DefaultSizedError("DefaultSized only works with cs.GreedyBytes")
        super().__init__(subcon)  # type: ignore
        self.default_size = default_size

    def _sizeof(self, context, path):
        return 0


class CmdCode(cst.EnumBase):
    Command1 = 0
    Command2 = 1


@dataclasses.dataclass
class RespData_Command1(cst.DataclassMixin):
    d1: int = cst.csfield(cs.Int8ul)
    d2: int = cst.csfield(cs.Int8ul)


@dataclasses.dataclass
class RespData_Command2(cst.DataclassMixin):
    c1: int = cst.csfield(cs.Int16ul)
    c2: int = cst.csfield(cs.Int16ul)


@dataclasses.dataclass
class RespData_Error(cst.DataclassMixin):
    e1: int = cst.csfield(cs.Int32ul)
    e2: int = cst.csfield(cs.Int32ul)


resp_data_formats: t.Dict[CmdCode, cst.Construct[t.Any, t.Any]] = {
    CmdCode.Command1: cst.DataclassStruct(RespData_Command1),
    CmdCode.Command2: cst.DataclassStruct(RespData_Command2),
}

RespDataType = t.Union[
    bytes,
    RespData_Command1,
    RespData_Command2,
]


class StatusCode(cst.EnumBase):
    OK = 0
    Error1 = 1
    Error2 = 2


status_code_format = cst.TEnum(cs.Int32ul, StatusCode)


def _get_cmd_code(ctx: cst.Context):
    contextkw = ctx._root._
    if "cmd_code" not in contextkw:
        # if no cmd_code is passed, fallback to GreedyBytes
        return None

    return contextkw.cmd_code


def _is_status_code_ok(ctx: cst.Context):
    if ctx._sizing is True:
        # while sizing pretend an ok status_code
        return True

    return ctx.status_code == StatusCode.OK


@dataclasses.dataclass
class Response(cst.DataclassMixin):
    status_code: StatusCode = cst.csfield(status_code_format)
    data: RespDataType = cst.csfield(
        cs.Select(
            cs.IfThenElse(
                condfunc=_is_status_code_ok,
                thensubcon=cs.Switch(
                    keyfunc=_get_cmd_code,  # select the response format based on the cmd_code
                    cases=resp_data_formats,
                    default=cs.StopIf(True),
                ),
                elsesubcon=cst.DataclassStruct(RespData_Error),
            ),
            DefaultSized(cs.GreedyBytes),
        )
    )


constr = cst.DataclassStruct(Response)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Zeros": bytes(20),
        "1": bytes([1, 1, 2, 1, 2]),
    },
    contextkw={"cmd_code": CmdCode.Command1},
)

# ######################################################################################
# ################## Adding new constructs to construct-editor #########################
# ######################################################################################
import construct_editor.helper.preprocessor as cse_preprocessor  # type: ignore
import construct_editor.helper.wrapper as cse_wrapper  # type: ignore

cse_wrapper.construct_entry_mapping.update(
    {
        DefaultSized: cse_wrapper.EntryTransparentSubcon,
    }
)

_original_include_metadata = cse_preprocessor.include_metadata


def include_metadata(
    constr: "cs.Construct[t.Any, t.Any]", bitwise: bool = False
) -> "cs.Construct[t.Any, t.Any]":
    if isinstance(constr, DefaultSized):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        constr.subcon = cse_preprocessor.include_metadata(constr.subcon, bitwise)
        return cse_preprocessor.IncludeGuiMetaData(constr, bitwise)
    else:
        return _original_include_metadata(constr, bitwise)


# monkey patch construct-editor
cse_preprocessor.include_metadata = include_metadata
