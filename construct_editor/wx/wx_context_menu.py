# -*- coding: utf-8 -*-
import typing as t

import wx

import construct_editor.core.construct_editor as construct_editor
import construct_editor.core.entries as entries
from construct_editor.core.context_menu import (
    COPY_LABEL,
    PASTE_LABEL,
    REDO_LABEL,
    UNDO_LABEL,
    ButtonMenuItem,
    CheckboxMenuItem,
    ContextMenu,
    MenuItem,
    RadioGroupMenuItems,
    SeparatorMenuItem,
    SubmenuItem,
)
from construct_editor.core.model import ConstructEditorModel

LABEL_TO_ID_MAPPING = {
    COPY_LABEL: wx.ID_COPY,
    PASTE_LABEL: wx.ID_PASTE,
    UNDO_LABEL: wx.ID_UNDO,
    REDO_LABEL: wx.ID_REDO,
}


class WxContextMenu(wx.Menu, ContextMenu):
    def __init__(
        self,
        parent: "construct_editor.ConstructEditor",
        model: "ConstructEditorModel",
        entry: t.Optional["entries.EntryConstruct"],
    ):
        wx.Menu.__init__(self)
        ContextMenu.__init__(self, parent, model, entry)

    def add_menu_item(self, item: MenuItem):
        """
        Add an menu item to the context menu.
        """
        self._add_menu_item(self, item)

    @classmethod
    def _add_menu_item(cls, menu: wx.Menu, item: MenuItem):
        if isinstance(item, SeparatorMenuItem):
            cls._add_separator_item(menu, item)
        elif isinstance(item, ButtonMenuItem):
            cls._add_button_item(menu, item)
        elif isinstance(item, CheckboxMenuItem):
            cls._add_checkbox_item(menu, item)
        elif isinstance(item, RadioGroupMenuItems):
            cls._add_radio_group_item(menu, item)
        elif isinstance(item, SubmenuItem):
            cls._add_submenu_item(menu, item)
        else:
            raise ValueError(f"menu item unsupported ({item})")

    @classmethod
    def _add_separator_item(cls, menu: wx.Menu, item: SeparatorMenuItem):
        menu.AppendSeparator()

    @classmethod
    def _add_button_item(cls, menu: wx.Menu, item: ButtonMenuItem):
        item_id = LABEL_TO_ID_MAPPING.get(item.label, wx.ID_ANY)
        label = item.label
        if item.shortcut is not None:
            label += "\t" + item.shortcut

        def button_event(event: wx.CommandEvent):
            item.callback()

        mi: wx.MenuItem = menu.Append(item_id, label)
        menu.Bind(wx.EVT_MENU, button_event, id=mi.Id)
        mi.Enable(item.enabled)

    @classmethod
    def _add_checkbox_item(cls, menu: wx.Menu, item: CheckboxMenuItem):
        label = item.label
        if item.shortcut is not None:
            label += "\t" + item.shortcut

        def checkbox_event(event: wx.CommandEvent):
            item.callback(event.IsChecked())

        mi: wx.MenuItem = menu.AppendCheckItem(wx.ID_ANY, label)
        menu.Bind(wx.EVT_MENU, checkbox_event, id=mi.Id)
        mi.Check(item.checked)
        mi.Enable(item.enabled)

    @classmethod
    def _add_radio_group_item(cls, menu: wx.Menu, item: RadioGroupMenuItems):
        def radio_group_event(event: wx.CommandEvent):
            item.callback(menu.GetLabel(event.GetId()))

        for label in item.labels:
            mi: wx.MenuItem = menu.AppendRadioItem(wx.ID_ANY, label)
            menu.Bind(wx.EVT_MENU, radio_group_event, id=mi.Id)
            if label == item.checked_label:
                mi.Check(True)

    @classmethod
    def _add_submenu_item(cls, menu: wx.Menu, item: SubmenuItem):
        submenu = wx.Menu()
        for subitem in item.subitems:
            cls._add_menu_item(submenu, subitem)
        menu.AppendSubMenu(submenu, item.label)
