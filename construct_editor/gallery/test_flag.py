import construct as cs
from . import GalleryItem


constr = cs.Struct(
    "flag0" / cs.Flag,
    "flag1" / cs.Flag,

    "bit_struct" / cs.BitStruct(
        "bit_flag0" / cs.Flag,
        "bit_flag1" / cs.Flag,
        "bit_flag2" / cs.Flag,
        "bit_flag3" / cs.Flag,
        cs.Padding(4)
    )
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "1": bytes([0x01, 0x02, 0x40]),
        "Zeros": bytes(3),
    },
)