"""Module to show the terminal GUI for the airbrakes system."""

from typing import ClassVar

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Label, Static


class FlightDisplay(App):
    """A terminal based GUI for displaying real-time flight data."""

    BINDINGS: ClassVar = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        """Create the layout of the app."""
        yield Header()
        yield Horizontal(Vertical(FlightDataPanel(id="flight_data_panel")), id="main")
        yield Footer()


class FlightDataPanel(Static):
    """Panel displaying real-time flight information."""

    time_display = reactive("00:00")
    state = reactive("Standby")
    current_velocity = reactive("0.0 m/s")
    max_velocity = reactive("0.0 m/s")
    current_height = reactive("0.0 m")
    max_height = reactive("0.0 m")
    apogee_prediction = reactive("0.0 m")
    imu_queue_size = reactive("0")
    cpu_usage = reactive("")

    def compose(self) -> ComposeResult:
        yield Label("Flight Data", id="title")
        yield Label("T+: " + self.time_display, id="time_display")
        yield Label("State: " + self.state, id="state")
        yield Label("Current Velocity: " + self.current_velocity, id="current_velocity")
        yield Label("Max Velocity: " + self.max_velocity, id="max_velocity")
        yield Label("Current Height: " + self.current_height, id="current_height")
        yield Label("Max Height: " + self.max_height, id="max_height")
        yield Label("Predicted Apogee: " + self.apogee_prediction, id="apogee_prediction")
        yield Label("IMU Queue Size: " + self.imu_queue_size, id="imu_queue_size")
        yield Label("CPU Usage: " + self.cpu_usage, id="cpu_usage")


if __name__ == "__main__":
    app = FlightDisplay()
    app.run()
