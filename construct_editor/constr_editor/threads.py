import ctypes
import threading
import inspect
import typing as t
import construct as cs

# see: https://stackoverflow.com/a/325528


def _async_raise(tid, exctype):
    """Raises an exception in the threads with id tid"""
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(tid), ctypes.py_object(exctype)
    )
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # "if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


class ThreadWithExc(threading.Thread):
    """A thread class that supports raising an exception in the thread from
    another thread.
    """

    def _get_my_tid(self):
        """determines this (self's) thread id

        CAREFUL: this function is executed in the context of the caller
        thread, to get the identity of the thread represented by this
        instance.
        """
        if not self.isAlive():
            raise threading.ThreadError("the thread is not active")

        # do we have it cached?
        if hasattr(self, "_thread_id"):
            return self._thread_id

        # no, look for it in the _active dict
        for tid, tobj in threading._active.items():  # type: ignore
            if tobj is self:
                self._thread_id = tid
                return tid

        # TODO: in python 2.6, there's a simpler way to do: self.ident

        raise AssertionError("could not determine the thread's id")

    def raise_exc(self, exctype):
        """Raises the given exception type in the context of this thread.

        If the thread is busy in a system call (time.sleep(),
        socket.accept(), ...), the exception is simply ignored.

        If you are sure that your exception should terminate the thread,
        one way to ensure that it works is:

            t = ThreadWithExc( ... )
            ...
            t.raiseExc( SomeException )
            while t.isAlive():
                time.sleep( 0.1 )
                t.raiseExc( SomeException )

        If the exception is to be caught by the thread, you need a way to
        check that your thread has caught it.

        CAREFUL: this function is executed in the context of the
        caller thread, to raise an exception in the context of the
        thread represented by this instance.
        """
        _async_raise(self._get_my_tid(), exctype)

    def terminate(self):
        """raises SystemExit in the context of the given thread, which should
        cause the thread to exit silently (unless caught)"""
        self.raise_exc(SystemExit)


class ParserThread(ThreadWithExc):
    def __init__(
        self,
        constr: "cs.Construct[t.Any, t.Any]",
        data: bytes,
        contextkw: t.Dict[str, t.Any],
        on_done: t.Callable[[t.Union[t.Any, Exception]], None],
    ):
        super().__init__()
        self._constr = constr
        self._data = data
        self._contextkw = contextkw
        self._on_done = on_done

    def run(self):
        try:
            obj = self._constr.parse(self._data, **self._contextkw)
            self._on_done(obj)
        except Exception as e:
            self._on_done(e)


class BuilderThread(ThreadWithExc):
    def __init__(
        self,
        constr: "cs.Construct[t.Any, t.Any]",
        obj: t.Any,
        contextkw: t.Dict[str, t.Any],
        on_done: t.Callable[[t.Union[bytes, Exception]], None],
    ):
        super().__init__()
        self._constr = constr
        self._obj = obj
        self._contextkw = contextkw
        self._on_done = on_done

    def run(self):
        try:
            byts = self._constr.build(self._obj, **self._contextkw)
            self._on_done(byts)
        except Exception as e:
            self._on_done(e)
