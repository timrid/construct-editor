import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


constr = cs.Struct(
    "choice"
    / cs.Enum(
        cs.Int8ub,
        USE_CHOICE1=1,
        USE_CHOICE2=2,
    ),
    "switch"
    / cs.Switch(
        cs.this.choice,
        cases={
            "USE_CHOICE1": cs.Struct(
                "case1_1" / cs.Default(cs.Int16sb, 0),
                "case1_2" / cs.Default(cs.Int16sb, 0),
            ),
            "USE_CHOICE2": cs.Struct(
                "case2_1" / cs.Int8sb,
                "case2_2" / cs.Int8sb,
                "case2_3" / cs.Int8sb,
                "case2_4" / cs.Int8sb,
            ),
        },
        default=cs.Struct(
            "case_default_1" / cs.Int32sb,
        ),
    ),
    "switch_without_default"
    / cs.Switch(
        cs.this.choice,
        cases={
            "USE_CHOICE1": cs.Struct(
                "case1_1" / cs.Int16sb,
                "case1_2" / cs.Int16sb,
            ),
            "USE_CHOICE2": cs.Struct(
                "case2_1" / cs.Int8sb,
                "case2_2" / cs.Int8sb,
                "case2_3" / cs.Int8sb,
                "case2_4" / cs.Int8sb,
            ),
        },
        default=cs.Pass,
    ),
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Default": bytes([0, 0, 0, 0, 0]),
        "Case 1": bytes([1, 1, 2, 1, 2, 5, 6, 7, 8]),
        "Case 2": bytes([2, 1, 2, 1, 2, 5, 6, 7, 8]),
    },
)
