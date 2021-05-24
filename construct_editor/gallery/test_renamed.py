import construct as cs
import construct_typed as cst
import dataclasses
import typing as t
from . import GalleryItem


@dataclasses.dataclass
class RenamedTest(cst.TContainerMixin):
    height: int = cst.sfield(cs.Int8sb, doc="Und hier von 'height")
    doc: int = cst.sfield(cs.Int8sb, doc="Das hier ist die Dokumentation von 'width'")
    doc_multiline: int = cst.sfield(
        cs.Int8sb,
        doc="""
        Das hier ist die Dokumentation von 'width'
        """,
    )
    doc2: int = cst.sfield(cs.Int8sb * "Das hier ist die Dokumentation von 'width'")
    doc2_multiline: int = cst.sfield(
        cs.Int8sb
        * """
        Das hier ist die Dokumentation von 'width'
        """
    )


constr = "renamed_test" / cst.DataclassStruct(RenamedTest)

gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "Zeros": bytes(constr.sizeof()),
    },
)