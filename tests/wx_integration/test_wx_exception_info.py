"""Tests for construct_editor.wx_widgets.wx_exception_dialog.ExceptionInfo (no wx required)."""

from construct_editor.wx_widgets.wx_exception_dialog import ExceptionInfo


def test_fields_stored_correctly() -> None:
    """ExceptionInfo must store etype, value, and trace."""
    try:
        raise ValueError("boom")
    except ValueError as exc:
        import sys

        etype, value, trace = sys.exc_info()
        assert etype is not None
        assert value is not None
        info = ExceptionInfo(etype=etype, value=value, trace=trace)
        assert info.etype is ValueError
        assert info.value is exc
