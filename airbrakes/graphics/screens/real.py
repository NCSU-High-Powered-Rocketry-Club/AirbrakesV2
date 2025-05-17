"""
Real-time flight data display screen.

Super light weight for use in real-time flight.
"""

from typing import ClassVar

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Button, Footer

from airbrakes.constants import REAL_TIME_DISPLAY_UPDATE_RATE
from airbrakes.context import Context
from airbrakes.graphics.real_widgets.header import MotorBurnSignal, RealFlightHeader
from airbrakes.graphics.real_widgets.telemetry import (
    BadDataSignal,
    GoodDataSignal,
    RealFlightTelemetry,
)
from airbrakes.graphics.screens.launcher import RealLaunchOptions


class RealFlightScreen(Screen[None]):
    """
    Real-time flight data display screen.
    """

    CSS_PATH = "../css/real.tcss"

    __slots__ = ("bell_timer", "context", "flight_header", "flight_telemetry", "launch_options")

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("l", "toggle_light", "Toggle light mode"),
        Binding("e", "extend_airbrakes", "Extend airbrakes", show=False),
        Binding("r", "retract_airbrakes", "Retract airbrakes", show=False),
    ]

    def compose(self) -> ComposeResult:
        """
        Compose the screen with the widgets to display flight data.
        """
        with Grid(id="real-main-grid"):
            # Column 1:
            self.flight_header = RealFlightHeader(id="real-flight-header")
            yield self.flight_header

            # Column 2:
            self.flight_telemetry = RealFlightTelemetry(id="real-flight-telemetry-panel")
            self.flight_telemetry.border_title = "REAL-TIME TELEMETRY"
            yield self.flight_telemetry

            # Column 3:
            # TODO: Graphs

        yield Footer()

    def start(self) -> None:
        """
        Start updating the screen by setting a timer.
        """
        self.update_timer = self.set_interval(REAL_TIME_DISPLAY_UPDATE_RATE, self.update_telemetry)
        if self.launch_options.verbose:
            self.flight_telemetry.debug_telemetry.start()

    def stop(self) -> None:
        """
        Stop updating the screen by stopping the timer.
        """
        self.flight_telemetry.debug_telemetry.stop()
        self.bell_timer.stop()
        self.update_timer.stop()
        # self.dismiss()

    def update_telemetry(self) -> None:
        """
        Update the telemetry data on the screen.
        """
        self.flight_header.update_header()
        self.flight_telemetry.update_telemetry()

    def initialize_widgets(self, context: Context, launch_options: RealLaunchOptions) -> None:
        """
        Initialize the widgets with the flight data from the context.
        """
        self.context = context
        self.launch_options = launch_options
        self.flight_header.initialize_widgets(context, launch_options)
        self.flight_telemetry.initialize_widgets(context, launch_options)
        self.bell_timer = self.set_interval(0.5, self.app.bell, pause=True)

    @on(BadDataSignal)
    def handle_bad_data(self) -> None:
        """
        Handle the bad data signal by updating the flight header.
        """
        self.flight_header.launch_hold()
        self.bell_timer.resume()

    @on(GoodDataSignal)
    def handle_good_data(self) -> None:
        """
        Handle the good data signal by updating the flight header.
        """
        self.flight_header.go_for_launch()
        self.bell_timer.stop()
        self.bell_timer = self.set_interval(0.5, self.app.bell, pause=True)

    @on(MotorBurnSignal)
    def handle_motor_burn(self) -> None:
        """
        Handle the motor burn signal by updating the flight header.
        """
        self.stop()

    def action_toggle_light(self) -> None:
        """
        Toggle the light mode of the screen, upon keyboard shortcut.
        """
        if self.app.theme == "textual-light":
            self.app.theme = "catppuccin-mocha"
        else:
            self.app.theme = "textual-light"

        # Unfortunately, we need to set the color of the FigletWidget manually (it doesn't support
        # CSS updates).
        # The call_after_refresh is important otherwise it would use the previous theme's colors.
        self.call_after_refresh(self.flight_header.refresh_pyfiglet_colors)

    def action_extend_airbrakes(self) -> None:
        """
        Extend the airbrakes, upon keyboard shortcut.
        """
        self.query_one("#extend-airbrakes-button", Button).press()

    def action_retract_airbrakes(self) -> None:
        """
        Retract the airbrakes, upon keyboard shortcut.
        """
        self.query_one("#retract-airbrakes-button", Button).press()
