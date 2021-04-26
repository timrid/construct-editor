import construct as cs
from . import GalleryItem


constr = cs.Struct(
    "value1" / cs.Int8sb,
    "pass" / cs.Pass,
    "value2" / cs.Int8sb,
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Zeros": bytes(2),
        "1": b"12",
    },
)