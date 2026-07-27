"""Tests for construct_editor.core.commands — Command / CommandProcessor."""


from construct_editor.core.commands import Command, CommandProcessor

# ---------------------------------------------------------------------------
# Minimal concrete Command for testing
# ---------------------------------------------------------------------------


class _IncrementCommand(Command):
    """Increments/decrements a shared counter."""

    def __init__(self, counter: list[int], amount: int = 1) -> None:
        super().__init__(can_undo=True, name="Increment")
        self._counter = counter
        self._amount = amount

    def do(self) -> bool:
        self._counter[0] += self._amount
        return True

    def undo(self) -> bool:
        self._counter[0] -= self._amount
        return True


# ---------------------------------------------------------------------------
# CommandProcessor tests
# ---------------------------------------------------------------------------


def _make_processor() -> CommandProcessor:
    return CommandProcessor(max_commands=100)


def test_submit_executes_command() -> None:
    """submit() must call do() on the command."""
    counter = [0]
    proc = _make_processor()
    proc.submit(_IncrementCommand(counter))
    assert counter[0] == 1


def test_can_undo_after_submit() -> None:
    """can_undo() returns True after at least one command has been submitted."""
    proc = _make_processor()
    assert not proc.can_undo()
    proc.submit(_IncrementCommand([0]))
    assert proc.can_undo()


def test_can_redo_after_undo() -> None:
    """can_redo() returns True after an undo operation."""
    proc = _make_processor()
    proc.submit(_IncrementCommand([0]))
    assert not proc.can_redo()
    proc.undo()
    assert proc.can_redo()


def test_undo_reverses_command() -> None:
    """undo() must call the command's undo() method, restoring the previous state."""
    counter = [0]
    proc = _make_processor()
    proc.submit(_IncrementCommand(counter))
    proc.undo()
    assert counter[0] == 0


def test_redo_re_executes_command() -> None:
    """redo() must re-apply the previously undone command."""
    counter = [0]
    proc = _make_processor()
    proc.submit(_IncrementCommand(counter))
    proc.undo()
    proc.redo()
    assert counter[0] == 1


def test_submit_after_undo_clears_redo_history() -> None:
    """Submitting a new command after undo must discard the redo stack."""
    counter = [0]
    proc = _make_processor()
    proc.submit(_IncrementCommand(counter))
    proc.undo()
    proc.submit(_IncrementCommand(counter, amount=5))
    assert not proc.can_redo()


def test_clear_commands_resets_state() -> None:
    """clear_commands() empties the history so undo/redo are no longer possible."""
    proc = _make_processor()
    proc.submit(_IncrementCommand([0]))
    proc.clear_commands()
    assert not proc.can_undo()
    assert not proc.can_redo()


def test_multiple_undo_redo_cycle() -> None:
    """Multiple submit/undo/redo operations must stay consistent."""
    counter = [0]
    proc = _make_processor()
    proc.submit(_IncrementCommand(counter, 1))
    proc.submit(_IncrementCommand(counter, 2))
    assert counter[0] == 3

    proc.undo()
    assert counter[0] == 1

    proc.undo()
    assert counter[0] == 0

    proc.redo()
    assert counter[0] == 1

    proc.redo()
    assert counter[0] == 3
