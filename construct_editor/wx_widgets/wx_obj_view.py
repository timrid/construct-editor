import typing as t

import arrow
import wx
import wx.adv
import wx.dataview as dv

import construct_editor.wx_widgets.wx_construct_editor as wx_construct_editor
from construct_editor.core.entries import (
    EntryFlagsEnum,
    EntryTFlagsEnum,
    FlagsEnumItem,
    ObjViewSettings,
    ObjViewSettings_Bytes,
    ObjViewSettings_Default,
    ObjViewSettings_Enum,
    ObjViewSettings_Flag,
    ObjViewSettings_FlagsEnum,
    ObjViewSettings_Integer,
    ObjViewSettings_String,
    ObjViewSettings_Timestamp,
    int_to_str,
    str_to_bytes,
    str_to_int,
)


# #####################################################################################################################
# Value Editors
# #####################################################################################################################
class WxObjEditor_Default(wx.TextCtrl):
    def __init__(self, parent, settings: ObjViewSettings):
        self.entry = settings.entry

        super(wx.TextCtrl, self).__init__(
            parent,
            wx.ID_ANY,
            self.entry.obj_str,
            wx.DefaultPosition,
            wx.Size(-1, -1),
            style=wx.TE_READONLY,
        )

    def get_new_obj(self) -> t.Any:
        return self.entry.obj


class WxObjEditor_String(wx.TextCtrl):
    def __init__(self, parent, settings: ObjViewSettings_String):
        self.entry = settings.entry

        super(wx.TextCtrl, self).__init__(
            parent,
            wx.ID_ANY,
            self.entry.obj_str,
            style=wx.TE_PROCESS_ENTER,
        )

        self.SelectAll()

    def get_new_obj(self) -> t.Any:
        val_str: str = self.GetValue()
        return val_str


class WxObjEditor_Integer(wx.TextCtrl):
    def __init__(self, parent, settings: ObjViewSettings_Integer):
        self.entry = settings.entry

        super(wx.TextCtrl, self).__init__(
            parent,
            wx.ID_ANY,
            self.entry.obj_str,
            style=wx.TE_PROCESS_ENTER,
        )

        self.SelectAll()

    def get_new_obj(self) -> t.Any:
        val_str: str = self.GetValue()

        try:
            # convert string to integer
            new_obj = str_to_int(val_str)
        except Exception:
            new_obj = val_str  # this will probably result in a building error

        return new_obj


class WxObjEditor_Bytes(wx.TextCtrl):
    def __init__(self, parent, settings: ObjViewSettings_Bytes):
        self.entry = settings.entry

        super(wx.TextCtrl, self).__init__(
            parent,
            wx.ID_ANY,
            settings.entry.obj_str,
            style=wx.TE_PROCESS_ENTER,
        )

        self.SelectAll()

    def get_new_obj(self) -> t.Any:
        val_str: str = self.GetValue()

        try:
            # convert string to bytes
            new_obj = str_to_bytes(val_str)
        except Exception:
            new_obj = val_str  # this will probably result in a building error

        return new_obj


class WxObjEditor_Enum(wx.ComboBox):
    def __init__(self, parent, settings: ObjViewSettings_Enum):
        self.entry = settings.entry

        super(wx.ComboBox, self).__init__(
            parent,
            style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER,
        )

        items = self.entry.get_enum_items()
        for pos, item in enumerate(items):
            self.Insert(
                item=f"{int_to_str(self.entry.model.integer_format, item.value)} ({item.name})",
                pos=pos,
                clientData=item,
            )
        item = self.entry.get_enum_item_from_obj()
        sel_item_str = (
            f"{int_to_str(self.entry.model.integer_format, item.value)} ({item.name})"
        )
        self.SetStringSelection(sel_item_str)
        self.SetValue(sel_item_str)  # show even if it is not in the list

    def get_new_obj(self) -> t.Any:
        val_str: str = self.GetValue()
        if len(val_str) == 0:
            val_str = "0"

        val_str = val_str.split()[0]
        new_obj = self.entry.conv_str_to_obj(val_str)
        return new_obj


