"""Module to show the terminal GUI for the airbrakes system."""

from typing import TYPE_CHECKING, ClassVar

import textual.renderables.digits
from gpiozero.pins.mock import MockFactory, MockPWMPin
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.renderables.digits import DIGITS
from textual.widgets import Digits, Footer, Header, Label, Static

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.logger import Logger
from airbrakes.graphics.launch_selector import LaunchSelector, SelectedLaunchConfiguration
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from airbrakes.mock.mock_imu import MockIMU
from airbrakes.mock.mock_logger import MockLogger
from constants import IMU_PORT, LOGS_PATH, SERVO_PIN

if TYPE_CHECKING:
    from textual.timer import Timer


unicode_T = """─┬─
 │
 ╵
"""


def add_unicode_T_to_digits():
    """Hack to modify the textual library code to include a 3x3 version of the letter 'T', so we
    can include it in the flight time display."""
    textual.renderables.digits.DIGITS = f"{DIGITS}T"
    textual.renderables.digits.DIGITS3X3.extend(unicode_T.splitlines())
    textual.renderables.digits.DIGITS3X3_BOLD.extend(unicode_T.splitlines())


class TimeDisplay(Digits):
    """A widget to display elapsed flight time"""

    add_unicode_T_to_digits()


class FlightDisplay(App):
    """A terminal based GUI for displaying real-time flight data."""

    BINDINGS: ClassVar[list] = [("q", "quit", "Quit")]
    TITLE = "AirbrakesV2"
    SCREENS: ClassVar[dict] = {"launch_selector": LaunchSelector}

    def __init__(self) -> None:
        super().__init__()
        self.imu: IMU | None = None
        self.servo: Servo | None = None
        self.logger: Logger | None = None
        self.update_timer: Timer | None = None

    @work
    async def on_mount(self) -> None:
        await self.push_screen("launch_selector", self.create_components, wait_for_dismiss=True)
        self.update_timer = self.set_interval(1 / 50, self.update_telemetry, pause=True)

    def create_components(self, launch_config: SelectedLaunchConfiguration) -> None:
        """Create the system components needed for the airbrakes system."""
        if launch_config.launch_options is not None:
            self.imu = MockIMU(
                real_time_simulation=not launch_config.launch_options.fast_simulation,
                log_file_path=launch_config.selected_button,
            )
            self.logger = MockLogger(
                LOGS_PATH, delete_log_file=not launch_config.launch_options.keep_log_file
            )

            self.servo = (
                Servo(SERVO_PIN)
                if launch_config.launch_options.real_servo
                else Servo(SERVO_PIN, pin_factory=MockFactory(pin_class=MockPWMPin))
            )
        else:
            # Use real hardware components
            self.servo = Servo(SERVO_PIN)
            self.imu = IMU(IMU_PORT)
            self.logger = Logger(LOGS_PATH)

    def update_telemetry(self) -> None:
        """Updates all the reactive variables with the latest telemetry data."""

    def run_flight_loop(self) -> None:
        """Main flight control loop that runs until shutdown is requested or interrupted."""

        # Initialize data processing and prediction
        data_processor = IMUDataProcessor()
        apogee_predictor = ApogeePredictor()

        # Initialize the airbrakes context and display
        airbrakes = AirbrakesContext(
            self.servo, self.imu, self.logger, data_processor, apogee_predictor
        )
        try:
            airbrakes.start()
            # Starts the airbrakes system and display

            while not self.shutdown_requested:
                # Update the state machine
                self.imu.update()
                self.servo.update()
                self.logger.update()

                # Stop the simulation when the data is exhausted
                if not self.imu.is_running:
                    break
        except KeyboardInterrupt:
            pass

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
        yield Label("SIMULATED TELEMETRY", id="title")
        yield TimeDisplay("T+" + self.time_display, id="time_display")
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
