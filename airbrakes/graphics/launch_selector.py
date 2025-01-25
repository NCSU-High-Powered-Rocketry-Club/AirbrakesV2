"""The launch file selection screen displayed on startup."""

from pathlib import Path

import msgspec
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Center, Grid, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Button,
    DataTable,
    Label,
    RadioButton,
    RadioSet,
    Static,
    Switch,
)

from airbrakes.mock.mock_imu import MockIMU
from airbrakes.utils import format_date_string, format_seconds_to_mins_and_secs

AVAILABLE_FILES = list(Path("launch_data").glob("*.csv"))


class LaunchOptions(msgspec.Struct):
    """The options for the launch simulation."""

    real_servo: bool
    keep_log_file: bool
    fast_simulation: bool
    real_camera: bool


class SelectedLaunchConfiguration(msgspec.Struct):
    """The selected launch configuration, which is sent to the main sim screen."""

    selected_button: Path | None
    launch_options: LaunchOptions | None


class LaunchFilesButtons(Widget):
    """The radio buttons for selecting the launch file to use."""

    def compose(self) -> ComposeResult:
        with RadioSet(id="launch-files-radio-set"):
            for idx, file in enumerate(AVAILABLE_FILES):
                # The file name is the title of the radio button
                # The first file is selected by default (idx == 0)
                yield RadioButton(f"{file.stem.replace('_', ' ').title()}", value=not idx)


class LaunchMetadataDisplay(Widget):
    """The display for the metadata of the selected launch file."""

    selected_file: reactive[Path] = reactive(AVAILABLE_FILES[0])
    fetched_metadata = MockIMU.read_file_metadata()

    def compose(self) -> ComposeResult:
        yield DataTable(
            show_header=False, zebra_stripes=True, id="launch-metadata", cursor_type="none"
        )

    def update_metadata(self, launch_metadata: dict, table: DataTable, update: bool) -> None:
        fields = {
            "Launch date": format_date_string(launch_metadata["date"]),
            "Flight Length": format_seconds_to_mins_and_secs(
                launch_metadata["flight_data"]["flight_length_seconds"]
            ),
            "Apogee": f"{launch_metadata['flight_data']['apogee_meters']} m",
            "Wind Speed": f"{launch_metadata['launch_site']['wind_speed_kmh']} km/h",
            "Wind Direction": f"{launch_metadata['launch_site']['wind_direction']}",
            "Temperature": f"{launch_metadata['launch_site']['air_temperature_celsius']} °C",
        }

        for key, value in fields.items():
            label = Text(key, style="bold")
            # If row exists, update it:
            if update:
                table.update_cell(key, "value", value)
            else:
                table.add_row(value, label=label, key=key)

    def watch_selected_file(self, new_path: Path) -> None:
        launch_metadata = self.fetched_metadata[new_path.name]
        table = self.query_one(DataTable)
        if not table.row_count:  # We are still before on_mount
            table.add_column("Value", key="value")
            self.update_metadata(launch_metadata, table, update=False)
        else:
            self.update_metadata(launch_metadata, table, update=True)


class LaunchConfiguration(Widget):
    """The configuration widget consisting of the options for the launch simulation."""

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Real Servo", id="label-real-servo"),
            Switch(id="real-servo-switch"),
            Label("Keep Log File", id="label-keep-log-file"),
            Switch(id="keep-log-file-switch"),
            Label("Fast Simulation", id="label-fast-sim"),
            Switch(id="fast-sim-switch"),
            Label("Real Camera", id="label-real-camera"),
            Switch(id="real-camera-switch"),
            id="launch-configuration-grid",
        )


class LaunchSelector(Screen):
    """The launch file selection screen displayed on startup."""

    CSS_PATH = "css/launch_selector.tcss"

    selected_file: reactive[Path] = reactive(AVAILABLE_FILES[0])
    launch_options: LaunchOptions = LaunchOptions(
        real_servo=False, keep_log_file=False, fast_simulation=False, real_camera=False
    )

    def compose(self) -> ComposeResult:
        yield Static("AirbrakesV2", id="title")
        yield LaunchMetadataDisplay(id="launch-metadata-container").data_bind(
            LaunchSelector.selected_file
        )
        yield LaunchFilesButtons(id="launch-files-container")
        yield LaunchConfiguration(id="launch-configuration-container")
        with Vertical(id="button-container"), Center():
            yield Button("Run Mock Simulation", id="run-mock-sim-button")
            yield Button("Run Real Flight", id="run-real-flight-button", disabled=True)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle the radio set change events."""
        # This event is triggered when a radio button is selected
        selection = AVAILABLE_FILES[event.index]
        self.selected_file = selection

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle the switch change events."""
        # This event is triggered when a switch is toggled
        match event.switch.id:
            case "real-servo-switch":
                self.launch_options.real_servo = event.value
            case "keep-log-file-switch":
                self.launch_options.keep_log_file = event.value
            case "fast-sim-switch":
                self.launch_options.fast_simulation = event.value
            case "real-camera-switch":
                self.launch_options.real_camera = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the button press events."""
        # Pop the launch selector screen and push the flight display screen:
        if event.button.id == "run-mock-sim-button":
            config = SelectedLaunchConfiguration(
                selected_button=self.selected_file,
                launch_options=self.launch_options,
            )
            self.dismiss(config)
        elif event.button.id == "run-real-flight-button":
            config = SelectedLaunchConfiguration(
                selected_button=None,
                launch_options=None,
            )
            self.dismiss(config)
