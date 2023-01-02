# -*- coding: utf-8 -*-
import abc
import dataclasses
import typing as t

import construct_editor.core.construct_editor as construct_editor
import construct_editor.core.entries as entries
from construct_editor.core.model import ConstructEditorModel, IntegerFormat

COPY_LABEL = "Copy"
PASTE_LABEL = "Paste"
UNDO_LABEL = "Undo"
REDO_LABEL = "Redo"

INTFORMAT_DEC_LABEL = "Dec"
INTFORMAT_HEX_LABEL = "Hex"

# #####################################################################################################################
# Context Menu ########################################################################################################
# #####################################################################################################################
@dataclasses.dataclass
class SeparatorMenuItem:
    pass


@dataclasses.dataclass
class ButtonMenuItem:
    label: str
    shortcut: t.Optional[str]
    enabled: bool
    callback: t.Callable[[], None]


@dataclasses.dataclass
class CheckboxMenuItem:
    label: str
    shortcut: t.Optional[str]
    enabled: bool
    checked: bool
    callback: t.Callable[[bool], None]


@dataclasses.dataclass
class RadioGroupMenuItems:
    labels: t.List[str]
    checked_label: str
    callback: t.Callable[[str], None]


@dataclasses.dataclass
class SubmenuItem:
    label: str
    subitems: t.List["MenuItem"]


MenuItem = t.Union[
    ButtonMenuItem,
    SeparatorMenuItem,
    CheckboxMenuItem,
    RadioGroupMenuItems,
    SubmenuItem,
]


class ContextMenu:
    def __init__(
        self,
        parent: "construct_editor.ConstructEditor",
        model: "ConstructEditorModel",
        entry: t.Optional["entries.EntryConstruct"],
    ):
        self.parent = parent
        self.model = model
        self.entry = entry

        self._init_default_menu()

    def _init_default_menu(self):
        self._init_copy_paste()
        self.add_menu_item(SeparatorMenuItem())
        self._init_undo_redo()
        self.add_menu_item(SeparatorMenuItem())
        self._init_hide_protected()
        self.add_menu_item(SeparatorMenuItem())
        self._init_intformat()
        if len(self.model.list_viewed_entries) > 0:
            self.add_menu_item(SeparatorMenuItem())
            self._init_list_viewed_entries()

        if self.entry is not None:
            self.entry.modify_context_menu(self)

    def _init_copy_paste(self):
        self.add_menu_item(
            ButtonMenuItem(
                COPY_LABEL,
                "Ctrl+C",
                True,
                self.on_copy_value_to_clipboard,
            )
        )
        self.add_menu_item(
            ButtonMenuItem(
                "Copy path to clipboard",
                "",
                True,
                self.on_copy_path_to_clipboard,
            )
        )
        self.add_menu_item(
            ButtonMenuItem(
                PASTE_LABEL,
                "Ctrl+V",
                False,
                self.on_paste,
            )
        )

    def _init_undo_redo(self):
        self.add_menu_item(
            ButtonMenuItem(
                UNDO_LABEL,
                "Ctrl+Z",
                self.model.command_processor.can_undo(),
                self.on_undo,
            )
        )
        self.add_menu_item(
            ButtonMenuItem(
                REDO_LABEL,
                "Ctrl+Y",
                self.model.command_processor.can_redo(),
                self.on_redo,
            )
        )

    def _init_hide_protected(self):
        self.add_menu_item(
            CheckboxMenuItem(
                "Hide Protected",
                None,
                True,
                self.parent.hide_protected,
                self.on_hide_protected,
            )
        )

    def _init_intformat(self):
        if self.model.integer_format is IntegerFormat.Hex:
            checked_label = INTFORMAT_HEX_LABEL
        else:
            checked_label = INTFORMAT_DEC_LABEL
        self.add_menu_item(
            RadioGroupMenuItems(
                [INTFORMAT_DEC_LABEL, INTFORMAT_HEX_LABEL],
                checked_label,
                self.on_intformat,
            )
        )

    def _init_list_viewed_entries(self):
        submenu = SubmenuItem("List Viewed Items", [])
        for e in self.model.list_viewed_entries:

            def on_remove_list_viewed_item(checked: bool):
                self.parent.disable_list_view(e)

            label = entries.create_path_str(e.path)
            submenu.subitems.append(
                CheckboxMenuItem(
                    label,
                    None,
                    True,
                    True,
                    on_remove_list_viewed_item,
                )
            )
        self.add_menu_item(submenu)

    @abc.abstractmethod
    def add_menu_item(self, item: MenuItem):
        """
        Add an menu item to the context menu.

        This has to be implemented by the derived class.
        """

    def on_copy_value_to_clipboard(self):
        if self.entry is None:
            return
        self.parent.copy_entry_value_to_clipboard(self.entry)

    def on_copy_path_to_clipboard(self):
        if self.entry is None:
            return
        self.parent.copy_entry_path_to_clipboard(self.entry)

    def on_paste(self):
        if self.entry is None:
            return
        self.parent.paste_entry_value_from_clipboard(self.entry)

    def on_undo(self):
        self.model.command_processor.undo()

    def on_redo(self):
        self.model.command_processor.redo()

    def on_hide_protected(self, checked: bool):
        self.parent.change_hide_protected(checked)
        self.parent.reload()

    def on_intformat(self, label: str):
        if label == INTFORMAT_DEC_LABEL:
            self.model.integer_format = IntegerFormat.Dec
        else:
            self.model.integer_format = IntegerFormat.Hex
        self.parent.reload()
