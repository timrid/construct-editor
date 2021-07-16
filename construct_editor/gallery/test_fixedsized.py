import construct as cs
from . import GalleryItem


constr = cs.Struct(
    "bytes1" / cs.Bytes(5),
    "fixedsized" / cs.FixedSized(5, cs.GreedyBytes),
    "bytes2" / cs.Bytes(5),
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "1": bytes([0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5]),
        "Zeros": bytes(15),
    },
)