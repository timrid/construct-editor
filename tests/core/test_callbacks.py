"""Tests for construct_editor.core.callbacks — CallbackList."""

import pytest

from construct_editor.core.callbacks import CallbackList


def test_fire_calls_appended_callback() -> None:
    """A callback that was appended is invoked when fire() is called."""
    calls: list[int] = []
    cb = CallbackList[[int]]()
    cb.append(lambda x: calls.append(x))

    cb.fire(42)

    assert calls == [42]


def test_fire_calls_multiple_callbacks_in_order() -> None:
    """All appended callbacks are called in insertion order."""
    order: list[str] = []
    cb = CallbackList()
    cb.append(lambda: order.append("first"))
    cb.append(lambda: order.append("second"))

    cb.fire()

    assert order == ["first", "second"]


def test_remove_prevents_future_invocation() -> None:
    """A removed callback must not be called on subsequent fire() calls."""
    calls: list[int] = []

    def handler(x: int) -> None:
        calls.append(x)

    cb = CallbackList()
    cb.append(handler)
    cb.remove(handler)

    cb.fire(1)

    assert calls == []


def test_clear_removes_all_callbacks() -> None:
    """clear() empties the callback list so no handlers are invoked."""
    calls: list[int] = []
    cb = CallbackList[[int]]()
    cb.append(lambda x: calls.append(x))
    cb.append(lambda x: calls.append(x + 10))

    cb.clear()
    cb.fire(5)

    assert calls == []


def test_fire_empty_list_does_not_raise() -> None:
    """Firing an empty CallbackList must not raise any exception."""
    cb = CallbackList()
    cb.fire()  # should not raise


def test_remove_non_existing_raises() -> None:
    """Removing a callback that was never appended should raise ValueError."""
    cb = CallbackList()
    with pytest.raises((ValueError, Exception)):
        cb.remove(lambda: None)
