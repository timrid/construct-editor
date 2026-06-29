import dataclasses

import construct as cs
import construct_typed as cst

from . import GalleryItem


@dataclasses.dataclass
class ComputedTest(cst.DataclassMixin):
    type_int_const: int = cst.csfield(cs.Computed(50))
    type_int_lambda: int = cst.csfield(cs.Computed(lambda ctx: 50))
    type_float_const: float = cst.csfield(cs.Computed(80.0))
    type_float_lambda: float = cst.csfield(cs.Computed(lambda ctx: 80.0))
    type_bool_const: bool = cst.csfield(cs.Computed(True))
    type_bool_lambda: bool = cst.csfield(cs.Computed(lambda ctx: True))
    type_bytes_const: bytes = cst.csfield(cs.Computed(bytes([0x00, 0xAB])))
    type_bytes_lambda: bytes = cst.csfield(cs.Computed(lambda ctx: bytes([0x00, 0xAB])))
    type_bytearray_const: bytearray = cst.csfield(cs.Computed(bytearray([0x00, 0xAB, 0xFF])))
    type_bytearray_lambda: bytearray = cst.csfield(cs.Computed(lambda ctx: bytearray([0x00, 0xAB, 0xFF])))


constr = cst.DataclassStruct(ComputedTest)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={"Zeros": bytes([])},
)
