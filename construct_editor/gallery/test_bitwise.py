import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


constr = cs.Bitwise(cs.GreedyRange(cs.Bit))

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "1": bytes([1, 2, 3, 4]),
        "Zeros": bytes(0),
        "Huge": bytes(10000),
    },
)
