"""Plain (non-fixture) helper functions for wx integration tests.

These have no fixture dependencies of their own, so they are simple functions
rather than pytest fixtures — callers just import and call them directly.
"""

from __future__ import annotations

import contextlib
import dataclasses
import typing as t

import wx
import wx.grid as Grid

from construct_editor.core.entries import EntryConstruct
from construct_editor.core.model import ConstructEditorColumn
from construct_editor.wx_widgets.wx_construct_editor import (
    WxConstructEditor,
)
from construct_editor.wx_widgets.wx_hex_editor import (
    HexEditorBinaryData,
    HexEditorGrid,
    HexEditorTable,
    WxHexEditor,
)


@dataclasses.dataclass
class WxAppAndUiSim:
    """Bundles the session-scoped wx.App with the shared
    wx.UIActionSimulator, so tests that need either (or both) can depend on
    a single fixture."""

    app: wx.App
    ui_simulator: wx.UIActionSimulator


@dataclasses.dataclass
class WxTestHarness:
    """Bundles the running wx.App with a widget's parent wx.Frame, and a
    wx.UIActionSimulator, for a test.

    Also provides `move_mouse_to`, `click`, `key_press` and `type_text` for
    driving simulated OS-level input via a real wx.MainLoop.
    """

    app: wx.App
    frame: wx.Frame
    ui_simulator: wx.UIActionSimulator

    @classmethod
    @contextlib.contextmanager
    def create(cls, app: wx.App, ui_simulator: wx.UIActionSimulator) -> t.Generator[WxTestHarness, None, None]:
        """Create a fresh top-level frame for a test, wrap it with `app` and
        `ui_simulator`, and tear it down again once the `with` block exits.

        The frame is shown, raised, and focused (instead of hidden) so that
        wx.UIActionSimulator — which drives real OS-level mouse/keyboard
        input — can reliably target it.
        """
        frame = wx.Frame(None)
        frame.Show(True)
        frame.Raise()
        frame.SetFocus()
        app.Yield()
        try:
            yield cls(app=app, frame=frame, ui_simulator=ui_simulator)
        finally:
            frame.Destroy()
            app.ProcessPendingEvents()

    def move_mouse_to(self, point: wx.Point, delay_ms: int = 150) -> None:
        """Move the simulated mouse cursor to an absolute screen point."""
        sim = self.ui_simulator
        self._run_steps([lambda: sim.MouseMove(point.x, point.y)], delay_ms)

    def move_mouse_linear(
        self,
        point: wx.Point,
        duration_ms: int = 150,
        step_delay_ms: int = 10,
    ) -> None:
        """Move the simulated mouse cursor from its current position to
        `point` in a straight line over `duration_ms`, in several
        intermediate steps, instead of jumping there directly.

        The number of steps is derived from `duration_ms` and
        `step_delay_ms` (i.e. how many `step_delay_ms`-sized slices fit into
        `duration_ms`), rather than being specified directly.

        This more closely mimics how a real user moves the mouse, which
        matters for widgets that react to mouse-move events along the way
        (e.g. hover tooltips that should only appear once the cursor has
        settled, or drag handling that tracks intermediate positions).
        """
        sim = self.ui_simulator
        start = wx.GetMousePosition()

        if step_delay_ms <= 0:
            raise ValueError("step_delay_ms must be > 0")
        steps = max(duration_ms // step_delay_ms, 1)

        def _make_step(step_index: int) -> t.Callable[[], t.Any]:
            fraction = step_index / steps
            x = round(start.x + (point.x - start.x) * fraction)
            y = round(start.y + (point.y - start.y) * fraction)
            return lambda: sim.MouseMove(x, y)

        move_steps = [_make_step(step_index) for step_index in range(1, steps + 1)]
        self._run_steps(move_steps, step_delay_ms)

    def click(self, delay_ms: int = 150) -> None:
        """Simulate a left mouse click at the current cursor position."""
        self._run_steps([self.ui_simulator.MouseClick], delay_ms)

    def key_press(
        self,
        keycode: int,
        modifiers: int = wx.MOD_NONE,
        delay_ms: int = 150,
    ) -> None:
        """Simulate a single key press (down + up) of `keycode`, optionally
        with modifier keys (e.g. wx.MOD_SHIFT) held down."""
        sim = self.ui_simulator
        self._run_steps([lambda: sim.Char(keycode, modifiers)], delay_ms)

    def type_text(self, text: str, delay_ms: int = 150) -> None:
        """Simulate typing `text` one character at a time, in a single
        wx.MainLoop run.

        Uppercase letters are typed with the Shift modifier held down;
        everything else (digits, lowercase letters) is typed plain.
        """
        sim = self.ui_simulator
        steps: list[t.Callable[[], t.Any]] = [
            (lambda ch=ch: sim.Char(ord(ch.upper()), wx.MOD_SHIFT if ch.isupper() else wx.MOD_NONE)) for ch in text
        ]
        self._run_steps(steps, delay_ms)

    def _run_steps(
        self,
        steps: t.Sequence[t.Callable[[], t.Any]],
        delay_ms: int,
    ) -> None:
        """Run a sequence of zero-arg callables inside a real wx.MainLoop, one
        after another, spaced apart in time via wx.CallLater.

        wx.UIActionSimulator posts real OS-level input events (SendInput on
        Windows). These are only reliably dispatched to widgets while an
        actual MainLoop is running — manually pumping with
        wx.Yield()/ProcessPendingEvents is not sufficient (verified:
        cell-edit-start events were silently dropped under manual
        Yield-polling, but processed correctly under a real MainLoop).

        Each step typically does one simulated input action (e.g. a mouse
        click or a keystroke); the delay between steps gives wx time to fully
        process the resulting events (focus changes, cell editor creation,
        ...) before the next step runs.
        """
        app = self.app
        pending = list(steps)

        def _run_next_step() -> None:
            if pending:
                step = pending.pop(0)
                step()
                wx.CallLater(delay_ms, _run_next_step)
            else:
                app.ExitMainLoop()

        wx.CallLater(delay_ms, _run_next_step)
        app.MainLoop()

    def wait_ms(self, ms: int) -> None:
        """Run the wx.MainLoop for approximately `ms` milliseconds, then
        return control to the test.

        Unlike wx.Yield()/ProcessPendingEvents(), this reliably lets pending
        wx.CallLater/wx.Timer callbacks (e.g. the ones driving
        WxHoverToolTip's show/hide delays) actually fire, since a real
        MainLoop is running while waiting.
        """
        wx.CallLater(ms, self.app.ExitMainLoop)
        self.app.MainLoop()


def grid_cell_screen_point(grid: Grid.Grid, row: int, col: int) -> wx.Point:
    """Convert a wx.grid.Grid cell to an absolute screen point.

    Used to target wx.UIActionSimulator mouse actions at a specific cell.
    """
    rect = grid.CellToRect(row, col)
    position = rect.GetPosition()
    unscrolled_center = wx.Point(
        position.x + rect.GetWidth() // 2,
        position.y + rect.GetHeight() // 2,
    )
    client_point = grid.CalcScrolledPosition(unscrolled_center)
    return grid.GetGridWindow().ClientToScreen(client_point)


# ---------------------------------------------------------------------------
# Private-member accessors.
#
# Tests intentionally reach into WxHexEditor/HexEditorGrid internals that
# aren't part of the public API, to exercise/assert on internal behavior.
# Rather than sprinkling a `# pyright: ignore[reportPrivateUsage]` (or
# disabling the rule project-wide), every such access is funneled through one
# of these small typed wrapper functions, each carrying exactly one ignore
# comment at its single point of definition. Call sites just call the
# wrapper, so they stay fully type-checked otherwise.
# ---------------------------------------------------------------------------


def editor_grid(editor: WxHexEditor) -> HexEditorGrid:
    """Access WxHexEditor's private `_grid`."""
    return editor._grid  # pyright: ignore[reportPrivateUsage]


def editor_table(editor: WxHexEditor) -> HexEditorTable:
    """Access WxHexEditor's private `_table`."""
    return editor._table  # pyright: ignore[reportPrivateUsage]


def editor_binary_data(editor: WxHexEditor) -> HexEditorBinaryData:
    """Access WxHexEditor's private `_binary_data`."""
    return editor._binary_data  # pyright: ignore[reportPrivateUsage]


def grid_selection(grid: HexEditorGrid) -> t.Tuple[int | None, int | None]:
    """Access HexEditorGrid's private `_selection`."""
    return grid._selection  # pyright: ignore[reportPrivateUsage]


def copy_selection(grid: HexEditorGrid) -> bool:
    """Call HexEditorGrid's private `_copy_selection()`."""
    return grid._copy_selection()  # pyright: ignore[reportPrivateUsage]


def cut_selection(grid: HexEditorGrid) -> bool:
    """Call HexEditorGrid's private `_cut_selection()`."""
    return grid._cut_selection()  # pyright: ignore[reportPrivateUsage]


def remove_selection(grid: HexEditorGrid) -> bool:
    """Call HexEditorGrid's private `_remove_selection()`."""
    return grid._remove_selection()  # pyright: ignore[reportPrivateUsage]


def insert_byte_at_selection(grid: HexEditorGrid) -> bool:
    """Call HexEditorGrid's private `_insert_byte_at_selection()`."""
    return grid._insert_byte_at_selection()  # pyright: ignore[reportPrivateUsage]


def paste_at_selection(grid: HexEditorGrid, overwrite: bool = False, insert: bool = False) -> bool:
    """Call HexEditorGrid's private `_paste(...)`."""
    return grid._paste(overwrite=overwrite, insert=insert)  # pyright: ignore[reportPrivateUsage]


def trigger_cell_right_click(grid: HexEditorGrid, event: Grid.GridEvent) -> None:
    """Call HexEditorGrid's private `_on_cell_right_click(event)`."""
    grid._on_cell_right_click(event)  # pyright: ignore[reportPrivateUsage]


def trigger_select_cell(grid: HexEditorGrid, event: Grid.GridEvent) -> None:
    """Call HexEditorGrid's private `_on_select_cell(event)`."""
    grid._on_select_cell(event)  # pyright: ignore[reportPrivateUsage]


def trigger_range_selecting_keyboard(grid: HexEditorGrid, row_diff: int = 0, col_diff: int = 0) -> None:
    """Call HexEditorGrid's private `_on_range_selecting_keyboard(...)`."""
    grid._on_range_selecting_keyboard(  # pyright: ignore[reportPrivateUsage]
        row_diff=row_diff, col_diff=col_diff
    )


def construct_editor_cell_screen_rect(editor: WxConstructEditor, entry: EntryConstruct, column: ConstructEditorColumn) -> wx.Rect:
    """Compute the on-screen rect of `entry`'s cell in `column`.

    Uses the exact same coordinate-space conversion as
    WxConstructEditor._on_dvc_motion (via `self._dvc`, not
    `self._dvc_main_window` - a previously fixed bug double-counted the
    dvc header offset when the wrong window was used for this conversion,
    shifting the tooltip down by roughly one row).
    """
    dvc = editor._dvc  # pyright: ignore[reportPrivateUsage]
    model = editor._model  # pyright: ignore[reportPrivateUsage]
    item = model.entry_to_dvc_item(entry)
    col = dvc.GetColumn(column)
    cell_rect: wx.Rect = dvc.GetItemRect(item, col)
    return wx.Rect(dvc.ClientToScreen(cell_rect.GetPosition()), cell_rect.GetSize())
