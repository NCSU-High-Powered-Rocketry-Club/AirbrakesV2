"""The launch file selection screen displayed on startup."""

from pathlib import Path

import msgspec
from textual.app import ComposeResult
from textual.containers import Center, Grid, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Label,
    RadioButton,
    RadioSet,
    Static,
    Switch,
)
from textual_image.widget import Image
from textual_pyfiglet import FigletWidget

from airbrakes.graphics.utils import (
    format_seconds_to_mins_and_secs,
    get_date_from_iso_string,
    get_time_from_iso_string,
)
from airbrakes.mock.mock_imu import MockIMU

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


class LaunchSelector(Screen[SelectedLaunchConfiguration]):
    """The launch file selection screen displayed on startup."""

    CSS_PATH = "css/launch_selector.tcss"

    selected_file: reactive[Path] = reactive(AVAILABLE_FILES[0])
    launch_options: LaunchOptions = LaunchOptions(
        real_servo=False, keep_log_file=False, fast_simulation=False, real_camera=False
    )

    def compose(self) -> ComposeResult:
        with Grid(id="launch-selector-grid"):
            # The title takes 3 columns:
            yield FigletWidget("AirbrakesV2", id="title", markup=False, font="dos_rebel")

            # TODO: Legacy launch 2 and purple launch are missing pictures
            self.launch_image = LaunchImage(id="launch-image-widget").data_bind(
                LaunchSelector.selected_file
            )
            yield self.launch_image
            self.launch_files = LaunchFilesButtons(id="launch-files-container")
            yield self.launch_files
            self.launch_config = LaunchConfiguration(id="launch-configuration-container")
            self.launch_config.border_title = "Launch Configuration"
            yield self.launch_config
            self.launch_metadata = LaunchMetadataDisplay(id="launch-metadata-container").data_bind(
                LaunchSelector.selected_file
            )
            yield self.launch_metadata
            with Vertical(id="button-container"), Center():
                yield Button("Run Mock Simulation", id="run-mock-sim-button")
                yield Button("Run Benchmark", id="run-benchmark-button", disabled=True)

        yield Footer()

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
        elif event.button.id == "run-benchmark-button":
            config = SelectedLaunchConfiguration(
                selected_button=None,
                launch_options=None,
            )
            self.dismiss(config)


class LaunchImage(Static):
    """The image widget for the launch file."""

    selected_file: reactive[Path] = reactive(AVAILABLE_FILES[0], init=False)

    def compose(self) -> ComposeResult:
        self.image = Image(
            self.convert_csv_path_to_image_path(self.selected_file), id="launch-image"
        )
        yield self.image

    def convert_csv_path_to_image_path(self, path: Path) -> Path:
        """Convert the CSV path to the image path."""
        # The image is in the launch_data/pictures folder:
        # The image name is the same as the CSV file name, but with a .jpg extension
        return Path("launch_data/pictures") / f"{path.stem}.jpg"

    def watch_selected_file(self, new_path: Path) -> None:
        """Update the image when the selected file changes."""
        # Find the image in the launch_data/pictures folder:
        self.image.image = self.convert_csv_path_to_image_path(new_path)


class LaunchMetadataDisplay(Widget):
    """The display for the metadata of the selected launch file."""

    selected_file: reactive[Path] = reactive(AVAILABLE_FILES[0])
    fetched_metadata = MockIMU.read_file_metadata()

    def compose(self) -> ComposeResult:
        self.data_table = DataTable(
            show_header=False, zebra_stripes=True, id="launch-metadata", cursor_type="none"
        )
        self.data_table.border_title = "Launch Metadata"
        yield self.data_table

    def update_metadata(self, launch_metadata: dict, table: DataTable, update: bool) -> None:
        # Add time and description fields to the table:
        fields = {
            "Launch date": get_date_from_iso_string(launch_metadata["date"]),
            "Launch time": get_time_from_iso_string(launch_metadata["date"]),
            "Launch site": launch_metadata["launch_site"]["location"],
            "Flight Length": format_seconds_to_mins_and_secs(
                launch_metadata["flight_data"]["flight_length_seconds"]
            ),
            "Apogee": f"{launch_metadata['flight_data']['apogee_meters']} m",
            "Wind Speed": f"{launch_metadata['launch_site']['wind_speed_kmh']} km/h",
            "Wind Direction": f"{launch_metadata['launch_site']['wind_direction']}",
            "Temperature": f"{launch_metadata['launch_site']['air_temperature_celsius']} °C",
            "Description": launch_metadata["flight_description"],
        }

        for key, value in fields.items():
            # If row exists, update it:
            if update:
                table.update_cell(key, "value", value, update_width=True)
            else:
                table.add_row(value, height=None, label=key, key=key)

    def watch_selected_file(self, new_path: Path) -> None:
        launch_metadata = self.fetched_metadata[new_path.name]
        table = self.data_table
        if not table.row_count:  # We are still before on_mount
            table.add_column("Value", key="value")
            self.update_metadata(launch_metadata, table, update=False)
        else:
            self.update_metadata(launch_metadata, table, update=True)


class LaunchConfiguration(Widget):
    """The configuration widget consisting of the options for the launch simulation."""

    def compose(self) -> ComposeResult:
        with Grid(id="launch-configuration-grid"):
            yield Label("Real Servo", id="label-real-servo")
            yield Switch(id="real-servo-switch")
            yield Label("Keep Log File", id="label-keep-log-file")
            yield Switch(id="keep-log-file-switch")
            yield Label("Fast Simulation", id="label-fast-sim")
            yield Switch(id="fast-sim-switch")
            yield Label("Real Camera", id="label-real-camera")
            yield Switch(id="real-camera-switch")


class LaunchFilesButtons(Widget):
    """The radio buttons for selecting the launch file to use."""

    def compose(self) -> ComposeResult:
        with RadioSet(id="launch-files-radio-set") as radio_set:
            for idx, file in enumerate(AVAILABLE_FILES):
                # The file name is the title of the radio button
                # The first file is selected by default (idx == 0)
                yield RadioButton(f"{file.stem.replace('_', ' ').title()}", value=not idx)

            radio_set.border_title = "Launch Files"
