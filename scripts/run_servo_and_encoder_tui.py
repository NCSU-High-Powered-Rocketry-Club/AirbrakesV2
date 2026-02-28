"""
Servo & Encoder TUI — Enhanced
================================
Run from the project root:
    uv run scripts/run_servo_and_encoder_tui.py          # real hardware
    uv run scripts/run_servo_and_encoder_tui.py -s       # mock / simulation
"""

from __future__ import annotations

import argparse
import re
import threading
import time
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.events import Resize
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Digits,
    Footer,
    Header,
    Label,
    Static,
)
from textual_plot import HiResMode, PlotWidget

from airbrakes.constants import (
    ENCODER_PIN_A,
    ENCODER_PIN_B,
    SERVO_CHANNEL,
    SERVO_MAX_ANGLE_DEGREES,
    ServoExtension,
)
from airbrakes.mock.mock_servo import MockServo

if TYPE_CHECKING:
    from airbrakes.base_classes.base_servo import BaseServo

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONSTANTS_FILE = Path("airbrakes/constants.py")

# Current sensor polling — 0.5 ms to capture transients
CURRENT_POLL_INTERVAL_S = 0.0005

# Rolling buffer: keep last 5 seconds of current data
CURRENT_HISTORY_SECONDS = 5.0

# How often the TUI refreshes each section
GRAPH_REFRESH_INTERVAL_S = 0.5
CURRENT_DISPLAY_REFRESH_S = 0.1

# How often we read servo.current_extension to keep Digits in sync
SERVO_STATE_REFRESH_S = 0.2

# Degrees nudged per arrow-key press in tuning mode
ANGLE_STEP = 0.5

# Terminal width threshold below which buttons stack vertically
NARROW_WIDTH_THRESHOLD = 64


# ---------------------------------------------------------------------------
# Helper — patch a constant value inside constants.py on disk
# ---------------------------------------------------------------------------

def _patch_constant_in_file(file_path: Path, attr_name: str, new_value: int | float) -> None:
    """Rewrite the numeric value of *attr_name* inside the ServoExtension enum in *file_path*."""
    text = file_path.read_text()
    # Matches lines like:    MIN_EXTENSION = 25
    pattern = rf"^(\s+{re.escape(attr_name)}\s*=\s*)\S+"
    replacement = rf"\g<1>{new_value}"
    new_text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
    if new_text == text:
        raise ValueError(f"Could not find '{attr_name}' in {file_path}")
    file_path.write_text(new_text)


# ---------------------------------------------------------------------------
# Current-sensor background thread
# ---------------------------------------------------------------------------

class CurrentMonitor:
    """Polls the current sensor at ~0.5 ms and maintains a rolling 5-second buffer."""

    def __init__(self, servo: "BaseServo", window: float = CURRENT_HISTORY_SECONDS) -> None:
        self._servo = servo
        self._window = window
        self._lock = threading.Lock()
        # Each entry: (monotonic timestamp, milliamps)
        self._buf: deque[tuple[float, float]] = deque()
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="current-monitor"
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            now = time.monotonic()
            mA = self._servo.get_system_current_milliamps()
            cutoff = now - self._window
            with self._lock:
                self._buf.append((now, mA))
                while self._buf and self._buf[0][0] < cutoff:
                    self._buf.popleft()
            self._stop.wait(CURRENT_POLL_INTERVAL_S)

    def latest_ma(self) -> float:
        with self._lock:
            return self._buf[-1][1] if self._buf else 0.0

    def history(self) -> tuple[list[float], list[float]]:
        """Return *(times_relative_to_now, milliamps)* for the rolling buffer.

        Times are expressed as negative offsets from *now* so the x-axis
        always scrolls: the rightmost point is 0 (= now) and the leftmost
        approaches -CURRENT_HISTORY_SECONDS.
        """
        now = time.monotonic()
        with self._lock:
            if not self._buf:
                return [-CURRENT_HISTORY_SECONDS, 0.0], [0.0, 0.0]
            ts = [e[0] - now for e in self._buf]
            ms = [e[1] for e in self._buf]
        return ts, ms


