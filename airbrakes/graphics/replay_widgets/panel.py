"""
Module which contains the 5 panels for the flight display.
"""

from textual.app import ComposeResult
from textual.widgets import Static

from airbrakes.context import Context
from airbrakes.graphics.replay_widgets.graphs import FlightGraph
from airbrakes.graphics.replay_widgets.telemetry import ReplayFlightTelemetry
from airbrakes.graphics.replay_widgets.visualization import Visualization


class FlightInformation(Static):
    """
    Panel displaying the real-time flight information.
    """

    __slots__ = ("context", "flight_graph", "flight_telemetry", "rocket_visualization")

    def compose(self) -> ComposeResult:
        self.flight_telemetry: ReplayFlightTelemetry = ReplayFlightTelemetry(id="flight-data-panel")
        self.flight_telemetry.border_title = "SIMULATED TELEMETRY"
        yield self.flight_telemetry
        self.flight_graph: FlightGraph = FlightGraph(id="flight-graph-panel")
        self.flight_graph.border_title = "FLIGHT GRAPHS"
        yield self.flight_graph
        self.rocket_visualization: Visualization = Visualization(id="rocket-visualization-panel")
        self.rocket_visualization.border_title = "ROCKET VISUALIZATION"
        yield self.rocket_visualization

    def initialize_widgets(self, context: Context) -> None:
        self.context: Context = context
        self.flight_telemetry.initialize_widgets(self.context)
        self.flight_graph.initialize_widgets(self.context)
        self.rocket_visualization.initialize_widgets(self.context)

    def reset_widgets(self) -> None:
        """
        Reset the widgets to their initial state.
        """
        self.flight_telemetry.reset_widgets()

    def update_flight_information(self) -> None:
        self.flight_telemetry.update_telemetry()
        self.rocket_visualization.update_visualization()
