import io
import construct as cs
import construct_typed as cst
import typing as t
import copy


class GuiMetaData(t.TypedDict):
    byte_range: t.Tuple[int, int]
    construct: cs.Construct
    context: "cs.Context"
    stream: io.BytesIO
    child_gui_metadata: t.Optional["GuiMetaData"]


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

    def __init__(self, subcon, bitwise: bool):
        super().__init__(subcon)  # type: ignore
        self.bitwise = bitwise

    def _parse(self, stream, context, path):
        offset_start = cs.stream_tell(stream, path)
        obj = self.subcon._parsereport(stream, context, path)  # type: ignore
        offset_end = cs.stream_tell(stream, path)

        # Maybe the obj has already gui_metadata. Read it
        # out and save it in the parent gui_metadata object.
        child_gui_metadata = get_gui_metadata(obj)

        if self.bitwise is True:
            stream._construct_bitstream_flag = True

        gui_metadata = GuiMetaData(
            byte_range=(offset_start, offset_end),
            construct=self.subcon,
            context=context,
            stream=stream,
            child_gui_metadata=child_gui_metadata,
        )

        return add_gui_metadata(obj, gui_metadata)

    def _build(self, obj, stream, context, path):
        buildret = self.subcon._build(obj, stream, context, path)  # type: ignore
        return obj


# #############################################################################
def include_metadata(
    constr: "cs.Construct[t.Any, t.Any]", bitwise: bool = False
) -> "cs.Construct[t.Any, t.Any]":
    """
    Surrond all named entries of a construct with offsets, so that
    we know the offset in the byte-stream and the length
    """

    # ########## Simple Constructs ############################################
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
        return IncludeGuiMetaData(constr, bitwise)

    # ########## Bitwiese Construct ###########################################
    elif (
        isinstance(constr, (cs.Restreamed))
        and (constr.decoder is cs.bytes2bits)
        and (constr.encoder is cs.bits2bytes)
    ) or (
        isinstance(constr, (cs.Transformed))
        and (constr.decodefunc is cs.bytes2bits)
        and (constr.encodefunc is cs.bits2bytes)
    ):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        constr.subcon = include_metadata(constr.subcon, bitwise=True)
        return IncludeGuiMetaData(constr, bitwise)

    # ########## Subconstructs ################################################
    elif isinstance(
        constr,
        (
            cs.Const,
            cs.Rebuild,
            cs.Default,
            cs.Padded,
            cs.Aligned,
            cs.Pointer,
            cs.Peek,
            cst.DataclassStruct,
            cs.Array,
            cs.GreedyRange,
            cs.Restreamed,
            cs.Transformed,
            cs.Tunnel,
            cs.Prefixed,
            cs.FixedSized,
            cs.NullStripped,
            cs.NullTerminated,
        ),
    ):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        constr.subcon = include_metadata(constr.subcon, bitwise)  # type: ignore
        return IncludeGuiMetaData(constr, bitwise)

    # Struct ##################################################################
    elif isinstance(constr, cs.Struct):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        new_subcons = []
        for subcon in constr.subcons:
            new_subcons.append(include_metadata(subcon, bitwise))
        constr.subcons = new_subcons
        return IncludeGuiMetaData(constr, bitwise)

    # FocusedSeq ##############################################################
    elif isinstance(constr, cs.FocusedSeq):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        new_subcons = []
        for subcon in constr.subcons:
            new_subcons.append(include_metadata(subcon, bitwise))
        constr.subcons = new_subcons
        return IncludeGuiMetaData(constr, bitwise)

    # Select ##################################################################
    elif isinstance(constr, cs.Select):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        new_subcons = []
        for subcon in constr.subcons:
            new_subcons.append(include_metadata(subcon, bitwise))
        constr.subcons = new_subcons
        return IncludeGuiMetaData(constr, bitwise)

    # IfThenElse ##############################################################
    elif isinstance(constr, cs.IfThenElse):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        constr.thensubcon = include_metadata(constr.thensubcon, bitwise)
        constr.elsesubcon = include_metadata(constr.elsesubcon, bitwise)
        return IncludeGuiMetaData(constr, bitwise)

    # Switch ##################################################################
    elif isinstance(constr, cs.Switch):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        new_cases = {}
        for key, subcon in constr.cases.items():
            new_cases[key] = include_metadata(subcon, bitwise)
        constr.cases = new_cases
        if constr.default is not None:
            constr.default = include_metadata(constr.default, bitwise)
        return IncludeGuiMetaData(constr, bitwise)

    # Checksum #################################################################
    elif isinstance(constr, cs.Checksum):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        constr.checksumfield = include_metadata(constr.checksumfield, bitwise)
        return IncludeGuiMetaData(constr, bitwise)

    # Renamed #################################################################
    elif isinstance(constr, cs.Renamed):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        constr.subcon = include_metadata(constr.subcon, bitwise)  # type: ignore
        return constr

    # Misc ####################################################################
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
        ),
    ):
        return IncludeGuiMetaData(constr, bitwise)

    # TODO:
    # # Grouping:
    # - Sequence
    # - Union
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
