import construct as cs
import construct_typed as cst
import typing as t
import copy


class GuiMetaData(t.TypedDict):
    byte_range: t.Optional[t.Tuple[int, int]]
    construct: cs.Construct
    context: "cs.Context"


class IntWithGuiMetadata(int):
    pass


class FloatWithGuiMetadata(float):
    pass


class BytesWithGuiMetadata(bytes):
    pass


class BytearrayWithGuiMetadata(bytearray):
    pass


class StrWithGuiMetadata(str):
    pass


class NoneWithGuiMetadata:
    pass


def get_gui_metadata(obj: t.Any) -> t.Optional[GuiMetaData]:
    """Get the GUI metadata if they are available"""
    try:
        return obj.__gui_metadata  # type: ignore
    except Exception:
        return None


def add_gui_metadata(obj: t.Any, gui_metadata: GuiMetaData) -> t.Any:
    """Append the private field "__gui_metadata" to an object"""
    obj_type = type(obj)
    if (obj_type is int) or (obj_type is bool):
        obj = IntWithGuiMetadata(obj)
        obj.__gui_metadata = gui_metadata
    elif obj_type is float:
        obj = FloatWithGuiMetadata(obj)
        obj.__gui_metadata = gui_metadata
    elif obj_type is bytes:
        obj = BytesWithGuiMetadata(obj)
        obj.__gui_metadata = gui_metadata
    elif obj_type is bytearray:
        obj = BytearrayWithGuiMetadata(obj)
        obj.__gui_metadata = gui_metadata
    elif obj_type is str:
        obj = StrWithGuiMetadata(obj)
        obj.__gui_metadata = gui_metadata
    elif obj is None:
        obj = NoneWithGuiMetadata()
        obj.__gui_metadata = gui_metadata
    else:
        try:
            obj.__gui_metadata = gui_metadata  # type: ignore
        except AttributeError:
            raise ValueError(f"add_gui_metadata dont work with type of {type(obj)}")
    return obj


class IncludeGuiMetaData(cs.Subconstruct):
    """Include GUI metadata to the parsed object"""

    def __init__(self, subcon, stream_nesting: int):
        super().__init__(subcon)  # type: ignore
        self.stream_nesting = stream_nesting

    def _parse(self, stream, context, path):
        offset_start = cs.stream_tell(stream, path)
        obj = self.subcon._parsereport(stream, context, path)  # type: ignore
        offset_end = cs.stream_tell(stream, path)

        gui_metadata = GuiMetaData(
            byte_range=(offset_start, offset_end) if self.stream_nesting == 0 else None,
            construct=self.subcon,
            context=context,
        )

        return add_gui_metadata(obj, gui_metadata)

    def _build(self, obj, stream, context, path):
        buildret = self.subcon._build(obj, stream, context, path)  # type: ignore
        return obj


def include_metadata(
    constr: "cs.Construct[t.Any, t.Any]", stream_nesting: int = 0
) -> "cs.Construct[t.Any, t.Any]":
    """
    Surrond all named entries of a construct with offsets, so that
    we know the offset in the byte-stream and the length
    """
    if isinstance(
        constr,
        (
            cs.BytesInteger,
            cs.BitsInteger,
            cs.Bytes,
            cs.FormatField,
            cs.BytesInteger,
            cs.BitsInteger,
            cs.Computed,
            cs.Check,
            cs.StopIf,
            cst.TEnum,
            cs.Enum,
            cs.FlagsEnum,
            cs.TimestampAdapter,
            cs.Seek,
        ),
    ):
        return IncludeGuiMetaData(constr, stream_nesting)

    elif isinstance(
        constr,
        (
            cs.Restreamed,
            cs.Transformed,
            cs.Tunnel,
            cs.Prefixed,
            cs.FixedSized,
            cs.NullStripped,
        ),
    ):
        # these constructs manipulate the stream, so the offsets of all nested subcons are wrong.
        # to detect this a counter is incremented for every nested stream
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        constr.subcon = include_metadata(constr.subcon, stream_nesting + 1)  # type: ignore
        return IncludeGuiMetaData(constr, stream_nesting)

    elif isinstance(constr, (cs.Struct)):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        new_subcons = []
        for subcon in constr.subcons:
            new_subcons.append(include_metadata(subcon, stream_nesting))
        constr.subcons = new_subcons
        return IncludeGuiMetaData(constr, stream_nesting)

    elif isinstance(constr, (cs.Array, cs.GreedyRange)):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        constr.subcon = include_metadata(constr.subcon, stream_nesting)
        return IncludeGuiMetaData(constr, stream_nesting)

    elif isinstance(constr, cs.IfThenElse):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        constr.thensubcon = include_metadata(constr.thensubcon, stream_nesting)
        constr.elsesubcon = include_metadata(constr.elsesubcon, stream_nesting)
        return IncludeGuiMetaData(constr, stream_nesting)

    elif isinstance(constr, cs.Switch):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        new_cases = {}
        for key, subcon in constr.cases.items():
            new_cases[key] = include_metadata(subcon, stream_nesting)
        constr.cases = new_cases
        if constr.default is not None:
            constr.default = include_metadata(constr.default, stream_nesting)
        return IncludeGuiMetaData(constr, stream_nesting)

    elif isinstance(
        constr,
        (
            cs.Renamed,
            cs.Const,
            cs.Rebuild,
            cs.Default,
            cs.Padded,
            cs.Aligned,
            cs.Pointer,
            cs.Peek,
        ),
    ):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        constr.subcon = include_metadata(constr.subcon, stream_nesting)  # type: ignore
        return constr

    elif isinstance(constr, cst.DataclassStruct):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        constr.subcon = include_metadata(constr.subcon, stream_nesting)  # type: ignore
        return IncludeGuiMetaData(constr, stream_nesting)

    elif isinstance(
        constr,
        (
            cs.ExprAdapter,
            cs.Adapter,
            type(cs.GreedyBytes),
            type(cs.VarInt),
            type(cs.ZigZag),
            type(cs.Flag),
            type(cs.Index),
            type(cs.Error),
            type(cs.Pickled),
            type(cs.Numpy),
            type(cs.Tell),
            type(cs.Pass),
            type(cs.Terminated),
        ),  # type: ignore
    ):
        return IncludeGuiMetaData(constr, stream_nesting)

    # TODO:
    # # Grouping:
    # - Sequence
    # - FocusedSeq
    # - Union
    # - Select
    # - LazyStruct

    # # Grouping lists:
    # - Array
    # - GreedyRange
    # - RepeatUntil

    # # Special:
    # - Pointer
    # - RawCopy
    # - Restreamed
    # - Transformed
    # - RestreamData
    raise ValueError(f"construct of type '{constr}' is not supported")
