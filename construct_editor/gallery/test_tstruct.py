import construct as cs
import construct_typed as cst
import dataclasses
import typing as t


@dataclasses.dataclass
class TStructTest(cst.TContainerMixin):
    width: int = cst.sfield(cs.Int8sb, doc="Das hier ist die Dokumentation von 'width'")
    height: int = cst.sfield(cs.Int8sb, doc="Und hier von 'height")

    @dataclasses.dataclass
    class Nested(cst.TContainerMixin):
        nested_width: int = cst.sfield(cs.Int16sb)
        nested_height: int = cst.sfield(cs.Int16sb)
        nested_bytes: bytes = cst.sfield(cs.Bytes(2))
        nested_array: t.List[int] = cst.sfield(cs.Array(2, cs.Int8sb))

    nested: Nested = cst.sfield((cst.TStruct(Nested)))


constr = cst.TStruct(TStructTest)
binarys = {
    "Zeros":bytes(constr.sizeof()),
}
