"""Module which contains the 5 panels for the flight display."""

from textual.app import ComposeResult
from textual.widgets import Static

from airbrakes.context import Context
from airbrakes.graphics.flight.graphs import FlightGraph
from airbrakes.graphics.flight.telemetry import FlightTelemetry
from airbrakes.graphics.flight.visualization import Visualization


class FlightInformation(Static):
    """Panel displaying the real-time flight information."""

    context: Context | None = None
    flight_telemetry: FlightTelemetry | None = None
    flight_graph: FlightGraph | None = None
    rocket_visualization: Visualization | None = None

    def compose(self) -> ComposeResult:
        self.flight_telemetry = FlightTelemetry(id="flight-data-panel")
        self.flight_telemetry.border_title = "SIMULATED TELEMETRY"
        yield self.flight_telemetry
        self.flight_graph = FlightGraph(id="flight-graph-panel")
        self.flight_graph.border_title = "FLIGHT GRAPHS"
        yield self.flight_graph
        self.rocket_visualization = Visualization(id="rocket-visualization-panel")
        self.rocket_visualization.border_title = "ROCKET VISUALIZATION"
        yield self.rocket_visualization

    def initialize_widgets(self, context: Context) -> None:
        self.context = context
        self.flight_telemetry.initialize_widgets(self.context)
        self.flight_graph.initialize_widgets(self.context)
        self.rocket_visualization.initialize_widgets(self.context)

    def update_flight_information(self) -> None:
        self.flight_telemetry.update_flight_telemetry()
        self.rocket_visualization.update_visualization()
