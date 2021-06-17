import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


@dataclasses.dataclass
class DataclassStructTest(cst.DataclassMixin):
    width: int = cst.csfield(cs.Int8sb, doc="Das hier ist die Dokumentation von 'width'")
    height: int = cst.csfield(cs.Int8sb, doc="Und hier von 'height")
    update: int = cst.csfield(cs.Int8sb)

    @dataclasses.dataclass
    class Nested(cst.DataclassMixin):
        nested_width: int = cst.csfield(cs.Int16sb)
        nested_height: int = cst.csfield(cs.Int16sb)
        nested_bytes: bytes = cst.csfield(cs.Bytes(2))
        nested_array: t.List[int] = cst.csfield(cs.Array(2, cs.Int8sb))

    nested: Nested = cst.csfield((cst.DataclassStruct(Nested)))


constr = cst.DataclassStruct(DataclassStructTest)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Zeros": bytes(constr.sizeof()),
    },
)
