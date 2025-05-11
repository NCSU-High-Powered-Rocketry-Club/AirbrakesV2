"""
Real-time flight data display screen.

Super light weight for use in real-time flight.
"""

from textual.app import ComposeResult
from textual.screen import Screen

from airbrakes.constants import REAL_TIME_DISPLAY_UPDATE_RATE
from airbrakes.context import Context
from airbrakes.graphics.screens.launcher import RealLaunchOptions


class RealFlightScreen(Screen[None]):
    """
    Real-time flight data display screen.
    """

    CSS_PATH = "../css/real.tcss"

    __slots__ = ("context", "launch_options")

    def compose(self) -> ComposeResult:
        """
        Compose the screen with the widgets to display flight data.
        """

    def start(self) -> None:
        """
        Start updating the screen by setting a timer.
        """
        self.set_interval(REAL_TIME_DISPLAY_UPDATE_RATE, self.update_telemetry)

    def update_telemetry(self) -> None:
        """
        Update the telemetry data on the screen.
        """

    def initialize_widgets(self, context: Context, launch_options: RealLaunchOptions) -> None:
        """
        Initialize the widgets with the flight data from the context.
        """
        self.context = context
        self.launch_options = launch_options
