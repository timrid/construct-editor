import abc
import sys

import construct as cs
import wx

from construct_editor.wx_widgets import WxConstructHexEditor


def take_screenshot(win: wx.Window, file_name: str):
    """
    Takes a screenshot of the screen at give pos & size (rect).
    """
    rect: wx.Rect = win.GetClientRect()
    rect.SetPosition(win.ClientToScreen(0, 0))
    # see http://aspn.activestate.com/ASPN/Mail/Message/wxpython-users/3575899
    # created by Andrea Gavana

    # adjust widths for Linux (figured out by John Torres
    # http://article.gmane.org/gmane.comp.python.wxpython/67327)
    if sys.platform == "linux2":
        client_x, client_y = win.ClientToScreen((0, 0))
        border_width = client_x - rect.x
        title_bar_height = client_y - rect.y
        rect.width += border_width * 2
        rect.height += title_bar_height + border_width

    # Create a DC for the whole screen area
    dcScreen = wx.ScreenDC()

    # Create a Bitmap that will hold the screenshot image later on
    # Note that the Bitmap must have a size big enough to hold the screenshot
    # -1 means using the current default colour depth
    bmp: wx.Bitmap = wx.Bitmap(rect.width, rect.height)

    # Create a memory DC that will be used for actually taking the screenshot
    memDC = wx.MemoryDC()

    # Tell the memory DC to use our Bitmap
    # all drawing action on the memory DC will go to the Bitmap now
    memDC.SelectObject(bmp)

    # Blit (in this case copy) the actual screen on the memory DC
    # and thus the Bitmap
    memDC.Blit(
        0,  # Copy to this X coordinate
        0,  # Copy to this Y coordinate
        rect.width,  # Copy this width
        rect.height,  # Copy this height
        dcScreen,  # From where do we copy?
        rect.x,  # What's the X offset in the original DC?
        rect.y,  # What's the Y offset in the original DC?
    )

    # Select the Bitmap out of the memory DC by selecting a new
    # uninitialized Bitmap
    memDC.SelectObject(wx.NullBitmap)
    img: wx.Image = bmp.ConvertToImage()

    img.SaveFile(str(file_name), wx.BITMAP_TYPE_PNG)


SCREENSHOT_FOLDER = "doc/screenshots/"


class ScreenshotFrame(wx.Frame):
    screenshot_name: str

    def __init__(self, auto_close: bool):
        super().__init__(None)
        self.SetTitle("Construct Hex Editor Example")
        self.SetSize(1000, 400)
        self.Center()

        self.auto_close = auto_close

        self.editor_panel = WxConstructHexEditor(self, construct=cs.Pass, binary=b"")

        self.init_example()

        wx.CallLater(100, self._take_screenshot_and_close)

    def _take_screenshot_and_close(self):
        take_screenshot(
            self.editor_panel,
            SCREENSHOT_FOLDER + f"{self.screenshot_name}_{sys.platform}.png",
        )
        if self.auto_close is True:
            self.Close()

    @abc.abstractmethod
    def init_example(self):
        ...

    @classmethod
    def create_screenshot(cls, auto_close: bool = True):
        app = wx.App(False)
        frame = cls(auto_close)
        frame.Show(True)
        app.MainLoop()
