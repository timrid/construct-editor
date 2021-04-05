import construct as cs
import construct_typed as cst
import dataclasses
import typing as t


@dataclasses.dataclass
class BitsTest(cst.TContainerMixin):
    width: int = cst.sfield(cs.Int8sb, doc="Das hier ist die Dokumentation von 'width'")
    height: int = cst.sfield(cs.Int8sb, doc="Und hier von 'height")

    @dataclasses.dataclass
    class Bits(cst.TContainerMixin):
        test_bit: int = cst.sfield(cs.Bit)
        test_nibble: int = cst.sfield(cs.Nibble)
        test_bits_1: int = cst.sfield(cs.BitsInteger(3))
        test_bits_2: int = cst.sfield(cs.BitsInteger(6))
        test_bits_3: int = cst.sfield(cs.BitsInteger(6))

    bits: Bits = cst.sfield(cst.TBitStruct(Bits))


constr = cst.TStruct(BitsTest)
binarys = {
    "Zeros": bytes(constr.sizeof()),
}