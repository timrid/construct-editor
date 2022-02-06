import construct as cs
from . import GalleryItem


constr = cs.Struct(
    "null_stripped" / cs.NullStripped(cs.GreedyBytes, pad=b"\x00"),
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "1": b"Hallo Welt!\x00\x00\x00",
        "Zeros": bytes(15),
    },
)
