import construct as cs
import construct_typed as cst
import dataclasses
import typing as t


@dataclasses.dataclass
class TStructTest(cst.TContainerMixin):
    static: t.List[int] = cst.sfield(cs.Array(5, cs.Int8sb))
    dynamic_len: int = cst.sfield(cs.Int8sb, doc="Die Länge des dynamischen Array'")
    dynamic: t.List[int] = cst.sfield(cs.Array(cs.this.dynamic_len, cs.Int8sb))


constr = cst.TStruct(TStructTest)
binarys = {
    "Zeros": bytes([0, 0, 0, 0, 0, 0]),
    "1": bytes([1, 2, 3, 4, 5, 4, 1, 2, 3, 4]),
    "2": bytes([1, 2, 3, 4, 5, 8, 7, 6, 5, 4, 3, 2, 1, 0]),
}
