import construct as cs
import construct_typed as cst
import dataclasses
import typing as t


@dataclasses.dataclass
class SwitchTest(cst.TContainerMixin):
    @dataclasses.dataclass
    class Case1(cst.TContainerMixin):
        case1_1: int = cst.sfield(cs.Int16sb)
        case1_2: int = cst.sfield(cs.Int16sb)

    @dataclasses.dataclass
    class Case2(cst.TContainerMixin):
        case2_1: int = cst.sfield(cs.Int8sb)
        case2_2: int = cst.sfield(cs.Int8sb)
        case2_3: int = cst.sfield(cs.Int8sb)
        case2_4: int = cst.sfield(cs.Int8sb)

    @dataclasses.dataclass
    class CaseDefault(cst.TContainerMixin):
        case_default_1: int = cst.sfield(cs.Int32sb)

    choice: int = cst.sfield(cs.Int8ub)
    switch: t.Union[Case1, Case2, CaseDefault] = cst.sfield(
        cs.Switch(
            cs.this.choice,
            {
                1: cst.TStruct(Case1),
                2: cst.TStruct(Case2),
            },
            cst.TStruct(CaseDefault),
        )
    )


constr = cst.TStruct(SwitchTest)
binarys = {
    "Zeros": bytes([0, 0, 0, 0, 0]),
    "1": bytes([1, 1, 2, 1, 2]),
}
