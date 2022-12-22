# -*- coding: utf-8 -*-
import abc
import typing as t

import construct as cs
import wx

from construct_editor.core.callbacks import CallbackList
from construct_editor.core.entries import EntryConstruct, create_entry_from_construct
from construct_editor.core.model import ConstructEditorModel
from construct_editor.core.preprocessor import include_metadata


class ConstructEditor:
    def __init__(self, construct: cs.Construct, model: ConstructEditorModel):
        self._model = model

        self.change_construct(construct)

        self.on_entry_selected: CallbackList[[EntryConstruct]] = CallbackList()
        self.on_root_obj_changed: CallbackList[[t.Any]] = CallbackList()

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

    @abc.abstractmethod
    def get_selected_entry(self) -> EntryConstruct:
        """
        Get the currently selected entry (or None if nothing is selected).
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

    def enable_list_view(self, entry: EntryConstruct):
        """
        Enable the list view for an entry.
        """
        if self.is_list_view_enabled(entry):
            return

        self._model.list_viewed_entries.append(entry)
        self.reload()

        # collapse all subentries without the entry itself,
        # so that the list can be seen better.
        self.collapse_children(entry)
        self.expand_entry(entry)

    def disable_list_view(self, entry: EntryConstruct):
        """
        Disable the list view for an entry.
        """
        if not self.is_list_view_enabled(entry):
            return

        self._model.list_viewed_entries.remove(entry)
        self.reload()

    def is_list_view_enabled(self, entry: EntryConstruct) -> bool:
        """
        Check if an entry is shown in a list view.
        """
        if entry in self._model.list_viewed_entries:
            return True
        return False

    def _get_list_viewed_column_count(self):
        """
        Get the count of all list viewed columns.
        """
        column_count = 0
        for list_viewed_entry in self._model.list_viewed_entries:
            if list_viewed_entry.subentries is None:
                continue
            for subentry in list_viewed_entry.subentries:
                flat_list = self._model.create_flat_subentry_list(subentry)
                column_count = max(column_count, len(flat_list))
        return column_count

    def _get_list_viewed_column_names(
        self, selected_entry: EntryConstruct
    ) -> t.List[str]:
        """
        Get the names of all list viewed columns.

        The selected entry is used to get the column names. If there are more
        columns than subentries in the selected entry or no selected entry is
        passed, the column number is used as label.
        """
        column_names: t.List[str] = []
        flat_list = self._model.create_flat_subentry_list(selected_entry)
        for entry in flat_list:
            column_name = entry.path
            column_name = column_name[
                len(selected_entry.path) :
            ]  # remove the path from the selected_entry
            column_names.append(".".join(column_name))
        return column_names

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
