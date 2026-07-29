"""Tests for HexEditorGrid.string_to_byts's paste-string parsing, covering
each of the accepted formats documented in its docstring.

Uses pytest.mark.parametrize since there are many equivalent-but-differently
-formatted input strings that should all parse to the same bytes — a single
parametrized test communicates "these are all valid spellings of the same
data" far better than a dozen near-identical individually named test
functions would. Formats that parse to genuinely different expected bytes
(the "0x.." list and the `b'...'` literal) get their own small test each.
"""

import pytest

from construct_editor.wx_widgets.wx_hex_editor import WxHexEditor
from tests.wx_integration.wx_test_helpers import editor_grid

_EXPECTED_1_TO_15 = bytes(range(1, 16))


@pytest.mark.parametrize(
    "byts_str",
    [
        "0102030405060708090a0b0c0d0e0f",
        "01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f",
        "01.02.03.04.05.06.07.08.09.0a.0b.0c.0d.0e.0f",
        "01-02-03-04-05-06-07-08-09-0a-0b-0c-0d-0e-0f",
        "1,2,3,4,5,6,7,8,9,a,b,c,d,e,f",
        "1 2 3 4 5 6 7 8 9 a b c d e f",
        "'0102030405060708090a0b0c0d0e0f'",
    ],
    ids=[
        "packed-hex",
        "space-separated-pairs",
        "dot-separated-pairs",
        "dash-separated-pairs",
        "comma-separated-nibbles",
        "space-separated-nibbles",
        "single-quoted-packed-hex",
    ],
)
def test_string_to_byts_parses_equivalent_formats_to_same_bytes(
    byts_str, wx_harness
) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"")

    assert editor_grid(editor).string_to_byts(byts_str) == _EXPECTED_1_TO_15


@pytest.mark.parametrize(
    "byts_str",
    [
        '"71 20 98 00 c0 7a 3e 6a 8d 7c c4 0d 04 10 02 f2 00"',
        '("71 20 98 00 c0 7a 3e 6a 8d 7c c4 0d 04 10 02 f2 00")',
        'bytes.fromhex("71 20 98 00 c0 7a 3e 6a 8d 7c c4 0d 04 10 02 f2 00")',
    ],
    ids=["quoted", "parenthesized-quoted", "bytes-fromhex-call"],
)
def test_string_to_byts_strips_surrounding_quotes_and_code(
    byts_str, wx_harness
) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"")

    result = editor_grid(editor).string_to_byts(byts_str)

    assert result == bytes.fromhex(
        "71 20 98 00 c0 7a 3e 6a 8d 7c c4 0d 04 10 02 f2 00"
    )


def test_string_to_byts_parses_0x_prefixed_comma_separated_list(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"")

    result = editor_grid(editor).string_to_byts("0x12, 0x23, 0x45,")

    assert result == b"\x12\x23\x45"


def test_string_to_byts_parses_python_bytes_repr_literal(wx_harness) -> None:
    editor = WxHexEditor(wx_harness.frame, binary=b"")

    result = editor_grid(editor).string_to_byts(
        r"b'\x00\x00\x00\xa4\xc18\xe1\x81_\x00\xcc#b\x0c\r\x15'"
    )

    assert result == b"\x00\x00\x00\xa4\xc18\xe1\x81_\x00\xcc#b\x0c\r\x15"


def test_string_to_byts_returns_none_and_shows_message_box_when_unparseable(
    wx_harness, mocker
) -> None:
    message_box = mocker.patch("wx.MessageBox")
    editor = WxHexEditor(wx_harness.frame, binary=b"")

    result = editor_grid(editor).string_to_byts("\\x")

    assert result is None
    message_box.assert_called_once()
