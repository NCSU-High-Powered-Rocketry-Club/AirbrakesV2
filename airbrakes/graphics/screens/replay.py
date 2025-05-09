"""
The main top level screen which displays all the information about the flight.
"""

from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Footer

from airbrakes.context import Context
from airbrakes.graphics.flight.header import FlightHeader
from airbrakes.graphics.flight.panel import FlightInformation
from airbrakes.graphics.flight.telemetry import CPUUsage


class ReplayScreen(Screen[None]):
    """
    The main top level screen which displays all the information about the flight.
    """

    CSS_PATH = "../css/replay.tcss"

    __slots__ = ("context", "flight_header", "flight_information")

    def start(self) -> None:
        """
        Responsible for starting the CPU usage monitor.
        """
        self.query_one(CPUUsage).start()

    def stop(self) -> None:
        """
        Responsible for stopping the CPU usage monitor.
        """
        self.query_one(CPUUsage).stop()

    def compose(self) -> ComposeResult:
        """
        Create the top level layout of the screen.
        """
        with Grid(id="main-grid"):
            self.flight_header = FlightHeader(id="flight-header")
            self.flight_information = FlightInformation(id="flight-information-panel")
            yield self.flight_header
            yield self.flight_information
        yield Footer()

    def initialize_widgets(self, context: Context, is_mock: bool) -> None:
        """
        Supplies the airbrakes context and related objects to the widgets for proper operation.
        """
        self.context = context
        self.flight_header.initialize_widgets(self.context, is_mock)
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
        self.context.imu._sim_speed_factor.value = sim_speed

    def _monitor_flight_time(self, flight_time_ns: int) -> None:
        """
        Updates the graphs when the time changes.
        """
        self.flight_information.flight_graph.update_data(flight_time_ns)
