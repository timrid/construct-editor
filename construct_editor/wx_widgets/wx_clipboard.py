"""Thin wrapper around wx.TheClipboard.

Kept as small, free functions (rather than inlined wx.TheClipboard.Open()/
Close() calls) so tests can mock `get_text`/`set_text` instead of touching
the real OS clipboard.
"""

from __future__ import annotations

import wx


def get_text() -> str | None:
    """Return the current clipboard text, or None if the clipboard couldn't
    be opened."""
    if not wx.TheClipboard.Open():
        return None
    try:
        data = wx.TextDataObject()
        wx.TheClipboard.GetData(data)
        return data.GetText()
    finally:
        wx.TheClipboard.Close()


def set_text(text: str) -> bool:
    """Set the clipboard text. Return False if the clipboard couldn't be
    opened."""
    if not wx.TheClipboard.Open():
        return False
    try:
        wx.TheClipboard.SetData(wx.TextDataObject(text))
        return True
    finally:
        wx.TheClipboard.Close()
