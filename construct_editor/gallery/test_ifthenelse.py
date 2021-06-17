import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


@dataclasses.dataclass
class IfThenElse(cst.DataclassMixin):
    @dataclasses.dataclass
    class Then(cst.DataclassMixin):
        then_1: int = cst.csfield(cs.Int16sb)
        then_2: int = cst.csfield(cs.Int16sb)

    @dataclasses.dataclass
    class Else(cst.DataclassMixin):
        else_1: int = cst.csfield(cs.Int8sb)
        else_2: int = cst.csfield(cs.Int8sb)
        else_3: int = cst.csfield(cs.Int8sb)
        else_4: int = cst.csfield(cs.Int8sb)

    choice: int = cst.csfield(cs.Int8ub)
    if_then_else: t.Union[Then, Else] = cst.csfield(
        cs.IfThenElse(
            cs.this.choice == 0, cst.DataclassStruct(Then), cst.DataclassStruct(Else)
        )
    )


constr = cst.DataclassStruct(IfThenElse)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Zeros": bytes([0, 0, 0, 0, 0]),
        "1": bytes([0, 1, 2, 1, 2]),
    },
)