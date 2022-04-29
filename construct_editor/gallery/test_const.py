import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


class CarBrand(cst.EnumBase):
    Porsche = 0
    Audi = 4
    VW = 7


@dataclasses.dataclass
class Car(cst.DataclassMixin):
    const_brand: CarBrand = cst.csfield(
        cs.Const(CarBrand.Audi, cst.TEnum(cs.Int8ul, CarBrand))
    )
    const_int: int = cst.csfield(cs.Const(15, cs.Int8ul))
    const_bytes: bytes = cst.csfield(cs.Const(b"1234"))


constr = cst.DataclassStruct(Car)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "1": b"\x04\x0f1234",
    },
)
