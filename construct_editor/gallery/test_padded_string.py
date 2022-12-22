import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


@dataclasses.dataclass
class DataclassStructTest(cst.DataclassMixin):
    value: str = cst.csfield(
        cs.PaddedString(10, "ascii"),
    )


constr = cst.DataclassStruct(DataclassStructTest)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "0": b"Hello".ljust(10, b"\x00"),
        "Zeros": bytes(constr.sizeof()),
    },
)
