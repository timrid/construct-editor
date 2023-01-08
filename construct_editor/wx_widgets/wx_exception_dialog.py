import dataclasses
import traceback
import typing as t
from types import TracebackType

import wx


@dataclasses.dataclass
class ExceptionInfo:
    etype: t.Type[BaseException]
    value: BaseException
    trace: t.Optional[TracebackType]


class WxExceptionDialog(wx.Dialog):
    def __init__(
        self, parent, title: str, exception: t.Union[ExceptionInfo, BaseException]
    ):
        wx.Dialog.__init__(
            self,
            parent,
            id=wx.ID_ANY,
            title=title,
            pos=wx.DefaultPosition,
            size=wx.Size(800, 600),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        self._init_gui()

        if isinstance(exception, ExceptionInfo):
            exception_info = exception
        else:
            exception_info = ExceptionInfo(
                type(exception), exception, exception.__traceback__
            )

        self.exception_txt.SetValue(
            "".join(
                traceback.format_exception_only(
                    exception_info.etype, exception_info.value
                )
            )
        )

        if exception_info.trace is None:
            self.traceback_txt.SetValue("")
        else:
            self.traceback_txt.SetValue(
                "".join(traceback.format_tb(exception_info.trace))
            )

    def _init_gui(self):
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.ok_btn = wx.Button(
            self, wx.ID_ANY, "OK", wx.DefaultPosition, wx.DefaultSize, 0
        )
        sizer.Add(self.ok_btn, 0, wx.ALL | wx.EXPAND, 5)

        self.exception_txt = wx.TextCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.Size(-1, -1),
            wx.TE_MULTILINE | wx.TE_READONLY,
        )
        sizer.Add(self.exception_txt, 1, wx.ALL | wx.EXPAND, 5)

        self.traceback_txt = wx.TextCtrl(
            self,
            wx.ID_ANY,
            wx.EmptyString,
            wx.DefaultPosition,
            wx.Size(-1, -1),
            wx.TE_MULTILINE | wx.TE_READONLY,
        )
        sizer.Add(self.traceback_txt, 2, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(sizer)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok_clicked)

    def on_ok_clicked(self, event):
        self.Close()
