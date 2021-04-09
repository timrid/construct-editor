import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


constr = cs.Struct(
    "signature" / cs.Bytes(23),
    "data_start_pos" / cs.Tell,
    "data_peek" / cs.Peek(cs.Array(5, cs.Int24ub)),
    cs.Seek(15, 1),
    "pos_after_seek" / cs.Tell,
    "data_pointer"
    / cs.Pointer(lambda ctx: ctx.data_start_pos, cs.Array(5, cs.Int24ub)),
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Zeros": bytes(23 + 15),
        "1": b"TestPointerPeekSeekTell0123456789abcde",
    },
)