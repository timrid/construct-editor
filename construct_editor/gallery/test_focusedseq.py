import dataclasses

import construct as cs
import construct_typed as cst

from . import GalleryItem


@dataclasses.dataclass
class Image(cst.DataclassMixin):
    width: int = cst.csfield(cs.Int8sb)
    height: int = cst.csfield(cs.Int8sb)
    pixels: bytes = cst.csfield(cs.Bytes(4))


constr = cs.FocusedSeq(
    "image",
    "const" / cs.Const(b"MZ"),
    "image" / cst.DataclassStruct(Image),
    "const2" / cs.Const(b"MZ"),
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "1": b"MZ\x10\x20\x00\x00\x00\x00MZ",
    },
)
