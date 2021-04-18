import typing as t

T = t.TypeVar("T")


class CallbackList(t.List[T]):
    def fire(self, *args, **kwargs):
        for listener in self:
            listener(*args, **kwargs)  # type: ignore