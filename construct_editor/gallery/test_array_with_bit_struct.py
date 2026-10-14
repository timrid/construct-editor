import dataclasses

import construct as cs
import construct_typed as cst

from construct_editor.gallery import GalleryItem


# Standard example structure ###############################################################################################
@dataclasses.dataclass
class Record(cst.DataclassMixin):
    @dataclasses.dataclass
    class Flags(cst.DataclassMixin):
        flag_1: bool = cst.csfield(cs.Flag)
        flag_2: bool = cst.csfield(cs.Flag)
        flag_3: bool = cst.csfield(cs.Flag)
        flag_4: bool = cst.csfield(cs.Flag)
        flag_5: bool = cst.csfield(cs.Flag)
        flag_6: bool = cst.csfield(cs.Flag)
        flag_7: bool = cst.csfield(cs.Flag)
        flag_8: bool = cst.csfield(cs.Flag)

    flags: Flags = cst.csfield(
        cs.ByteSwapped(cst.DataclassBitStruct(Flags, reverse=True)),
    )


constr = cs.GreedyRange(cst.DataclassStruct(Record))


_sample_record = constr.parse(bytes(constr.subcon.sizeof()))[0]
sample_records = [dataclasses.replace(_sample_record) for _ in range(2)]

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Sample": constr.build(sample_records),
    },
)
