import construct as cs
import construct_typed as cst
import dataclasses
from . import GalleryItem


@dataclasses.dataclass
class TBitsStructTest(cst.TContainerMixin):
    @dataclasses.dataclass
    class Nested(cst.TContainerMixin):
        test_bit: int = cst.sfield(cs.Bit)
        test_nibble: int = cst.sfield(cs.Nibble)
        test_bits_1: int = cst.sfield(cs.BitsInteger(3))
        test_bits_2: int = cst.sfield(cs.BitsInteger(6))
        test_bits_3: int = cst.sfield(cs.BitsInteger(2))

    nested: Nested = cst.sfield(cs.ByteSwapped(cst.DataclassBitStruct(Nested)))

    nested_reverse: Nested = cst.sfield(cst.DataclassBitStruct(Nested, reverse=True))


constr = cst.DataclassStruct(TBitsStructTest)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Zeros": bytes(constr.sizeof()),
    },
)
