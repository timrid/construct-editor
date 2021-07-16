import construct as cs
from . import GalleryItem


constr = cs.Struct(
    "choice" / cs.Int32ul,
    "fixedsized"
    / cs.FixedSized(
        5,
        cs.Struct(
            switch=cs.Switch(
                cs.this._.choice,
                cases={
                    1: cs.Int8ul,
                    2: cs.Int16ul,
                },
                default=cs.Pass,
            ),
            bytes=cs.GreedyBytes,
        ),
    ),
    # "fixedsized" / cs.FixedSized(5, cs.GreedyBytes),
    "bytes2" / cs.Bytes(5),
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "1": bytes([1, 0, 0, 0, 0, 1, 2, 3, 4, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5]),
        "2": bytes([2, 0, 0, 0, 0, 1, 2, 3, 4, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5]),
        "Zeros": bytes(15),
    },
)
