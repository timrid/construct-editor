import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


@dataclasses.dataclass
class DataclassStructTest(cst.TContainerMixin):
    width: int = cst.sfield(cs.Int8sb, doc="Das hier ist die Dokumentation von 'width'")
    height: int = cst.sfield(cs.Int8sb, doc="Und hier von 'height")
    update: int = cst.sfield(cs.Int8sb)

    @dataclasses.dataclass
    class Nested(cst.TContainerMixin):
        nested_width: int = cst.sfield(cs.Int16sb)
        nested_height: int = cst.sfield(cs.Int16sb)
        nested_bytes: bytes = cst.sfield(cs.Bytes(2))
        nested_array: t.List[int] = cst.sfield(cs.Array(2, cs.Int8sb))

    nested: Nested = cst.sfield((cst.DataclassStruct(Nested)))


constr = cst.DataclassStruct(DataclassStructTest)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Zeros": bytes(constr.sizeof()),
    },
)
