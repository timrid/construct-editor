import hashlib
import construct as cs
from . import GalleryItem


constr = cs.Struct(
    "checksum_start" / cs.Tell,
    "fields" / cs.Struct(
        cs.Padding(1000),
    ),
    "checksum_end" / cs.Tell,
    "checksum" / cs.Checksum(cs.Bytes(64),
        lambda data: hashlib.sha512(data).digest(),
        lambda ctx: ctx._io.getvalue()[ctx.checksum_start:ctx.checksum_end]),  # type: ignore
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "1": constr.build(dict(fields=dict(value={}))),
    },
)
