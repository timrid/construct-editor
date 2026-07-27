from __future__ import annotations

from typing import Any, Dict

import construct as cs

from . import GalleryItem

ENCODDINGS = dict(
ASCII="ascii", 
UTF8="utf8",
UTF16="utf16",
MANDARIN="gb2312",
ARABIC="iso8859_6",
RUSSIAN="iso8859_5",
JAPANESE="shift_jis",
PORTUGUESE="cp860",
)

ENCODDINGS_NUMBER = dict([(key,number,) for number,(key,_) in enumerate(ENCODDINGS.items())]) 

def text_helper(encodding :str, text: str) -> bytes:
    return ENCODDINGS_NUMBER[encodding].to_bytes(1, "little") + text.encode(ENCODDINGS[encodding])

def generate_all_string_encodded() -> Dict[str, Any]:
    return dict([(key,cs.StringEncoded(cs.GreedyBytes, value),) for key,value in ENCODDINGS.items()])


constr = cs.Struct(
    "encodding" / cs.Enum(cs.Int8ub, **ENCODDINGS_NUMBER),
    "string"
    / cs.Switch(
        cs.this.encodding,
        cases=generate_all_string_encodded(),
    ),
)


gallery_item = GalleryItem(
    construct=constr,
    example_binarys={
        "English": text_helper("ASCII", "hello world"),
        "Mandarin" : text_helper("MANDARIN", "你好世界"),
        "HINDI" : text_helper("UTF8", "नमस्ते दुनिया"),
        "SPANISH" : text_helper("ASCII", "Hola Mundo"),
        "FRENCH" : text_helper("ASCII", "Bonjour le monde"),
        "ARABIC" : text_helper("ARABIC", "مرحبا بالعالم"),
        "RUSSIAN" : text_helper("RUSSIAN", "Привет мир"),
        "PORTUGUESE" : text_helper("PORTUGUESE", "Olá Mundo"),
        "INDONESIAN" : text_helper("ASCII", "Halo Dunia"),
        "JAPANESE" : text_helper("JAPANESE", "こんにちは世界"),
        "emoji": text_helper("UTF8", "🙋🏼🌎"),
        "Zeros": bytes(8),
    },
)