class FlagsEnumComboPopup(wx.ComboPopup):
    def __init__(
        self,
        combo_ctrl: wx.ComboCtrl,
        entry: t.Union["EntryTFlagsEnum", "EntryFlagsEnum"],
    ):
        super().__init__()
        self.combo_ctrl = combo_ctrl
        self.entry = entry
        self.clbx: wx.CheckListBox

    def on_motion(self, evt):
        item = self.clbx.HitTest(evt.GetPosition())
        if item != wx.NOT_FOUND:
            # only select if not selected prevents flickering
            if not self.clbx.IsSelected(item):
                self.clbx.Select(item)

    def on_left_down(self, evt):
        item = self.clbx.HitTest(evt.GetPosition())
        if item != wx.NOT_FOUND:
            # select the new item in the gui
            items = list(self.clbx.GetCheckedItems())
            if item in items:
                items.remove(item)
            else:
                items.append(item)
            self.clbx.SetCheckedItems(items)

            # refresh shown string
            self.combo_ctrl.SetValue(self.GetStringValue())

    def Create(self, parent):
        self.clbx = wx.CheckListBox(parent)
        self.clbx.Bind(wx.EVT_MOTION, self.on_motion)
        self.clbx.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        return True

    # Return the widget that is to be used for the popup
    def GetControl(self):
        return self.clbx

    # Return final size of popup. Called on every popup, just prior to OnPopup.
    # minWidth = preferred minimum width for window
    # prefHeight = preferred height. Only applies if > 0,
    # maxHeight = max height for window, as limited by screen size
    #   and should only be rounded down, if necessary.
    def GetAdjustedSize(self, minWidth, prefHeight, maxHeight):
        row_height = self.clbx.GetCharHeight() + 2
        row_count = self.clbx.GetCount()
        prefHeight = min(row_height * row_count + 4, prefHeight)
        return wx.ComboPopup.GetAdjustedSize(self, minWidth, prefHeight, maxHeight)

    def get_flagsenum_items(self) -> t.List["FlagsEnumItem"]:
        # read all flagsenum items and modify checked status
        flagsenum_items: t.List[FlagsEnumItem] = []
        for item in range(self.clbx.GetCount()):
            flagsenum_item: FlagsEnumItem = self.clbx.GetClientData(item)
            flagsenum_item.checked = self.clbx.IsChecked(item)
            flagsenum_items.append(flagsenum_item)
        return flagsenum_items

    def GetStringValue(self):
        flagsenum_items = self.get_flagsenum_items()
        temp_obj = self.entry.conv_flagsenum_items_to_obj(flagsenum_items)
        return self.entry.conv_obj_to_str(temp_obj)


class WxObjEditor_FlagsEnum(wx.ComboCtrl):
    def __init__(self, parent, settings: ObjViewSettings_FlagsEnum):
        self.entry = settings.entry

        super(wx.ComboCtrl, self).__init__(
            parent,
            style=wx.CB_READONLY,
        )

        self.popup_ctrl = FlagsEnumComboPopup(self, self.entry)
        self.SetPopupControl(self.popup_ctrl)

        # Initialize CheckListBox
        items = self.entry.get_flagsenum_items_from_obj()
        for pos, item in enumerate(items):
            self.popup_ctrl.clbx.Insert(
                item=f"{int_to_str(self.entry.model.integer_format, item.value)} ({item.name})",
                pos=pos,
                clientData=item,
            )
            self.popup_ctrl.clbx.Check(pos, item.checked)

        self.SetValue(self.popup_ctrl.GetStringValue())

    def get_new_obj(self) -> t.Any:
        flagsenum_items = self.popup_ctrl.get_flagsenum_items()
        new_obj = self.entry.conv_flagsenum_items_to_obj(flagsenum_items)
        return new_obj


