import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


@dataclasses.dataclass
class ComputedTest(cst.DataclassMixin):
    type_int: int = cst.csfield(cs.Computed(lambda ctx: 50))
    type_float: float = cst.csfield(cs.Computed(lambda ctx: 80.0))
    type_bool: bool = cst.csfield(cs.Computed(lambda ctx: True))
    type_bytes: bytes = cst.csfield(cs.Computed(lambda ctx: bytes([0x00, 0xAB])))
    type_bytearray: bytearray = cst.csfield(
        cs.Computed(lambda ctx: bytearray([0x00, 0xAB, 0xFF]))
    )


constr = cst.DataclassStruct(ComputedTest)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={"Zeros": bytes([])},
)