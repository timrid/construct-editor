import dataclasses

import construct as cs
import construct_typed as cst

from . import GalleryItem


@dataclasses.dataclass
class BigImage(cst.DataclassMixin):
    big_width: int = cst.csfield(cs.Int8sb)
    big_height: int = cst.csfield(cs.Int8sb)
    big_pixels: bytes = cst.csfield(cs.Bytes(10))


@dataclasses.dataclass
class SmallImage(cst.DataclassMixin):
    small_width: int = cst.csfield(cs.Int8sb)
    small_height: int = cst.csfield(cs.Int8sb)
    small_pixels: bytes = cst.csfield(cs.Bytes(4))


constr = cs.Select(
    cst.DataclassStruct(BigImage),
    cst.DataclassStruct(SmallImage),
)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Big": b"\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        "Small": b"\x01\x08\x00\x00\x00\x00",
    },
)
