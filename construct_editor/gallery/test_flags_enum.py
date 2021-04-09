import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


constr = cs.Struct(
    "permissions" / cs.FlagsEnum(cs.Int8ul, R=4, W=2, X=1),
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "read": bytes([4]),
        "read_write": bytes([6]),
    },
)