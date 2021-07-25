import construct as cs
from . import GalleryItem


constr = cs.Struct(
    "compressed_bits"
    / cs.Prefixed(
        cs.VarInt,
        cs.Compressed(
            cs.BitStruct(
                "value1" / cs.BitsInteger(7),
                "value2" / cs.BitsInteger(3),
                "value3" / cs.BitsInteger(6),
            ),
            "zlib",
        ),
    ),
    "compressed_bytes"
    / cs.Prefixed(
        cs.VarInt,
        cs.Compressed(
            cs.Struct(
                "value1" / cs.Int8ul,
                "value2" / cs.Int16ul,
                "value3" / cs.Int8ul,
                "bits"
                / cs.BitStruct(
                    "bits1" / cs.BitsInteger(7),
                    "bits2" / cs.BitsInteger(3),
                    "bits3" / cs.BitsInteger(6),
                ),
                "swapped_bits"
                / cs.ByteSwapped(
                    cs.BitStruct(
                        "bits1" / cs.BitsInteger(7),
                        "bits2" / cs.BitsInteger(3),
                        "bits3" / cs.BitsInteger(6),
                    )
                ),
            ),
            "zlib",
        ),
    ),
)

# b = constr.build(
#     dict(
#         compressed_bits=dict(value1=0, value2=1, value3=3),
#         compressed_bytes=dict(value1=0, value2=1, value3=3, bits=dict(bits1=0, bits2=1, bits3=3),swapped_bits=dict(bits1=0, bits2=1, bits3=3),),
#     ),
# )
# print(b.hex())

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "1": bytes.fromhex("0a789c637006000045004410789c63606460667076660000016d008b"),
    },
)
