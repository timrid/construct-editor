import construct as cs
import construct_typed as cst
import dataclasses
from . import GalleryItem


class CarBrand(cst.EnumBase):
    Porsche = 0
    Audi = 4
    VW = 7


@dataclasses.dataclass
class Car(cst.DataclassMixin):
    default_brand: CarBrand = cst.csfield_default(cst.TEnum(cs.Int8ul, CarBrand), default=CarBrand.Audi)
    default_int: int = cst.csfield_default(cs.Int8ul, default=15)
    default_bytes: bytes = cst.csfield_default(cs.Bytes(4), default=b"1234")
    price: int = cst.csfield(cs.Int32ul, kw_only=True)  # must provide `kw_only` because field follows default-fields!


specific_car = Car(
    default_brand=CarBrand.Porsche,
    default_int=99,
    default_bytes=b"9999",
    price=10000,
)

default_car = Car(
    price=800,
)

constr = cst.DataclassStruct(Car)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Specific": constr.build(specific_car),
        "Default": constr.build(default_car),
    },
)
