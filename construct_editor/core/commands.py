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

    def redo(self) -> bool:
        """
        Executes (redoes) the current command (the command that has just been
        undone if any).
        """
        next_command = self.get_next_command()

        # no command to redo in the history
        if next_command is None:
            return False

        if next_command.do() is False:
            return False

        self._increment_current_command()

        return True

    def undo(self) -> bool:
        """
        Undoes the last command executed.
        """
        current_command = self.get_current_command()

        # no command available
        if current_command is None:
            return False

        # command cant be undone
        if not current_command.can_undo:
            return False

        # error on undo
        if current_command.undo() is False:
            return False

        # set current command to previous command
        self._decrement_current_command()

        return True

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

        Any command that has been undone will be chopped off the history list.
        """
        # We must chop off the current 'branch', so that
        # we're at the end of the command list.
        if self._current_command_idx is None:
            self.clear_commands()
        else:
            self._history = self._history[: self._current_command_idx + 1]

        # Limit history length. Remove fist commands from history
        # if an overflow occures
        if len(self._history) >= self._max_commands:
            if self._current_command_idx is None:
                raise ValueError("history and current_command_idx are out of sync")
            self._history.pop(0)
            self._current_command_idx = self._current_command_idx - 1

        # append command to history
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
        Returns the next command.
        """
        if self._current_command_idx is None:
            next_command_idx = 0
        else:
            next_command_idx = self._current_command_idx + 1

        if next_command_idx >= len(self._history):
            return None

        return self._history[next_command_idx]

    def _decrement_current_command(self) -> None:
        if self._current_command_idx is None:
            return
        if self._current_command_idx > 0:
            self._current_command_idx -= 1
        else:
            self._current_command_idx = None

    def _increment_current_command(self) -> None:
        if self._current_command_idx is None:
            next_command_idx = 0
        else:
            next_command_idx = self._current_command_idx + 1

        if next_command_idx >= len(self._history):
            return

        self._current_command_idx = next_command_idx
