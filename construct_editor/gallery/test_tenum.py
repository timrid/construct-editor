import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


class CarBrand(cst.EnumBase):
    Porsche = 0
    Audi = 4
    VW = 7


class CarColor(cst.EnumBase):
    Red = 1
    Green = 10
    Blue = 11
    Black = 12


class LongList(cst.EnumBase):
    Entry0 = 0
    Entry1 = 1
    Entry2 = 2
    Entry3 = 3
    Entry4 = 4
    Entry5 = 5
    Entry6 = 6
    Entry7 = 7
    Entry8 = 8
    Entry9 = 9
    Entry10 = 10
    Entry11 = 11
    Entry12 = 12
    Entry13 = 13
    Entry14 = 14
    Entry15 = 15
    Entry16 = 16
    Entry17 = 17
    Entry18 = 18
    Entry19 = 19
    Entry20 = 20
    Entry21 = 21
    Entry22 = 22
    Entry23 = 23
    Entry24 = 24
    Entry25 = 25
    Entry26 = 26
    Entry27 = 27
    Entry28 = 28
    Entry29 = 29
    Entry30 = 30
    Entry31 = 31
    Entry32 = 32
    Entry33 = 33
    Entry34 = 34
    Entry35 = 35
    Entry36 = 36
    Entry37 = 37
    Entry38 = 38
    Entry39 = 39
    Entry40 = 40
    Entry41 = 41
    Entry42 = 42
    Entry43 = 43
    Entry44 = 44
    Entry45 = 45
    Entry46 = 46
    Entry47 = 47
    Entry48 = 48
    Entry49 = 49
    Entry50 = 50


@dataclasses.dataclass
class Car(cst.DataclassMixin):
    brand: CarBrand = cst.csfield(cst.TEnum(cs.Int8ul, CarBrand))
    wheels: int = cst.csfield(cs.Int8ul)
    color: CarColor = cst.csfield(cst.TEnum(cs.Int8ul, CarColor))
    long_list: LongList = cst.csfield(cst.TEnum(cs.Int8ul, LongList))


constr = cst.DataclassStruct(Car)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "3": bytes([7, 2, 1, 7]),
        "2": bytes([4, 4, 13, 6]),
        "1": bytes([4, 4, 12, 5]),
        "Zeros": bytes(constr.sizeof()),
    },
)