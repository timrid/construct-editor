import construct as cs
from . import GalleryItem


constr = cs.Struct(
    "before" / cs.Int8ub,
    "aligned_16" / cs.Aligned(5, cs.Bytes(3)),
    "aligned_len" / cs.Int8ub,
    "aligned" / cs.Aligned(5, cs.Bytes(cs.this.aligned_len)),
    "after" / cs.Int8ub,
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "1": bytes([0xF0, 0, 1, 2, 3, 4, 6, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0xFF]),
        "Zeros": bytes(8),
    },
)