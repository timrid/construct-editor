import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


@dataclasses.dataclass
class SwitchTest(cst.DataclassMixin):
    @dataclasses.dataclass
    class Case1(cst.DataclassMixin):
        case1_1: int = cst.csfield(cs.Int16sb)
        case1_2: int = cst.csfield(cs.Int16sb)

    @dataclasses.dataclass
    class Case2(cst.DataclassMixin):
        case2_1: int = cst.csfield(cs.Int8sb)
        case2_2: int = cst.csfield(cs.Int8sb)
        case2_3: int = cst.csfield(cs.Int8sb)
        case2_4: int = cst.csfield(cs.Int8sb)

    @dataclasses.dataclass
    class CaseDefault(cst.DataclassMixin):
        case_default_1: int = cst.csfield(cs.Int32sb)

    choice: int = cst.csfield(cs.Int8ub)
    switch: t.Union[Case1, Case2, CaseDefault] = cst.csfield(
        cs.Switch(
            cs.this.choice,
            cases={
                1: cst.DataclassStruct(Case1),
                2: cst.DataclassStruct(Case2),
            },
            default=cst.DataclassStruct(CaseDefault),
        )
    )

    switch_without_default: t.Union[Case1, Case2, None] = cst.csfield(
        cs.Switch(
            cs.this.choice,
            cases={
                1: cst.DataclassStruct(Case1),
                2: cst.DataclassStruct(Case2),
            },
            default=cs.Pass,
        )
    )


constr = cst.DataclassStruct(SwitchTest)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Default": bytes([0, 0, 0, 0, 0]),
        "Case 1": bytes([1, 1, 2, 1, 2, 5, 6, 7, 8]),
        "Case 2": bytes([2, 1, 2, 1, 2, 5, 6, 7, 8]),
    },
)