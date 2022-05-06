import dataclasses
import typing as t

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


@dataclasses.dataclass
class Image(cst.DataclassMixin):
    is_big: int = cst.csfield(cs.Int8ub)
    data: t.Union[BigImage, SmallImage] = cst.csfield(
        cs.Select(
            cs.IfThenElse(
                condfunc=cs.this.is_big == 1,
                thensubcon=cs.Switch(
                    1,
                    cases={
                        1: cst.DataclassStruct(BigImage),
                        2: cst.DataclassStruct(BigImage),
                        3: cst.DataclassStruct(BigImage),
                        4: cst.DataclassStruct(BigImage),
                    },
                    default=cs.StopIf(True),
                ),
                elsesubcon=cst.DataclassStruct(SmallImage),
            ),
            cs.GreedyBytes,
        )
    )


constr = cst.DataclassStruct(Image)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Big": b"\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        "Small": b"\x00\x01\x08\x00\x00\x00\x00",
    },
)
