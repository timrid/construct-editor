import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


@dataclasses.dataclass
class Entry(cst.DataclassMixin):
    id: int = cst.csfield(cs.Int8sb)
    width: int = cst.csfield(cs.Int8sb)
    height: int = cst.csfield(cs.Int8sb)


constr = cs.GreedyRange(cst.DataclassStruct(Entry))

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "5": bytes([1, 10, 10, 2, 10, 10, 3, 18, 18, 4, 10, 10, 5, 20, 20]),
        "1": bytes([1, 10, 10]),
        "Zeros": bytes([]),
    },
)