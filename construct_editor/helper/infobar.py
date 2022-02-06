import wx.lib.agw.infobar
import wx


class CustomInfoBar(wx.lib.agw.infobar.InfoBar):
    def __init__(
        self,
        parent,
        id=wx.ID_ANY,
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=0,
        name="CustomInfoBar",
    ):
        super().__init__(parent, id, pos, size, style, name)

        sizer: wx.Sizer = self.GetSizer()

        # dont show Close Button
        if self._button is not None:
            if sizer.Detach(self._button):
                self._button.Hide()

    def show_info(self, s: str):
        self.ShowMessage(
            s,
            wx.ICON_INFORMATION,
        )

    def show_parsing_error(self, e: Exception):
        self.ShowMessage(
            f"Error while parsing binary data: {type(e).__name__}\n{str(e)}",
            wx.ICON_WARNING,
        )

    def show_building_error(self, e: Exception):
        self.ShowMessage(
            f"Error while building binary data: {type(e).__name__}\n{str(e)}",
            wx.ICON_WARNING,
        )
