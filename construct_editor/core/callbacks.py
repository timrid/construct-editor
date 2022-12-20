# -*- coding: utf-8 -*-
from typing import Callable, Generic, TypeVar

from typing_extensions import ParamSpec

T = TypeVar("T")
P = ParamSpec("P")


class CallbackListNew(Generic[P]):
    def __init__(self):
        self._callbacks = []

    def append(self, callback: Callable[P, None]):
        """
        Neue Callback-Funktion in die Liste einfügen (Duplikate werden ignoriert)
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove(self, callback: Callable[P, None]):
        """
        Callback-Funktion aus der Liste entfernen
        """
        self._callbacks.remove(callback)

    def clear(self):
        """
        Alle Callback-Funktion entfernen
        """
        self._callbacks.clear()

    def fire(self, *args: P.args, **kwargs: P.kwargs):
        """
        Alle Callbacks aufrufen
        """
        for callback in self._callbacks:
            callback(*args, **kwargs)
