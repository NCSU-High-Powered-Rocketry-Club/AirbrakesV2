"""Module which contains the 5 panels for the flight display."""

from textual.app import ComposeResult
from textual.widgets import Placeholder, Static

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.graphics.flight.telemetry import DebugTelemetry, FlightTelemetry


class FlightInformation(Static):
    """Panel displaying the real-time flight information."""

    airbrakes: AirbrakesContext | None = None

    def compose(self) -> ComposeResult:
        self.flight_telemetry = FlightTelemetry(id="flight_data_panel")
        self.flight_telemetry.border_title = "SIMULATED TELEMETRY"
        yield self.flight_telemetry
        yield Placeholder("tabbed graphs")
        yield Placeholder("2d rocket vis")
        self.debug_telemetry = DebugTelemetry(id="debug-flight-data-panel")
        yield self.debug_telemetry
        yield Placeholder("downrange map")
        yield Placeholder("2d rocket vis")

    def initialize_widgets(self, airbrakes: AirbrakesContext) -> None:
        self.airbrakes = airbrakes
        self.flight_telemetry.initialize_widgets(self.airbrakes)
        self.debug_telemetry.initialize_widgets(self.airbrakes)

    def update_flight_information(self) -> None:
        self.flight_telemetry.update_flight_telemetry()
        self.debug_telemetry.update_debug_telemetry()
