# -*- coding: utf-8 -*-
import abc
import typing as t


class Command:
    def __init__(self, can_undo: bool, name: str) -> None:
        self.can_undo: bool = can_undo
        self.name: str = name

    @abc.abstractmethod
    def do(self) -> bool:
        ...

    @abc.abstractmethod
    def undo(self) -> bool:
        ...


class CommandProcessor:
    def __init__(self, max_commands: int) -> None:
        self._max_commands = max_commands

        self._history: t.List[Command] = []
        self._current_command_idx: t.Optional[int] = None

    def can_undo(self) -> bool:
        """
        Returns true if the currently-active command can be undone, false
        otherwise.
        """
        current_command = self.get_current_command()
        if current_command is None:
            return False
        else:
            return current_command.can_undo

    def can_redo(self) -> bool:
        """
        Returns true if the currently-active command can be redone, false
        otherwise.
        """
        next_command = self.get_next_command()
        if next_command is None:
            return False
        else:
            return True

    def redo(self) -> None:
        """
        Executes (redoes) the current command (the command that has just been
        undone if any).
        """

    def undo(self) -> None:
        """
        Undoes the last command executed.
        """

    def submit(self, command: Command) -> None:
        """
        Submits a new command to the command processor.

        The command processor calls Command.do to execute the command; if it
        succeeds, the command is stored in the history list, and the associated
        edit menu (if any) updated appropriately. If it fails, the command is
        deleted immediately.
        """
        command.do()
        self.store(command)

    def store(self, command: Command) -> None:
        """
        Just store the command without executing it.
        """
        if self._current_command_idx is None:
            self.clear_commands()

        if len(self._history) >= self._max_commands:
            if self._current_command_idx is None:
                raise ValueError("history and current_command_idx are out of sync")
            self._history.pop(0)
            self._current_command_idx = self._current_command_idx - 1

        self._current_command_idx = len(self._history)
        self._history.append(command)

    def clear_commands(self):
        """
        Deletes all commands in the list and sets the current command pointer to None.
        """
        self._history.clear()
        self._current_command_idx = None

    def get_current_command(self) -> t.Optional[Command]:
        """
        Returns the current command.
        """
        if self._current_command_idx is None:
            return None

        return self._history[self._current_command_idx]

    def get_next_command(self) -> t.Optional[Command]:
        """
        Returns the current command.
        """
        if self._current_command_idx is None:
            return None

        next_command_idx = self._current_command_idx + 1

        if next_command_idx >= len(self._history):
            return None

        return self._history[next_command_idx]
