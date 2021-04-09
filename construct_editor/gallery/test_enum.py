import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


constr = cs.Struct(
    "brand" / cs.Enum(cs.Int8ul, Porsche=0, Audi=4, VW=7),
    "wheels" / cs.Int8ul,
    "color" / cs.Enum(cs.Int8ul, Red=1, Green=10, Blue=11, Black=12),
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Zeros": bytes(constr.sizeof()),
        "1": bytes([4, 4, 12]),
        "2": bytes([4, 4, 13]),
        "3": bytes([7, 2, 1]),
    },
)