import construct as cs
from . import GalleryItem


constr = cs.Struct(
    "null_terminated" / cs.NullTerminated(cs.Int16ul, term=b"\x00"),
    "remaining" / cs.GreedyBytes,
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "1": bytes([10, 20, 0, 0xFF, 0xFF]),
        "Zeros": bytes(15),
    },
)
