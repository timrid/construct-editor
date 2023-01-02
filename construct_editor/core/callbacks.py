# -*- coding: utf-8 -*-
from typing import Callable, Generic, TypeVar

from typing_extensions import ParamSpec

T = TypeVar("T")
P = ParamSpec("P")


class CallbackList(Generic[P]):
    def __init__(self):
        self._callbacks = []

    def append(self, callback: Callable[P, None]):
        """
        Add new callback function to the list (ignroe duplicates)
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove(self, callback: Callable[P, None]):
        """
        Remove callback function from the list.
        """
        self._callbacks.remove(callback)

    def clear(self):
        """
        Clear the complete list.
        """
        self._callbacks.clear()

    def fire(self, *args: P.args, **kwargs: P.kwargs):
        """
        Call all callback functions, with the given parameters.
        """
        for callback in self._callbacks:
            callback(*args, **kwargs)
