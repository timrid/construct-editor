"""Tests for construct_editor.core.context_menu — menu item data types and ContextMenu.

ContextMenu is abstract; these tests cover the pure-data menu item dataclasses
and the logic of the concrete init helpers without requiring a wx runtime.
"""

from construct_editor.core.context_menu import (
    ButtonMenuItem,
    CheckboxMenuItem,
    RadioGroupMenuItems,
    SeparatorMenuItem,
    SubmenuItem,
)


def test_separator_menu_item_instantiation() -> None:
    item = SeparatorMenuItem()
    assert item is not None


def test_button_menu_item_fields() -> None:
    callback_called: list[bool] = []
    item = ButtonMenuItem(
        label="Copy",
        shortcut="Ctrl+C",
        enabled=True,
        callback=lambda: callback_called.append(True),
    )
    assert item.label == "Copy"
    item.callback()
    assert callback_called == [True]


def test_checkbox_menu_item_checked_state() -> None:
    item = CheckboxMenuItem(
        label="Show protected",
        shortcut=None,
        enabled=True,
        checked=True,
        callback=lambda v: None,
    )
    assert item.label == "Show protected"
    assert item.checked is True


def test_checkbox_menu_item_unchecked_state() -> None:
    item = CheckboxMenuItem(
        label="Show protected",
        shortcut=None,
        enabled=True,
        checked=False,
        callback=lambda v: None,
    )
    assert item.checked is False


def test_radio_group_menu_items_fields() -> None:
    item = RadioGroupMenuItems(
        labels=["Dec", "Hex"],
        checked_label="Dec",
        callback=lambda label: None,
    )
    assert item.labels == ["Dec", "Hex"]
    assert item.checked_label == "Dec"


def test_submenu_item_fields() -> None:
    item = SubmenuItem(label="Integer format", subitems=[SeparatorMenuItem()])
    assert item.label == "Integer format"
    assert len(item.subitems) == 1


# TODO: Add tests for ContextMenu._init_copy_paste, _init_undo_redo etc. once
#       a concrete non-wx stub of ContextMenu is available.