# ---------------------------------------------------------------------------
# Custom widgets
# ---------------------------------------------------------------------------

class AngleDisplay(Digits):
    """Large digit readout that shows the current servo angle."""

    angle: reactive[float] = reactive(0.0)

    def watch_angle(self, value: float) -> None:
        self.update(f"{value:5.1f}°")


class EncoderBox(Static):
    """Shows the raw encoder step count, centered."""

    steps: reactive[int] = reactive(0)

    def render(self) -> str:
        return f"{self.steps:+d}"


class CurrentBox(Static):
    """Shows the live current draw in amps, centered and
 color-coded."""

    ma: reactive[float] = reactive(0.0)

    def render(self) -> str:
        amps = self.ma / 1000.0
        if self.ma < 1000:
            color = "green"
        elif self.ma < 2000:
            color = "yellow"
        else:
            color = "red"
        return f"[{color}]{amps:.4f} A[/{color}]"


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------

class ServoControllerApp(App[None]):
    """Servo & Encoder TUI — Normal and Tuning modes, vertical-first layout."""

    CSS_PATH = "servo_tui.tcss"

    BINDINGS = [
        Binding("up",   "angle_up",   "Extend / +0.5°", show=True,  priority=True),
        Binding("down", "angle_down", "Retract / −0.5°", show=True, priority=True),
        Binding("t",    "toggle_tuning", "Toggle Tuning", show=True),
    ]

    # ── Reactive state ───────────────────────────────────────────────────
    tuning_mode: reactive[bool] = reactive(False)
    # current_angle is a *display* value kept in sync with servo.current_extension
    current_angle: reactive[float] = reactive(float(ServoExtension.MIN_NO_BUZZ.value))

    # ── Init ─────────────────────────────────────────────────────────────
    def __init__(self, mock_servo: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        if mock_servo:
            self.servo: BaseServo = MockServo(SERVO_CHANNEL, ENCODER_PIN_A, ENCODER_PIN_B)
        else:
            from airbrakes.hardware.servo import Servo
            self.servo = Servo(SERVO_CHANNEL, ENCODER_PIN_A, ENCODER_PIN_B)

        self.encoder = self.servo.encoder
        self._current_monitor = CurrentMonitor(self.servo)

        # In tuning mode the user drives the angle manually via arrow keys;
        # we track it separately and only sync from the servo in normal mode.
        self._tuning_angle: float = float(ServoExtension.MIN_NO_BUZZ.value)

    # ── Compose ──────────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)

        with VerticalScroll(id="scroll-root"):

            # ── Top info row: [Encoder] [Digits] [Current] ────────────
            with Horizontal(id="info-row"):
                with Container(id="encoder-box"):
                    eb = EncoderBox(id="encoder-widget")
                    eb.border_title = "Encoder"
                    yield eb

                yield AngleDisplay(id="angle-display")

                with Container(id="current-box"):
                    cb = CurrentBox(id="current-widget")
                    cb.border_title = "Current (A)"
                    yield cb

            # ── Mode indicator ────────────────────────────────────────
            yield Static("", id="mode-indicator")

            # ── Normal mode panel ─────────────────────────────────────
            with Vertical(id="normal-panel"):
                # control-row and precise-row each swap between Horizontal
                # and Vertical at runtime depending on terminal width.
                with Horizontal(id="control-row"):
                    yield Button("⬆ Extend",  id="extend-btn",  variant="success")
                    yield Button("⬇ Retract", id="retract-btn", variant="error")

                with Horizontal(id="precise-row"):
                    yield Button(
                        f"MIN  ({ServoExtension.MIN_EXTENSION.value}°)",
                        id="min-btn",
                        variant="primary",
                    )
                    yield Button(
                        f"MIN No Buzz  ({ServoExtension.MIN_NO_BUZZ.value}°)",
                        id="min-no-buzz-btn",
                        variant="primary",
                    )
                    yield Button(
                        f"MAX  ({ServoExtension.MAX_EXTENSION.value}°)",
                        id="max-btn",
                        variant="warning",
                    )
                    yield Button(
                        f"MAX No Buzz  ({ServoExtension.MAX_NO_BUZZ.value}°)",
                        id="max-no-buzz-btn",
                        variant="warning",
                    )

            # ── Tuning mode panel (hidden by default) ─────────────────
            with Vertical(id="tuning-panel", classes="hidden"):
                yield Static(
                    "↑ / ↓  adjust angle  •  click a button to save that constant",
                    id="tuning-hint",
                )
                with Horizontal(id="tuning-buttons"):
                    yield Button(
                        f"Set MIN_EXTENSION\n({ServoExtension.MIN_EXTENSION.value}°)",
                        id="set-min-btn",
                        variant="primary",
                    )
                    yield Button(
                        f"Set MIN_NO_BUZZ\n({ServoExtension.MIN_NO_BUZZ.value}°)",
                        id="set-min-no-buzz-btn",
                        variant="primary",
                    )
                    yield Button(
                        f"Set MAX_EXTENSION\n({ServoExtension.MAX_EXTENSION.value}°)",
                        id="set-max-btn",
                        variant="warning",
                    )
                    yield Button(
                        f"Set MAX_NO_BUZZ\n({ServoExtension.MAX_NO_BUZZ.value}°)",
                        id="set-max-no-buzz-btn",
                        variant="warning",
                    )

            # ── Current graph ─────────────────────────────────────────
            with Vertical(id="graph-container"):
                yield Static("⚡ Current Draw — last 5 s", id="graph-title")
                yield PlotWidget(id="current-plot", allow_pan_and_zoom=False)

        yield Footer()

    # ── Lifecycle ────────────────────────────────────────────────────────
    def on_mount(self) -> None:
        self.encoder.when_rotated = self._on_encoder_rotated
        self._current_monitor.start()

        # Sync display with whatever the servo starts at
        self._sync_angle_from_servo()

        self.set_interval(SERVO_STATE_REFRESH_S,   self._sync_angle_from_servo)
        self.set_interval(CURRENT_DISPLAY_REFRESH_S, self._refresh_current)
        self.set_interval(GRAPH_REFRESH_INTERVAL_S,  self._refresh_graph)

        self._update_mode_indicator()

    def on_unmount(self) -> None:
        self._current_monitor.stop()

    # ── Resize — reflow buttons to avoid squishing ───────────────────────
    def on_resize(self, event: Resize) -> None:
        narrow = event.size.width < NARROW_WIDTH_THRESHOLD
        self._reflow_row("control-row",  narrow, vertical_cls="control-col")
        self._reflow_row("precise-row",  narrow, vertical_cls="precise-col")
        self._reflow_row("tuning-buttons", narrow, vertical_cls="tuning-col")

    def _reflow_row(self, row_id: str, go_vertical: bool, vertical_cls: str) -> None:
        """Toggle between horizontal and vertical layout for a button row."""
        try:
            row = self.query_one(f"#{row_id}")
        except Exception:
            return
        if go_vertical:
            row.add_class(vertical_cls)
        else:
            row.remove_class(vertical_cls)

    # ── Reactive watchers ────────────────────────────────────────────────
    def watch_current_angle(self, value: float) -> None:
        try:
            self.query_one("#angle-display", AngleDisplay).angle = value
        except Exception:
            pass  # DOM not yet ready on first reactive init

    def watch_tuning_mode(self, is_tuning: bool) -> None:
        try:
            self.query_one("#normal-panel").set_class(is_tuning,  "hidden")
            self.query_one("#tuning-panel").set_class(not is_tuning, "hidden")
        except Exception:
            return
        self._update_mode_indicator()
        if is_tuning:
            # Seed tuning angle from whatever the servo is currently at
            self._tuning_angle = float(self.servo.current_extension.value)
            self.current_angle = self._tuning_angle

    # ── Key actions ──────────────────────────────────────────────────────
    def action_toggle_tuning(self) -> None:
        self.tuning_mode = not self.tuning_mode

    def action_angle_up(self) -> None:
        if self.tuning_mode:
            self._nudge_angle(ANGLE_STEP)
        else:
            self.servo.set_extended()
            # Don't touch current_angle here — _sync_angle_from_servo will
            # pick it up: first MAX_EXTENSION, then MAX_NO_BUZZ after the timer.

    def action_angle_down(self) -> None:
        if self.tuning_mode:
            self._nudge_angle(-ANGLE_STEP)
        else:
            self.servo.set_retracted()
            # Same: let _sync_angle_from_servo track the transition.

    # ── Event handlers ───────────────────────────────────────────────────
    @on(Button.Pressed)
    def _on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            # Normal mode — let the servo handle the state machine;
            # _sync_angle_from_servo will keep the Digits up to date.
            case "extend-btn":
                self.servo.set_extended()
            case "retract-btn":
                self.servo.set_retracted()
            case "min-btn":
                self.servo._set_extension(ServoExtension.MIN_EXTENSION)
            case "min-no-buzz-btn":
                self.servo._set_extension(ServoExtension.MIN_NO_BUZZ)
            case "max-btn":
                self.servo._set_extension(ServoExtension.MAX_EXTENSION)
            case "max-no-buzz-btn":
                self.servo._set_extension(ServoExtension.MAX_NO_BUZZ)
            # Tuning mode — save current tuning angle as a named constant
            case "set-min-btn":
                self._save_constant("MIN_EXTENSION", self._tuning_angle)
            case "set-min-no-buzz-btn":
                self._save_constant("MIN_NO_BUZZ", self._tuning_angle)
            case "set-max-btn":
                self._save_constant("MAX_EXTENSION", self._tuning_angle)
            case "set-max-no-buzz-btn":
                self._save_constant("MAX_NO_BUZZ", self._tuning_angle)

    # ── Internal helpers ─────────────────────────────────────────────────
    def _sync_angle_from_servo(self) -> None:
        """Read servo.current_extension and update the Digits widget.

        Called on a fast timer so the UI automatically reflects the deferred
        _NO_BUZZ transition that BaseServo fires ~1 s after set_extended /
        set_retracted.  In tuning mode the display is driven by the arrow
        keys instead, so we skip the sync.
        """
        if self.tuning_mode:
            return
        angle = float(self.servo.current_extension.value)
        # Only trigger a reactive update (and thus a redraw) when the value
        # actually changes, to avoid unnecessary work.
        if angle != self.current_angle:
            self.current_angle = angle

    def _nudge_angle(self, delta: float) -> None:
        """Move the servo by *delta* degrees (tuning mode only)."""
        new_angle = max(0.0, min(float(SERVO_MAX_ANGLE_DEGREES), self._tuning_angle + delta))
        self._tuning_angle = new_angle
        self.current_angle = new_angle
        self._apply_angle(new_angle)

    def _apply_angle(self, angle: float) -> None:
        """Send an arbitrary angle to the servo hardware (tuning mode)."""
        from airbrakes.base_classes.base_servo import BaseServo as _BS
        self.servo.servo.change_duty_cycle(_BS._angle_to_duty_cycle(angle))

    def _update_mode_indicator(self) -> None:
        try:
            indicator = self.query_one("#mode-indicator", Static)
        except Exception:
            return
        if self.tuning_mode:
            indicator.update("[bold yellow]⚙  TUNING MODE[/bold yellow]  — press [b]T[/b] to return to Normal")
        else:
            indicator.update("[bold green]●  NORMAL MODE[/bold green]  — press [b]T[/b] to enter Tuning")

    def _save_constant(self, attr_name: str, value: float) -> None:
        """Persist *value* into ServoExtension both live (in-process) and on disk."""
        int_value = round(value)

        # Dynamic: mutate the live enum member in-place
        try:
            member = ServoExtension[attr_name]
            old_value = member._value_
            ServoExtension._value2member_map_.pop(old_value, None)
            member._value_ = int_value
            ServoExtension._value2member_map_[int_value] = member
        except (KeyError, AttributeError):
            pass

        # Also sync via the airbrakes.constants module reference
        try:
            import airbrakes.constants as _c
            m = _c.ServoExtension[attr_name]
            _c.ServoExtension._value2member_map_.pop(m._value_, None)
            m._value_ = int_value
            _c.ServoExtension._value2member_map_[int_value] = m
        except Exception:
            pass

        # Static: rewrite the source file so the value survives a restart
        try:
            _patch_constant_in_file(CONSTANTS_FILE, attr_name, int_value)
            self.notify(
                f"{attr_name} = {int_value}°  →  saved to {CONSTANTS_FILE}",
                title="✅ Constant saved",
                severity="information",
            )
        except Exception as exc:
            self.notify(
                f"Couldn't write {CONSTANTS_FILE}: {exc}",
                title="⚠️ File write error",
                severity="warning",
            )

        self._refresh_tuning_labels()

    def _refresh_tuning_labels(self) -> None:
        """Update tuning button labels to match the current enum values."""
        pairs = [
            ("set-min-btn",         "MIN_EXTENSION"),
            ("set-min-no-buzz-btn", "MIN_NO_BUZZ"),
            ("set-max-btn",         "MAX_EXTENSION"),
            ("set-max-no-buzz-btn", "MAX_NO_BUZZ"),
        ]
        for btn_id, attr in pairs:
            try:
                val = ServoExtension[attr].value
                self.query_one(f"#{btn_id}", Button).label = f"Set {attr}\n({val}°)"
            except Exception:
                pass

    # ── Encoder callback (called from gpiozero's background thread) ───────
    def _on_encoder_rotated(self) -> None:
        steps = self.encoder.steps
        self.call_from_thread(self._update_encoder_display, steps)

    def _update_encoder_display(self, steps: int) -> None:
        try:
            self.query_one("#encoder-widget", EncoderBox).steps = steps
        except Exception:
            pass

    # ── Periodic refresh callbacks ────────────────────────────────────────
    def _refresh_current(self) -> None:
        try:
            mA = self._current_monitor.latest_ma()
            self.query_one("#current-widget", CurrentBox).ma = mA
        except Exception:
            pass

    def _refresh_graph(self) -> None:
        try:
            plot = self.query_one("#current-plot", PlotWidget)
        except Exception:
            return
        if not plot.is_attached:
            return

        times, milliamps = self._current_monitor.history()
        amps = [v / 1000.0 for v in milliamps]

        try:
            plot.clear()
        except Exception:
            return

        plot.xlabel = "t (s)"
        plot.ylabel = "A"
        # Pin the x-axis so it always spans the full rolling window;
        # this makes the graph scroll rather than stretch as data fills up.
        # plot.set_xlimits(-CURRENT_HISTORY_SECONDS, 0.0)
        # Pin the y-axis to a sensible range so the flat-zero mock line
        # doesn't cause the autoscaler to collapse the axis to a dot.
        # all_zero = all(v == 0.0 for v in amps)
        # if all_zero:
        #     plot.set_ylimits(0.0, 1.0)
        # else:
        #     plot.set_ylimits(None, None)  # autoscale when real data arrives
        plot.plot(times, amps, line_style="cyan", hires_mode=HiResMode.BRAILLE)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Servo & Encoder TUI")
    parser.add_argument(
        "--mock-servo", "-s",
        action="store_true",
        help="Use a mock servo (no real hardware required)",
    )
    args = parser.parse_args()
    app = ServoControllerApp(mock_servo=args.mock_servo)
    app.run()
