"""Thin wrapper around wx.TheClipboard.

Kept as small, free functions (rather than inlined wx.TheClipboard.Open()/
Close() calls) so tests can mock `get_text`/`set_text` instead of touching
the real OS clipboard.
"""

from __future__ import annotations

import wx


def get_text() -> str | None:
    """Return the current clipboard text.

    Returns None if the clipboard couldn't be opened (a warning is shown in
    that case) or if it doesn't currently hold text data (e.g. an image) -
    that's not an error, so no warning is shown for it.
    """
    if not wx.TheClipboard.Open():
        wx.MessageBox("Can't open the clipboard", "Warning")
        return None
    try:
        data = wx.TextDataObject()
        if not wx.TheClipboard.GetData(data):
            return None
        return data.GetText()
    finally:
        wx.TheClipboard.Close()


def set_text(text: str) -> bool:
    """Set the clipboard text. Return False if the clipboard couldn't be
    opened (a warning is shown in that case)."""
    if not wx.TheClipboard.Open():
        wx.MessageBox("Can't open the clipboard", "Warning")
        return False
    try:
        wx.TheClipboard.SetData(wx.TextDataObject(text))
        return True
    finally:
        wx.TheClipboard.Close()
