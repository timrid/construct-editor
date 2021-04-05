import construct as cs
import construct_typed as cst
import dataclasses
import typing as t


class CarBrand(cst.EnumBase):
    Porsche = 0
    Audi = 4
    VW = 7


class CarColor(cst.EnumBase):
    Red = 1
    Green = 10
    Blue = 11
    Black = 12


@dataclasses.dataclass
class Car(cst.TContainerMixin):
    brand: CarBrand = cst.sfield(cst.TEnum(cs.Int8ul, CarBrand))
    wheels: int = cst.sfield(cs.Int8ul)
    color: CarColor = cst.sfield(cst.TEnum(cs.Int8ul, CarColor))


constr = cst.TStruct(Car)
binarys = {
    "Zeros": bytes(constr.sizeof()),
    "1": bytes([4, 4, 12]),
    "2": bytes([4, 4, 13]),
    "3": bytes([7, 2, 1]),
}