class WxObjEditor_Timestamp(wx.Panel):
    def __init__(self, parent, settings: ObjViewSettings_Timestamp):
        self.entry = settings.entry

        super(wx.Panel, self).__init__(parent)
        self.parent = parent

        # Test if the obj of the entry is available
        if self.entry.obj is None:
            return
        if not isinstance(self.entry.obj, arrow.Arrow):
            return

        # Obj
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        dt = self.entry.obj.datetime
        wx_datetime = wx.DateTime(
            day=dt.day,
            month=dt.month - 1,  # in wx.adc.DatePickerCtrl the month start with 0
            year=dt.year,
            hour=dt.hour,
            minute=dt.minute,
            second=dt.second,
            millisec=dt.microsecond // 1000,
        )

        self.date_picker = wx.adv.DatePickerCtrl(
            self,
            wx.ID_ANY,
            wx_datetime,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY,
        )
        hsizer.Add(self.date_picker, 0, wx.LEFT, 0)

        self.time_picker = wx.adv.TimePickerCtrl(
            self,
            wx.ID_ANY,
            wx_datetime,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.adv.TP_DEFAULT,
        )
        hsizer.Add(self.time_picker, 0, wx.LEFT, 5)

        self.obj_txtctrl = wx.TextCtrl(
            self,
            wx.ID_ANY,
            self.entry.obj_str,
            wx.DefaultPosition,
            wx.DefaultSize,
            style=wx.TE_READONLY,
        )
        hsizer.Add(self.obj_txtctrl, 1, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)

        self.date_picker.Bind(wx.EVT_KILL_FOCUS, self._on_kill_focus)
        self.time_picker.Bind(wx.EVT_KILL_FOCUS, self._on_kill_focus)
        self.obj_txtctrl.Bind(wx.EVT_KILL_FOCUS, self._on_kill_focus)

        self.SetSizer(hsizer)
        self.Layout()

    def get_new_obj(self) -> t.Any:
        date: wx.DateTime = self.date_picker.GetValue()
        time: wx.DateTime = self.time_picker.GetValue()
        new_obj = arrow.Arrow(
            year=date.year,
            month=date.month + 1,  # in wx.adc.DatePickerCtrl the month start with 0
            day=date.day,
            hour=time.hour,
            minute=time.minute,
            second=time.second,
        )
        return new_obj

    def _on_kill_focus(self, event):
        # The kill focus event is not propagated from the childs to the panel. So we have to do it manually.
        # If this is not done, the dvc editor is not closed correctly, when the focus is lost.
        evt_handler: wx.EvtHandler = self.GetEventHandler()
        evt_handler.ProcessEvent(event)


WxObjEditor = t.Union[
    WxObjEditor_Default,
    WxObjEditor_String,
    WxObjEditor_Integer,
    WxObjEditor_Bytes,
    WxObjEditor_Enum,
    WxObjEditor_FlagsEnum,
    WxObjEditor_Timestamp,
]


# #####################################################################################################################
# Value Editor Factory
# #####################################################################################################################
def create_obj_editor(parent, settings: ObjViewSettings) -> WxObjEditor:
    if isinstance(settings, ObjViewSettings_String):
        return WxObjEditor_String(parent, settings)
    elif isinstance(settings, ObjViewSettings_Integer):
        return WxObjEditor_Integer(parent, settings)
    elif isinstance(settings, ObjViewSettings_Bytes):
        return WxObjEditor_Bytes(parent, settings)
    elif isinstance(settings, ObjViewSettings_Enum):
        return WxObjEditor_Enum(parent, settings)
    elif isinstance(settings, ObjViewSettings_FlagsEnum):
        return WxObjEditor_FlagsEnum(parent, settings)
    elif isinstance(settings, ObjViewSettings_Timestamp):
        return WxObjEditor_Timestamp(parent, settings)
    else:
        return WxObjEditor_Default(parent, settings)


