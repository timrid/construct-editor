import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


@dataclasses.dataclass
class ArrayTest(cst.DataclassMixin):
    simple_static: t.List[int] = cst.csfield(cs.Array(5, cs.Int8ul))

    simple_dynamic_len: int = cst.csfield(
        cs.Int32ul, doc="Length of the simple dynamic array"
    )
    simple_dynamic: t.List[int] = cst.csfield(
        cs.Array(cs.this.simple_dynamic_len, cs.Int8ul)
    )

    @dataclasses.dataclass
    class Entry(cst.DataclassMixin):
        id: int = cst.csfield(cs.Int8ul)
        width: int = cst.csfield(cs.Int8ul)
        height: int = cst.csfield(cs.Int8ul)

    struct_static: t.List[Entry] = cst.csfield(cs.Array(3, cst.DataclassStruct(Entry)))

    struct_dynamic_len: int = cst.csfield(
        cs.Int8ul, doc="Length of the struct dynamic array"
    )
    struct_dynamic: t.List[Entry] = cst.csfield(
        cs.Array(cs.this.struct_dynamic_len, cst.DataclassStruct(Entry))
    )


constr = cst.DataclassStruct(ArrayTest)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Zeros": bytes(5 + 4 + 3 * 3 + 1),
        "1": (
            bytes([1, 2, 3, 4, 5, 4, 0, 0, 0, 1, 2, 3, 4])
            + bytes([0xA0, 0xA1, 0xA2, 0xB0, 0xB1, 0xB2, 0xC0, 0xC1, 0xC2])
            + bytes([2, 0xA0, 0xA1, 0xA2, 0xB0, 0xB1, 0xB2])
        ),
        "2": (
            bytes([1, 2, 3, 4, 5, 8, 0, 0, 0, 7, 6, 5, 4, 3, 2, 1, 0])
            + bytes([0xA0, 0xA1, 0xA2, 0xB0, 0xB1, 0xB2, 0xC0, 0xC1, 0xC2])
            + bytes([3, 0xA0, 0xA1, 0xA2, 0xB0, 0xB1, 0xB2, 0xC0, 0xC1, 0xC2])
        ),
        "Huge": (
            bytes([1, 2, 3, 4, 5, 0x20, 0x4E, 0, 0] + ([0]*20000))
            + bytes([0xA0, 0xA1, 0xA2, 0xB0, 0xB1, 0xB2, 0xC0, 0xC1, 0xC2])
            + bytes([3, 0xA0, 0xA1, 0xA2, 0xB0, 0xB1, 0xB2, 0xC0, 0xC1, 0xC2])
        ),
    },
)