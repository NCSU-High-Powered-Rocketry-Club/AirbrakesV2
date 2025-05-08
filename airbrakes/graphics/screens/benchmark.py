"""
Module which has the benchmark screen for the flight display.
"""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from airbrakes.context import Context


class BenchmarkScreen(ModalScreen):
    """
    Screen which displays the benchmark results.
    """

    CSS_PATH = "../css/benchmark.tcss"

    def __init__(self, context: Context, profiled_time: float, flight_name: Path) -> None:
        super().__init__()
        self.context = context
        self.profiled_time = profiled_time
        self.flight_name = flight_name

    def compose(self) -> ComposeResult:
        """
        Called when the screen is mounted.

        Mounts the widgets to the screen.
        """
        with Vertical(id="vertical-container"):
            # Add the flight name
            yield Static(
                f"Running [$secondary]{self.flight_name!s}[/] took "
                f"[$success]{self.profiled_time}[/] seconds",
                id="flight-name-widget",
            )
            # Add the benchmark results
            yield Static(
                "Benchmark results:\n"
                f"[$secondary]Current state:[/] [$success]{self.context.state.name}[/]\n"
                f"[$secondary]Max Altitude:[/] "
                f"[$success]{self.context.data_processor.max_altitude}[/] m\n"
                f"[$secondary]Max Velocity:[/] "
                f"[$success]{self.context.data_processor.max_vertical_velocity}[/] m/s\n",
                id="benchmark-results-widget",
            )

            with Horizontal(id="button-container"):
                # Add the button to go back to the main screen
                yield Button(
                    "Back to Main Screen", id="back-to-main-screen-button", variant="primary"
                )
                # Add the Button to exit the application
                yield Button("Exit", id="exit-button", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Called when a button is pressed.

        Handles the button presses.
        """
        if event.button.id == "back-to-main-screen-button":
            self.app.pop_screen()
        elif event.button.id == "exit-button":
            self.app.exit()
