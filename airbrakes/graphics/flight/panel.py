"""Module which contains the 5 panels for the flight display."""

from textual.app import ComposeResult
from textual.widgets import Placeholder, Static

from airbrakes.context import AirbrakesContext
from airbrakes.graphics.flight.graphs import FlightGraph
from airbrakes.graphics.flight.telemetry import FlightTelemetry


class FlightInformation(Static):
    """Panel displaying the real-time flight information."""

    context: AirbrakesContext | None = None
    flight_telemetry: FlightTelemetry | None = None
    flight_graph: FlightGraph | None = None

    def compose(self) -> ComposeResult:
        self.flight_telemetry = FlightTelemetry(id="flight-data-panel")
        self.flight_telemetry.border_title = "SIMULATED TELEMETRY"
        yield self.flight_telemetry
        self.flight_graph = FlightGraph(id="flight-graph-panel")
        yield self.flight_graph
        yield Placeholder("2d rocket vis")
        yield Placeholder("downrange map")
        yield Placeholder("2d rocket vis")

    def initialize_widgets(self, context: AirbrakesContext) -> None:
        self.context = context
        self.flight_telemetry.initialize_widgets(self.context)
        self.flight_graph.initialize_widgets(self.context)

    def update_flight_information(self) -> None:
        self.flight_telemetry.update_flight_telemetry()
