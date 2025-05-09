"""
Module which has the benchmark screen for the flight display.
"""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from airbrakes.context import Context


class BenchmarkScreen(ModalScreen[None]):
    """
    Screen which displays the benchmark results.
    """

    CSS_PATH = "../css/benchmark.tcss"

    __slots__ = ("context", "flight_name")

    def initialize_widgets(self, context: Context, flight_name: Path) -> None:
        self.context = context
        self.flight_name = flight_name

    def update_stats(self, profiled_time: float) -> None:
        """
        Update the stats of the screen.

        Args:
            profiled_time (float): The profiled time of the flight.
        """
        self.query_one("#flight-name-widget").update(
            f"Running [$secondary]{self.flight_name!s}[/] took [$success]{profiled_time}[/] seconds"
        )
        self.query_one("#benchmark-results-widget").update(
            "Benchmark results:\n"
            f"[$secondary]Current state:[/] [$success]{self.context.state.name}[/]\n"
            f"[$secondary]Max Altitude:[/] "
            f"[$success]{self.context.data_processor.max_altitude}[/] m\n"
            f"[$secondary]Max Velocity:[/] "
            f"[$success]{self.context.data_processor.max_vertical_velocity}[/] m/s\n"
        )
        self.query_one("#back-to-main-screen-button").disabled = False
        self.query_one("#exit-button").disabled = False

    def compose(self) -> ComposeResult:
        """
        Called when the screen is mounted.

        Mounts the widgets to the screen.
        """
        with Vertical(id="vertical-container"):
            # Add the flight name
            yield Static(
                id="flight-name-widget",
            )
            # Add the benchmark results
            yield Static(
                "Benchmark results:\n",
                id="benchmark-results-widget",
            )

            with Horizontal(id="button-container"):
                # Add the button to go back to the main screen
                yield Button(
                    "Back to Main Screen",
                    id="back-to-main-screen-button",
                    variant="primary",
                    disabled=True,
                )
                # Add the Button to exit the application
                yield Button("Exit", id="exit-button", variant="error", disabled=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Called when a button is pressed.

        Handles the button presses.
        """
        if event.button.id == "back-to-main-screen-button":
            self.app.pop_screen()
        elif event.button.id == "exit-button":
            self.app.exit()
