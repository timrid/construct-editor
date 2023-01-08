# -*- coding: utf-8 -*-
import abc
import typing as t

import construct as cs

import construct_editor.core.entries as entries
from construct_editor.core.callbacks import CallbackList
from construct_editor.core.model import ConstructEditorColumn, ConstructEditorModel
from construct_editor.core.preprocessor import include_metadata


class ConstructEditor:
    def __init__(self, construct: cs.Construct, model: ConstructEditorModel):
        self._model = model

        self.change_construct(construct)

        self.on_entry_selected: CallbackList[
            ["entries.EntryConstruct"]
        ] = CallbackList()
        self.on_root_obj_changed: CallbackList[[t.Any]] = CallbackList()

    @abc.abstractmethod
    def reload(self):
        """
        Reload the ConstructEditor, while remaining expaned elements and selection.

        This has to be implemented by the derived class.
        """

    @abc.abstractmethod
    def show_parse_error_message(self, msg: t.Optional[str], ex: t.Optional[Exception]):
        """
        Show an parse error message to the user.

        This has to be implemented by the derived class.
        """

    @abc.abstractmethod
    def show_build_error_message(self, msg: t.Optional[str], ex: t.Optional[Exception]):
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
    def get_selected_entry(self) -> "entries.EntryConstruct":
        """
        Get the currently selected entry (or None if nothing is selected).

        This has to be implemented by the derived class.
        """

    @abc.abstractmethod
    def select_entry(self, entry: "entries.EntryConstruct") -> None:
        """
        Select an entry programmatically.

        This has to be implemented by the derived class.
        """

    @abc.abstractmethod
    def _put_to_clipboard(self, txt: str):
        """
        Put text to the clipboard.

        This has to be implemented by the derived class.
        """

    @abc.abstractmethod
    def _get_from_clipboard(self):
        """
        Get text from the clipboard.

        This has to be implemented by the derived class.
        """

    def copy_entry_value_to_clipboard(self, entry: "entries.EntryConstruct"):
        """
        Copy the value of the entry to the clipboard.
        """
        copy_txt = entry.obj_str
        self._put_to_clipboard(copy_txt)

    def copy_entry_path_to_clipboard(self, entry: "entries.EntryConstruct"):
        """
        Copy the path of the entry to the clipboard.
        """
        copy_txt = entries.create_path_str(entry.path)
        self._put_to_clipboard(copy_txt)

    def paste_entry_value_from_clipboard(self, entry: "entries.EntryConstruct"):
        """
        Paste the value of the entry from the clipboard.
        """
        txt = self._get_from_clipboard()
        if txt is None:
            return

        # TODO: This does not work correctly, because the clipboard only saves
        # strings. So here is a string to entry.obj conversation needed, which is
        # not so easy.
        # self.model.set_value(txt, entry, ConstructEditorColumn.Value)
        # self.on_root_obj_changed.fire(self.root_obj)

    def change_construct(self, constr: cs.Construct) -> None:
        """
        Change the construct format, that is used for building/parsing.
        """
        # reset error messages
        self.show_build_error_message(None, None)
        self.show_parse_error_message(None, None)

        # add root name, is none is available
        if constr.name is None:
            constr = "root" / constr

        # modify the copied construct, so that each item also includes metadata for the GUI
        self._construct = include_metadata(constr)

        # create entry from the construct
        self._model.root_entry = entries.create_entry_from_construct(
            self._model, None, self._construct, None, ""
        )

        self._model.list_viewed_entries.clear()

    def change_hide_protected(self, hide_protected: bool) -> None:
        """
        Show/hide protected entries.
        A protected member starts with an undescore (_)
        """
        self._model.hide_protected = hide_protected
        self.reload()

    def parse(self, binary: bytes, **contextkw: t.Any):
        """
        Parse binary data to struct.
        """
        try:
            self._model.root_obj = self._construct.parse(binary, **contextkw)
            self.show_parse_error_message(None, None)
        except Exception as e:
            self.show_parse_error_message(
                f"Error while parsing binary data: {type(e).__name__}\n{str(e)}", e
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
            self.show_build_error_message(None, None)
        except Exception as e:
            self.show_build_error_message(
                f"Error while building binary data: {type(e).__name__}\n{str(e)}", e
            )
            raise e

        # Parse the build binary, so that constructs that parses from nothing
        # are shown correctly (eg. cs.Peek, cs.Pointer).
        self.parse(binary, **contextkw)

        return binary

    @abc.abstractmethod
    def expand_entry(self, entry: "entries.EntryConstruct"):
        """
        Expand an entry.

        This has to be implemented by the derived class.
        """

    def expand_children(self, entry: "entries.EntryConstruct"):
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

        def dvc_expand(entry: "entries.EntryConstruct", current_level: int):
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
    def collapse_entry(self, entry: "entries.EntryConstruct"):
        """
        Collapse an entry.

        This has to be implemented by the derived class.
        """

    def collapse_children(self, entry: "entries.EntryConstruct"):
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

    def restore_expansion_from_model(self, entry: "entries.EntryConstruct"):
        """
        Restore the expansion state from the model recursively.

        While reloading the view in some frameworks (eg. wxPython) the expansion
        state of the entries get lost. Because auf this, the expansion state is
        saved in the model data itself an with this method the expansion state
        of the model can be restored.
        """
        visible_entry = entry.get_visible_row_entry()
        if visible_entry is None:
            return

        if visible_entry.row_expanded is True:
            self.expand_entry(visible_entry)
        else:
            self.collapse_entry(visible_entry)

        subentries = self._model.get_children(entry)
        if len(subentries) == 0:
            return

        for subentry in subentries:
            self.restore_expansion_from_model(subentry)

    def enable_list_view(self, entry: "entries.EntryConstruct"):
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

    def disable_list_view(self, entry: "entries.EntryConstruct"):
        """
        Disable the list view for an entry.
        """
        if not self.is_list_view_enabled(entry):
            return

        self._model.list_viewed_entries.remove(entry)
        self.reload()

    def is_list_view_enabled(self, entry: "entries.EntryConstruct") -> bool:
        """
        Check if an entry is shown in a list view.
        """
        if entry in self._model.list_viewed_entries:
            return True
        return False

    @property
    def construct(self) -> cs.Construct:
        """
        Construct that is used for displaying.
        """
        return self._construct

    @construct.setter
    def construct(self, constr: cs.Construct):
        self.change_construct(constr)

    @property
    def hide_protected(self) -> bool:
        """
        Hide protected members.
        A protected member starts with an undescore (_)
        """
        return self._model.hide_protected

    @hide_protected.setter
    def hide_protected(self, hide_protected: bool):
        self.change_hide_protected(hide_protected)

    @property
    def root_obj(self) -> t.Any:
        """
        Root object that is displayed
        """
        return self._model.root_obj

    @property
    def model(self) -> ConstructEditorModel:
        """
        Model with the displayed data.
        """
        return self._model

    # Internals ###############################################################
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
        self, selected_entry: "entries.EntryConstruct"
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
            column_path = entry.path
            column_path = column_path[
                len(selected_entry.path) :
            ]  # remove the path from the selected_entry
            column_names.append(entries.create_path_str(column_path))
        return column_names

    def _refresh_status_bar(self, entry: t.Optional["entries.EntryConstruct"]) -> None:
        if entry is None:
            self.show_status("", "")
            return

        path_info = entries.create_path_str(entry.path)
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
