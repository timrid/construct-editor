import construct as cs
import construct_typed as cst
import typing as t
import copy
import dataclasses


@dataclasses.dataclass
class GuiMetadata:
    byte_range: t.Tuple[int, int]
    construct: cs.Construct
    context: "cs.Context"


class StructWithGuiMetadata(cs.Struct):
    def _parse(self, stream, context, path):
        obj = cs.Container()
        obj._io = stream  # type: ignore
        obj._gui_metadata = {}  # type: ignore
        context = cs.Container(
            _=context,
            _params=context._params,
            _root=None,
            _parsing=context._parsing,
            _building=context._building,
            _sizing=context._sizing,
            _subcons=self._subcons,
            _io=stream,
            _index=context.get("_index", None),
        )
        context._root = context._.get("_root", context)  # type: ignore
        for sc in self.subcons:
            try:
                start = cs.stream_tell(stream, path)
                subobj = sc._parsereport(stream, context, path)  # type: ignore
                end = cs.stream_tell(stream, path)
                if sc.name:
                    obj[sc.name] = subobj
                    obj._gui_metadata[sc.name] = GuiMetadata((start, end), sc, context)  # type: ignore
                    context[sc.name] = subobj
            except cs.StopFieldError:
                break
        return obj


class DataclassStructWithGuiMetadata(cst.DataclassStruct):
    def __init__(
        self,
        dc_type: t.Type,
        reverse: bool = False,
    ) -> None:
        if not issubclass(dc_type, cst.DataclassMixin):
            raise TypeError(f"'{repr(dc_type)}' has to be a '{repr(cst.DataclassMixin)}'")
        if not dataclasses.is_dataclass(dc_type):
            raise TypeError(f"'{repr(dc_type)}' has to be a 'dataclasses.dataclass'")
        self.dc_type = dc_type
        self.reverse = reverse

        # get all fields from the dataclass
        fields = dataclasses.fields(self.dc_type)
        if self.reverse:
            fields = tuple(reversed(fields))

        # extract the construct formats from the struct_type
        subcon_fields = {}
        for field in fields:
            subcon_fields[field.name] = field.metadata["subcon"]

        # init adatper
        cs.Subconstruct.__init__(self, StructWithGuiMetadata(**subcon_fields))  # type: ignore

    def _decode(self, obj, context, path):
        # get all fields from the dataclass
        fields = dataclasses.fields(self.dc_type)

        # extract all fields from the container, that are used for create the dataclass object
        dc_init = {}
        for field in fields:
            if field.init:
                value = obj[field.name]
                dc_init[field.name] = value

        # create object of dataclass
        dc = self.dc_type(**dc_init)  # type: ignore

        # extract all other values from the container, an pass it to the dataclass
        for field in fields:
            if not field.init:
                value = obj[field.name]
                setattr(dc, field.name, value)

        # copy gui_metadata
        dc._gui_metadata = obj._gui_metadata

        return dc


class SequenceWithGuiMetadata(cs.Sequence):
    def _parse(self, stream, context, path):
        obj = cs.ListContainer()
        obj._gui_metadata = []  # type: ignore
        context = cs.Container(
            _=context,
            _params=context._params,
            _root=None,
            _parsing=context._parsing,
            _building=context._building,
            _sizing=context._sizing,
            _subcons=self._subcons,
            _io=stream,
            _index=context.get("_index", None),
        )
        context._root = context._.get("_root", context)  # type: ignore
        for sc in self.subcons:
            try:
                start = cs.stream_tell(stream, path)
                subobj = sc._parsereport(stream, context, path)  # type: ignore
                end = cs.stream_tell(stream, path)
                obj.append(subobj)
                obj._gui_metadata.append(GuiMetadata((start, end), sc, context))  # type: ignore
                if sc.name:
                    context[sc.name] = subobj
            except cs.StopFieldError:
                break
        return obj


class ArrayWithGuiMetadata(cs.Array):
    def _parse(self, stream, context, path):
        count = cs.evaluate(self.count, context)  # type: ignore
        if not 0 <= count:
            raise cs.RangeError("invalid count %s" % (count,), path=path)
        discard = self.discard
        obj = cs.ListContainer()
        obj._gui_metadata = []  # type: ignore
        for i in range(count):
            context._index = i
            start = cs.stream_tell(stream, path)
            e = self.subcon._parsereport(stream, context, path)  # type: ignore
            end = cs.stream_tell(stream, path)
            if not discard:
                obj.append(e)
                obj._gui_metadata.append(GuiMetadata((start, end), self.subcon, context))  # type: ignore
        return obj


# #############################################################################
def include_metadata(
    constr: "cs.Construct[t.Any, t.Any]",
) -> "cs.Construct[t.Any, t.Any]":
    """
    Surrond all named entries of a construct with offsets, so that
    we know the offset in the byte-stream and the length
    """

    ########## Simple Constructs ############################################
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
        return constr

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
            cs.GreedyRange,
            cs.Restreamed,
            cs.Transformed,
            cs.Tunnel,
            cs.Prefixed,
            cs.FixedSized,
            cs.NullStripped,
        ),
    ):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        constr.subcon = include_metadata(constr.subcon)  # type: ignore
        return constr

    # Struct ##################################################################
    elif isinstance(constr, cs.Struct):
        subcons = []
        for subcon in constr.subcons:
            subcons.append(include_metadata(subcon))
        return StructWithGuiMetadata(*subcons)

    # DataclassStruct #########################################################
    elif isinstance(constr, cst.DataclassStruct):
        subcons = []
        for subcon in constr.subcon.subcons:
            subcons.append(include_metadata(subcon))
        constr = DataclassStructWithGuiMetadata(constr.dc_type, constr.reverse)
        constr.subcon.subcons = subcons
        return constr

    # Array ###################################################################
    elif isinstance(constr, cs.Array):
        subcon = include_metadata(constr.subcon)
        return ArrayWithGuiMetadata(constr.count, subcon, constr.discard)

    # IfThenElse ##############################################################
    elif isinstance(constr, cs.IfThenElse):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        constr.thensubcon = include_metadata(constr.thensubcon)
        constr.elsesubcon = include_metadata(constr.elsesubcon)
        return constr

    # Switch ##################################################################
    elif isinstance(constr, cs.Switch):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        new_cases = {}
        for key, subcon in constr.cases.items():
            new_cases[key] = include_metadata(subcon)
        constr.cases = new_cases
        if constr.default is not None:
            constr.default = include_metadata(constr.default)
        return constr

    # Checksum #################################################################
    elif isinstance(constr, cs.Checksum):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        constr.checksumfield = include_metadata(constr.checksumfield)
        return constr

    # Renamed #################################################################
    elif isinstance(constr, cs.Renamed):
        constr = copy.copy(constr)  # constr is modified, so we have to make a copy
        constr.subcon = include_metadata(constr.subcon)  # type: ignore
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
        return constr

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
