import dataclasses
import construct as cs
import typing as t


@dataclasses.dataclass
class GalleryItem:
    construct: "cs.Construct[t.Any, t.Any]"
    contextkw: t.Dict[str, t.Any] = dataclasses.field(default_factory=dict)
    example_binarys: t.Dict[str, bytes] = dataclasses.field(default_factory=dict)
