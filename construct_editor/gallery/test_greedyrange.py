import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


@dataclasses.dataclass
class GreedyRangeTest(cst.TContainerMixin):
    @dataclasses.dataclass
    class Entry(cst.TContainerMixin):
        id: int = cst.sfield(cs.Int8sb)
        width: int = cst.sfield(cs.Int8sb)
        height: int = cst.sfield(cs.Int8sb)

    entries: t.List[Entry] = cst.sfield(cs.GreedyRange(cst.DataclassStruct(Entry)))
    cnt: int = cst.sfield(cs.Computed(lambda ctx: len(ctx.entries)))


constr = cst.DataclassStruct(GreedyRangeTest)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Zeros": bytes([]),
        "1": bytes([1, 10, 10]),
        "5": bytes([1, 10, 10, 2, 10, 10, 3, 18, 18, 4, 10, 10, 5, 20, 20]),
    },
)