import construct as cs
import construct_typed as cst
import dataclasses


@dataclasses.dataclass
class TBitsStructTest(cst.TContainerMixin):
    @dataclasses.dataclass
    class Nested(cst.TContainerMixin):
        bit: int = cst.sfield(cs.Bit)
        bits_integer_1: int = cst.sfield(cs.BitsInteger(2))
        bits_integer_2: int = cst.sfield(cs.BitsInteger(5))

    nested: Nested = cst.sfield(cs.ByteSwapped(cst.TBitStruct(Nested)))

    nested_reverse: Nested = cst.sfield(
        cst.TBitStruct(Nested, reverse=True)
    )


constr = cst.TStruct(TBitsStructTest)
binarys = {
    "Zeros": bytes(2),
}
