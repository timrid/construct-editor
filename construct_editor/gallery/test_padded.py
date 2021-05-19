import construct as cs
from . import GalleryItem


constr = cs.Struct(
    "padded" / cs.Padded(5, cs.Bytes(3)),
    "padding" / cs.Padding(5),
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "1": bytes([0, 1, 2, 3, 4, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5]),
        "Zeros": bytes(10),
    },
)