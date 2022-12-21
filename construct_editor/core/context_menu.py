# -*- coding: utf-8 -*-
import typing as t

import wx

import construct_editor.core.construct_editor as construct_editor
import construct_editor.core.entries as entries
from construct_editor.core.model import ConstructEditorModel, IntegerFormat


# #####################################################################################################################
# Context Menu ########################################################################################################
# #####################################################################################################################
class ContextMenu(wx.Menu):
    def __init__(
        self,
        parent: "construct_editor.ConstructEditor",
        model: "ConstructEditorModel",
        entry: t.Optional["entries.EntryConstruct"],
    ):
        super(ContextMenu, self).__init__()
        self.parent = parent
        self.model = model

        item: wx.MenuItem = self.Append(wx.ID_COPY, "Copy\tCtrl+C")
        # self.Bind(wx.EVT_MENU, self.on_copy, id=item.Id)
        item.Enable(False)

        item: wx.MenuItem = self.Append(wx.ID_PASTE, "Paste\tCtrl+V")
        # self.Bind(wx.EVT_MENU, self.on_paste, id=item.Id)
        item.Enable(False)  # TODO:

        self.AppendSeparator()

        item: wx.MenuItem = self.Append(wx.ID_UNDO, "Undo\tCtrl+Z")
        self.Bind(
            wx.EVT_MENU,
            lambda event: self.model.command_processor.undo(),
            id=item.Id,
        )
        item.Enable(self.model.command_processor.can_undo())

        item: wx.MenuItem = self.Append(wx.ID_REDO, "Redo\tCtrl+Y")
        self.Bind(
            wx.EVT_MENU,
            lambda event: self.model.command_processor.redo(),
            id=item.Id,
        )
        item.Enable(self.model.command_processor.can_redo())

        self.AppendSeparator()

        item: wx.MenuItem = self.AppendCheckItem(wx.ID_ANY, "Hide Protected")
        self.Bind(wx.EVT_MENU, self.on_hide_protected, id=item.Id)
        item.Check(self.parent.is_hide_protected_enabled())
        self.hide_protected_mi = item

        self.AppendSeparator()

        item: wx.MenuItem = self.AppendRadioItem(wx.ID_ANY, "Dec")
        self.Bind(wx.EVT_MENU, self.on_intformat_dec, id=item.Id)
        self.intformat_dec_mi = item

        item: wx.MenuItem = self.AppendRadioItem(wx.ID_ANY, "Hex")
        self.Bind(wx.EVT_MENU, self.on_intformat_hex, id=item.Id)
        self.intformat_hex_mi = item

        if self.model.integer_format is IntegerFormat.Hex:
            self.intformat_hex_mi.Check(True)
        else:
            self.intformat_dec_mi.Check(True)

        # Add List with all currently shown list viewed items
        if len(model.list_viewed_entries) > 0:
            self.AppendSeparator()

            submenu = wx.Menu()
            self.submenu_map: t.Dict[t.Any, "entries.EntryConstruct"] = {}
            for e in model.list_viewed_entries:
                name = ".".join(e.path)
                item: wx.MenuItem = submenu.AppendCheckItem(wx.ID_ANY, name)
                self.submenu_map[item.GetId()] = e
                self.Bind(wx.EVT_MENU, self.on_remove_list_viewed_item, item)
                item.Check(True)

            self.AppendSubMenu(submenu, "List Viewed Items")

        # Add additional items for this entry
        if entry is not None:
            entry.modify_context_menu(self)

    def on_hide_protected(self, event):
        checked = self.hide_protected_mi.IsChecked()
        self.parent.hide_protected = checked
        self.parent.reload()

    def on_intformat_dec(self, event: wx.CommandEvent):
        self.intformat_dec_mi.Check(True)
        self.model.integer_format = IntegerFormat.Dec
        self.parent.reload()
        event.Skip()

    def on_intformat_hex(self, event: wx.CommandEvent):
        self.intformat_hex_mi.Check(True)
        self.model.integer_format = IntegerFormat.Hex
        self.parent.reload()
        event.Skip()

    def on_remove_list_viewed_item(self, event: wx.CommandEvent):
        entry = self.submenu_map[event.GetId()]
        self.model.list_viewed_entries.remove(entry)
        self.parent.reload()
