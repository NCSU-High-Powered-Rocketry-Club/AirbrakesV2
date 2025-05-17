"""
UI Header for when you are running a real flight.
"""

import time

from textual.app import ComposeResult
from textual.containers import Center, Grid
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Label, Static
from textual_pyfiglet import FigletWidget

from airbrakes.constants import TARGET_APOGEE_METERS
from airbrakes.context import Context
from airbrakes.graphics.custom_widgets import TimeDisplay
from airbrakes.graphics.screens.launcher import RealLaunchOptions
from airbrakes.graphics.utils import set_only_class


class MotorBurnSignal(Message):
    """
    Message to signal the start of motor burn, so the display can stop.
    """


class RealFlightHeader(Static):
    """
    Header panel for a real flight.

    Minimalistic and simple.
    """

    state: reactive[str] = reactive("STANDBY", init=False)
    time_elapsed: reactive[int] = reactive(0, init=False)

    __slots__ = (
        "context",
        "elapsed_time_label",
        "flight_start_time_ns",
        "launch_status_label",
        "servo_status_label",
        "state_label",
    )

    def compose(self) -> ComposeResult:
        """
        Compose the header panel.
        """
        with Grid(id="real-header-grid"):
            # Column 1:
            # Row 1 & 2 - State:
            with Center(id="state-center-container"):
                self.state_label = FigletWidget(
                    "STANDBY",
                    id="real-state-label",
                    font="future",
                    justify="center",
                    color1=self.app.theme_variables["primary"],
                )
                yield self.state_label

            # Column 2:
            # Row 1 - Elapsed Time since script start:
            self.elapsed_time_label = Label("Elapsed Time: 00:00:01", id="elapsed-time-label")
            yield self.elapsed_time_label

            # Column 3
            # Row 1 - Servo status:
            self.servo_status_label = Label("Servo: [$success]ARMED[/]", id="servo-status-label")
            yield self.servo_status_label

            # Column 2:
            # Row 2 - Launch Status:
            with Center(id="launch-status-center-container"):
                self.launch_status_label = FigletWidget(
                    "GO FOR LAUNCH",
                    id="launch-status-label",
                    font="smblock",
                    justify="center",
                    color1=self.app.theme_variables["primary"],
                )
                yield self.launch_status_label

            # Column 3:
            # Row 2 - Target Apogee label:
            yield Static(
                f"Target Apogee: [$secondary]{TARGET_APOGEE_METERS}[/] m",
                id="real-target-apogee-label",
            )

    def watch_time_elapsed(self) -> None:
        """
        Watch the time elapsed since the script started.
        """
        self.elapsed_time_label.update(
            f"Elapsed Time: {TimeDisplay.format_ns_to_min_s_ms(self.time_elapsed)}"
        )

    def watch_state(self) -> None:
        """
        Watch the state of the flight.

        If we hit motor burn, we should stop the display.
        """
        self.state_label.update(self.state)
        # TODO: Check if we are in motor burn and stop the display.
        if self.state == "MotorBurn":
            self.launched()
            self.post_message(MotorBurnSignal())

    def go_for_launch(self) -> None:
        """
        Update the launch status to "GO FOR LAUNCH".
        """
        self.launch_status_label.update("GO FOR LAUNCH")
        set_only_class(self.launch_status_label, None)
        self.refresh_pyfiglet_colors()

    def launch_hold(self) -> None:
        """
        Update the launch status to "HOLD".
        """
        self.launch_status_label.update("HOLD")
        set_only_class(self.launch_status_label, "hold")
        self.refresh_pyfiglet_colors()

    def launched(self) -> None:
        """
        Update the launch status to "LAUNCHED".
        """
        self.launch_status_label.update("LAUNCHED")
        set_only_class(self.launch_status_label, "launched")
        self.refresh_pyfiglet_colors()

    def refresh_pyfiglet_colors(self) -> None:
        """
        Refresh the colors of the Figlet widgets.

        Can be called when the theme changes.
        """
        self.state_label.color1 = self.app.theme_variables["text-primary"]
        match list(self.launch_status_label.classes):
            case ["hold"]:
                self.launch_status_label.color1 = self.app.theme_variables["text-error"]
            case ["launched"]:
                self.launch_status_label.color1 = self.app.theme_variables["text-success"]
            case _:
                # Default to primary if no class is set
                self.launch_status_label.color1 = self.app.theme_variables["text-accent"]

    def initialize_widgets(self, context: Context, launch_options: RealLaunchOptions) -> None:
        self.context = context
        self.state = self.context.state.name.removesuffix("State")
        self.flight_start_time_ns = time.monotonic_ns()

        if launch_options.mock_servo:
            self.servo_status_label.update("Servo: [$text-warning]DISARMED[/]")

    def update_header(self) -> None:
        """
        Update the header with the latest telemetry data.
        """
        self.state = self.context.state.name.removesuffix("State")
        self.time_elapsed = time.monotonic_ns() - self.flight_start_time_ns