# #####################################################################################################################
# Obj Renderer Helper
# #####################################################################################################################
class WxObjRendererHelper_Default:
    def __init__(self, settings: ObjViewSettings):
        self.entry = settings.entry

    def get_size(
        self,
        renderer: "wx_construct_editor.ObjectRenderer",
    ) -> wx.Size:
        # Return the size needed to display the value.  The renderer
        # has a helper function we can use for measuring text that is
        # aware of any custom attributes that may have been set for
        # this item.
        obj_str = self.entry.obj_str if self.entry else ""
        size = renderer.GetTextExtent(obj_str)
        size += (2, 2)
        return size

    def render(
        self,
        renderer: "wx_construct_editor.ObjectRenderer",
        rect: wx.Rect,
        dc: wx.DC,
        state,
    ) -> bool:
        # And then finish up with this helper function that draws the
        # text for us, dealing with alignment, font and color
        # attributes, etc.
        obj_str = self.entry.obj_str if self.entry else ""
        renderer.RenderText(obj_str, 0, rect, dc, state)
        return True

    def get_mode(self):
        return dv.DATAVIEW_CELL_EDITABLE

    def activate_cell(
        self,
        renderer: "wx_construct_editor.ObjectRenderer",
        rect: wx.Rect,
        model: dv.DataViewModel,
        item: dv.DataViewItem,
        col: int,
        mouse_event: t.Optional[wx.MouseEvent],
    ):
        return False


class WxObjRendererHelper_Flag(WxObjRendererHelper_Default):
    def __init__(self, settings: ObjViewSettings_Flag):
        self.entry = settings.entry

    def get_size(
        self,
        renderer: "wx_construct_editor.ObjectRenderer",
    ) -> wx.Size:
        native_renderer: wx.RendererNative = wx.RendererNative.Get()
        win: wx.Window = renderer.GetView()

        size = native_renderer.GetCheckBoxSize(win)
        return size

    def render(
        self,
        renderer: "wx_construct_editor.ObjectRenderer",
        rect: wx.Rect,
        dc: wx.DC,
        state,
    ) -> bool:
        native_renderer: wx.RendererNative = wx.RendererNative.Get()
        win: wx.Window = renderer.GetView()

        flags = 0
        if bool(self.entry.obj) is True:
            flags = wx.CONTROL_CHECKED
        native_renderer.DrawCheckBox(win, dc, rect, flags)
        return True

    def get_mode(self):
        return dv.DATAVIEW_CELL_ACTIVATABLE

    def activate_cell(
        self,
        renderer: "wx_construct_editor.ObjectRenderer",
        rect: wx.Rect,
        model: dv.DataViewModel,
        item: dv.DataViewItem,
        col: int,
        mouse_event: t.Optional[wx.MouseEvent],
    ):
        # see wxWidgets: wxDataViewToggleRenderer::WXActivateCell

        if mouse_event is not None:
            # Only react to clicks directly on the checkbox, not elsewhere in
            # the same cell.
            size = self.get_size(renderer)
            column: dv.DataViewColumn = renderer.GetOwner()

            if column.GetAlignment() == wx.ALIGN_LEFT:
                # i dont know why, but without the offset on windows the
                # clickable area is shifted
                mouse_event.SetX(mouse_event.GetX() - 3)

            if not wx.Rect(size).Contains(mouse_event.GetPosition()):
                return False

        new_value = not bool(self.entry.obj)
        model.ChangeValue(wx_construct_editor.ValueFromEditorCtrl(new_value), item, col)
        return True


WxObjRendererHelper = t.Union[
    WxObjRendererHelper_Default,
    WxObjRendererHelper_Flag,
]


def create_obj_renderer_helper(settings: ObjViewSettings) -> WxObjRendererHelper:
    if isinstance(settings, ObjViewSettings_Flag):
        return WxObjRendererHelper_Flag(settings)
    else:
        return WxObjRendererHelper_Default(settings)
