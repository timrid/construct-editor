# -*- coding: utf-8 -*-
import abc
import enum
import textwrap
import typing as t

import construct as cs
import wx
import wx.dataview as dv

from construct_editor.core.callbacks import CallbackListNew
from construct_editor.core.commands import Command, CommandProcessor
from construct_editor.core.entries import EntryConstruct, create_entry_from_construct
from construct_editor.core.model import ConstructEditorModel
from construct_editor.core.preprocessor import (
    add_gui_metadata,
    get_gui_metadata,
    include_metadata,
)


class ConstructEditor:
    def __init__(self, construct: cs.Construct, model: ConstructEditorModel):
        self._model = model

        self.change_construct(construct)

        self.on_entry_selected: CallbackListNew[[EntryConstruct]] = CallbackListNew()
        self.on_root_obj_changed: CallbackListNew[[t.Any]] = CallbackListNew()

    @abc.abstractmethod
    def reload(self):
        """
        Reload the ConstructEditor, while remaining expaned elements and selection.

        This has to be implemented by the derived class.
        """

    @abc.abstractmethod
    def show_parse_error_message(self, msg: t.Optional[str]):
        """
        Show an parse error message to the user.

        This has to be implemented by the derived class.
        """

    @abc.abstractmethod
    def show_build_error_message(self, msg: t.Optional[str]):
        """
        Show an build error message to the user.

        This has to be implemented by the derived class.
        """

    @abc.abstractmethod
    def show_status(self, path_info: str, bytes_info: str):
        """
        Show an status to the user.

        This has to be implemented by the derived class.
        """

    def change_construct(self, constr: cs.Construct) -> None:
        """
        Change the construct format, that is used for building/parsing.
        """
        # add root name, is none is available
        if constr.name is None:
            constr = "root" / constr

        # modify the copied construct, so that each item also includes metadata for the GUI
        self._construct = include_metadata(constr)

        # create entry from the construct
        self._model.root_entry = create_entry_from_construct(
            self._model, None, self._construct, None, ""
        )

        self._model.list_viewed_entries.clear()

    def parse(self, binary: bytes, **contextkw: t.Any):
        """
        Parse binary data to struct.
        """
        try:
            self._model.root_obj = self._construct.parse(binary, **contextkw)
            self.show_parse_error_message(None)
        except Exception as e:
            self.show_parse_error_message(
                f"Error while parsing binary data: {type(e).__name__}\n{str(e)}"
            )
            self._model.root_obj = None

        # clear all commands, when new data is set from external
        self._model.command_processor.clear_commands()
        self.reload()

    def build(self, **contextkw: t.Any) -> bytes:
        """
        Build binary data from struct.
        """
        try:
            binary = self._construct.build(self._model.root_obj, **contextkw)
            self.show_build_error_message(None)
        except Exception as e:
            self.show_build_error_message(
                f"Error while building binary data: {type(e).__name__}\n{str(e)}"
            )
            raise e

        # parse the build binary, so that constructs that parses from nothing are shown correctly (eg. cs.Peek)
        wx.CallAfter(lambda: self.parse(binary, **contextkw))

        return binary

    def hide_protected(self, hide_protected: bool) -> None:
        """
        Hide protected members.
        A protected member starts with an undescore (_)
        """
        self._model.hide_protected = hide_protected
        self.reload()

    def is_hide_protected_enabled(self) -> bool:
        """
        Check if "hide_protected" is enabled
        """
        return self._model.hide_protected

    @abc.abstractmethod
    def expand_entry(self, entry: EntryConstruct):
        """
        Expand an entry.

        This has to be implemented by the derived class.
        """

    def expand_children(self, entry: EntryConstruct):
        """
        Expand all children of an entry recursively including the entry itself.
        """
        self.expand_entry(entry)

        subentries = entry.subentries
        if subentries is not None:
            for sub_entry in subentries:
                self.expand_children(sub_entry)

    def expand_all(self):
        """
        Expand all entries.
        """
        if self._model.root_entry is not None:
            self.expand_children(self._model.root_entry)

    def expand_level(self, level: int):
        """
        Expand all Entries to Level ... (0=root level)
        """

        def dvc_expand(entry: EntryConstruct, current_level: int):
            subentries = entry.subentries
            if subentries is None:
                return

            self.expand_entry(entry)

            if current_level < level:
                for sub_entry in subentries:
                    dvc_expand(sub_entry, current_level + 1)

        if self._model.root_entry:
            dvc_expand(self._model.root_entry, 1)

    @abc.abstractmethod
    def collapse_entry(self, entry: EntryConstruct):
        """
        Collapse an entry.

        This has to be implemented by the derived class.
        """

    def collapse_children(self, entry: EntryConstruct):
        """
        Collapse all children of an entry recursively including the entry itself.
        """
        subentries = entry.subentries
        if subentries is not None:
            for sub_entry in subentries:
                self.collapse_children(sub_entry)

        self.collapse_entry(entry)

    def collapse_all(self):
        """
        Collapse all entries.
        """
        if self._model.root_entry:
            self.collapse_children(self._model.root_entry)

    def restore_expansion_from_model(self, entry: EntryConstruct):
        """
        Restore the expansion state from the model recursively.

        While reloading the view in some frameworks (eg. wxPython) the expansion
        state of the entries get lost. Because auf this, the expansion state is
        saved in the model data itself an with this method the expansion state
        of the model can be restored.
        """
        if entry.row_expanded is True:
            self.expand_entry(entry)
        else:
            self.collapse_entry(entry)

        if entry.subentries is None:
            return

        for subentry in entry.subentries:
            self.restore_expansion_from_model(subentry)

    # Internals ###############################################################
    # def _reload_dvc_columns(self):
    #     """Reload the dvc columns"""
    #     self._dvc.ClearColumns()

    #     self._dvc.AppendTextColumn("Name", ConstructEditorColumn.Name, width=160)
    #     self._dvc.AppendTextColumn("Type", ConstructEditorColumn.Type, width=90)
    #     # self._dvc.AppendTextColumn("Value", ConstructEditorColumn.Value, width=200)

    #     renderer = ObjectRenderer()
    #     col = dv.DataViewColumn(
    #         "Value", renderer, ConstructEditorColumn.Value, width=200
    #     )
    #     col.Alignment = wx.ALIGN_LEFT
    #     self._dvc.AppendColumn(col)

    #     list_cols = 0
    #     for list_viewed_entry in self._model.list_viewed_entries:
    #         if list_viewed_entry.subentries is not None:
    #             for subentry in list_viewed_entry.subentries:
    #                 flat_list = []
    #                 subentry.create_flat_subentry_list(flat_list)
    #                 list_cols = max(list_cols, len(flat_list))

    #     for list_col in range(list_cols):
    #         self._dvc.AppendTextColumn(
    #             str(list_col), len(ConstructEditorColumn) + list_col
    #         )

    # def _rename_dvc_columns(self, entry: EntryConstruct):
    #     """Rename the dvc columns"""

    #     flat_list: t.List["EntryConstruct"] = []
    #     if (entry.parent is not None) and (
    #         entry.parent in self._model.list_viewed_entries
    #     ):
    #         entry.create_flat_subentry_list(flat_list)

    #     list_cols = self._dvc.GetColumnCount() - len(ConstructEditorColumn)
    #     for list_col in range(list_cols):
    #         dvc_column: dv.DataViewColumn = self._dvc.GetColumn(
    #             len(ConstructEditorColumn) + list_col
    #         )
    #         if list_col < len(flat_list):
    #             path = flat_list[list_col].path
    #             path = path[len(entry.path) :]  # remove the path from the parent
    #             dvc_column.SetTitle(".".join(path))
    #         else:
    #             dvc_column.SetTitle(str(list_col))

    def _refresh_status_bar(self, entry: t.Optional[EntryConstruct]) -> None:
        if entry is None:
            self.show_status("", "")
            return

        path_info = ".".join(entry.path)
        bytes_info = ""
        stream_infos = entry.get_stream_infos()

        # Show byte range only when no nested streams are used
        if len(stream_infos) == 1:
            byte_range = stream_infos[0].byte_range
            start = byte_range[0]
            end = byte_range[1] - 1
            size = end - start + 1
            if size > 0:
                bytes_info = f"Bytes: {start:n}-{end:n} ({size:n})"
        self.show_status(path_info, bytes_info)
