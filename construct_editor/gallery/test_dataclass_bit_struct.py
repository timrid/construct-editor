import construct as cs
import construct_typed as cst
import dataclasses
from . import GalleryItem


@dataclasses.dataclass
class TBitsStructTest(cst.DataclassMixin):
    @dataclasses.dataclass
    class Nested(cst.DataclassMixin):
        test_bit: int = cst.csfield(cs.Bit)
        test_nibble: int = cst.csfield(cs.Nibble)
        test_bits_1: int = cst.csfield(cs.BitsInteger(3))
        test_bits_2: int = cst.csfield(cs.BitsInteger(6))
        test_bits_3: int = cst.csfield(cs.BitsInteger(2))

    nested: Nested = cst.csfield(cs.ByteSwapped(cst.DataclassBitStruct(Nested)))

    nested_reverse: Nested = cst.csfield(cst.DataclassBitStruct(Nested, reverse=True))


constr = cst.DataclassStruct(TBitsStructTest)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Zeros": bytes(constr.sizeof()),
    },
)
