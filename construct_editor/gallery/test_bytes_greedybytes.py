import construct as cs
from . import GalleryItem


constr = cs.Struct(
    "len" / cs.Int8ul,
    "bytes_fix" / cs.Bytes(5),
    "bytes_lambda" / cs.Bytes(lambda ctx: 2),
    "bytes_this" / cs.Bytes(cs.this.len),
    "greedybytes" / cs.GreedyBytes,
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Zeros": bytes([3]) + bytes(15),
        "1": b"\x03123456789ABCDEF",
    },
)