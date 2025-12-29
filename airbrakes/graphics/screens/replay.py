"""
The main top level screen which displays all the information about the flight.
"""

from typing import TYPE_CHECKING

from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Footer

from airbrakes.graphics.replay_widgets.header import ReplayFlightHeader
from airbrakes.graphics.replay_widgets.panel import FlightInformation

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from airbrakes.context import Context


class ReplayScreen(Screen[None]):
    """
    The main top level screen which displays all the information about the flight.
    """

    CSS_PATH = "../css/replay.tcss"

    __slots__ = ("context", "flight_header", "flight_information")

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def compose(self) -> ComposeResult:
        """
        Create the top level layout of the screen.
        """
        with Grid(id="main-grid"):
            self.flight_header = ReplayFlightHeader(id="flight-header")
            self.flight_information = FlightInformation(id="flight-information-panel")
            yield self.flight_header
            yield self.flight_information
        yield Footer()

    def initialize_widgets(self, context: Context) -> None:
        """
        Supplies the airbrakes context and related objects to the widgets for proper operation.
        """
        self.context = context
        self.flight_header.initialize_widgets(self.context)
        self.flight_information.initialize_widgets(self.context)
        self.watch(self.query_one("#sim-speed-panel"), "sim_speed", self._change_sim_speed)
        self.watch(
            self.query_one("#flight-header"),
            "t_zero_time_ns",
            self._monitor_flight_time,
            init=False,
        )

    def reset_widgets(self) -> None:
        """
        Resets the widgets to their initial state.
        """
        self.flight_header.reset_widgets()
        self.flight_information.reset_widgets()
        self.app.pop_screen()

    def update_telemetry(self) -> None:
        """
        Updates all the reactive variables with the latest telemetry data.
        """
        self.flight_header.update_header()
        self.flight_information.update_flight_information()

    def _change_sim_speed(self, sim_speed: float) -> None:
        self.context.imu._sim_speed_factor = sim_speed

    def _monitor_flight_time(self, flight_time_ns: int) -> None:
        """
        Updates the graphs when the time changes.
        """
        self.flight_information.flight_graph.update_data(flight_time_ns)
