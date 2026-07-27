from __future__ import annotations

import dataclasses

import construct as cs
import construct_typed as cst

from . import GalleryItem


class CarBrand(cst.EnumBase):
    Porsche = 0
    Audi = 4
    VW = 7


@dataclasses.dataclass
class Car(cst.DataclassMixin):
    const_brand: CarBrand = cst.csfield_const(cst.TEnum(cs.Int8ul, CarBrand), CarBrand.Audi)
    const_int: int = cst.csfield_const(cs.Int8ul, 15)
    const_bytes: bytes = cst.csfield_const(cs.Bytes(4), b"1234")


constr = cst.DataclassStruct(Car)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "1": b"\x04\x0f1234",
    },
)
