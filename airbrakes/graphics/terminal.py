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
from textual.worker import Worker, WorkerState, get_current_worker

import airbrakes
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

    @staticmethod
    def format_ns_to_min_s_ms(ns: int) -> str:
        """
        Formats a time in nanoseconds to a string in the format MM:SS:ms.
        :param: ns: The time in nanoseconds.

        :return: The formatted time string.
        """

        # Convert nanoseconds to seconds
        s = ns / 1e9

        # Get the minutes
        m = s // 60
        s %= 60

        # Get the milliseconds
        ms = (s % 1) * 100

        return f"{m:02.0f}:{s:02.0f}.{ms:02.0f}"


class AirbrakesApplication(App):
    """A terminal based GUI for displaying real-time flight data."""

    BINDINGS: ClassVar[list] = [("q", "quit", "Quit")]
    TITLE = "AirbrakesV2"
    SCREENS: ClassVar[dict] = {"launch_selector": LaunchSelector}

    def __init__(self) -> None:
        super().__init__()
        self.update_timer: Timer | None = None
        self.airbrakes: AirbrakesContext = None
        self.is_mock: bool = False
        self._pre_calculated_motor_burn_time: int = None

    @work
    async def on_mount(self) -> None:
        await self.push_screen("launch_selector", self.create_components, wait_for_dismiss=True)
        self.update_timer = self.set_interval(1 / 50, self.update_telemetry, pause=True)
        self.start()

    @work
    async def on_unmount(self) -> None:
        self.update_timer.pause()
        self.airbrakes.stop()

    def start(self) -> None:
        """Starts the flight display."""
        # Initialize the airbrakes context and display
        self.airbrakes.start()
        self.call_later(self.update_timer.resume)
        self.run_worker(self.run_flight_loop, name="Flight Loop", exclusive=True, thread=True)

    def create_components(self, launch_config: SelectedLaunchConfiguration) -> None:
        """Create the system components needed for the airbrakes system."""
        if launch_config.launch_options is not None:
            imu = MockIMU(
                real_time_simulation=not launch_config.launch_options.fast_simulation,
                log_file_path=launch_config.selected_button,
            )
            logger = MockLogger(
                LOGS_PATH, delete_log_file=not launch_config.launch_options.keep_log_file
            )

            servo = (
                Servo(SERVO_PIN)
                if launch_config.launch_options.real_servo
                else Servo(SERVO_PIN, pin_factory=MockFactory(pin_class=MockPWMPin))
            )
            self.is_mock = True
        else:
            # Use real hardware components
            servo = Servo(SERVO_PIN)
            imu = IMU(IMU_PORT)
            logger = Logger(LOGS_PATH)

        # Initialize data processing and prediction
        data_processor = IMUDataProcessor()
        apogee_predictor = ApogeePredictor()

        self.airbrakes = AirbrakesContext(servo, imu, logger, data_processor, apogee_predictor)
        self._pre_calculated_motor_burn_time: int = self.airbrakes.imu.get_launch_time()

    def update_telemetry(self) -> None:
        """Updates all the reactive variables with the latest telemetry data."""
        data_panel = self.query_one(FlightDisplay)
        time = self.calculate_launch_time()
        # print(f"Returnded time: {time}")
        data_panel.t_zero_time = time
        data_panel.current_height = self.airbrakes.data_processor.current_altitude
        data_panel.max_height = self.airbrakes.data_processor.max_altitude
        data_panel.vertical_velocity = self.airbrakes.data_processor.vertical_velocity
        data_panel.max_vertical_velocity = self.airbrakes.data_processor.max_vertical_velocity
        data_panel.apogee_prediction = self.airbrakes.apogee_predictor.apogee
        data_panel.state = self.airbrakes.state.name

    def calculate_launch_time(self) -> int:
        """
        Calculates the launch time relative to the start of motor burn.
        :return: The launch time in nanoseconds relative to the start of motor burn.
        """
        # Just update our launch time, if it was set:

        flight_display = self.query_one(FlightDisplay)
        takeoff_time = flight_display.takeoff_time
        if takeoff_time:
            # print("t_zero_time is set")
            current_timestamp = self.airbrakes.data_processor.current_timestamp
            return current_timestamp - takeoff_time

        # No launch time set yet, and we are in MotorBurnState:
        # if not takeoff_time and self.airbrakes.state.name == "MotorBurnState":
        # print("t_zero_time is not set")
        # takeoff_time = self.airbrakes.state.start_time_ns
        # return 0

        # We are before launch (T-0). Only happens when running a mock:
        if self.is_mock:
            current_timestamp = self.airbrakes.data_processor.current_timestamp
            if not current_timestamp:
                return None
            return current_timestamp - self._pre_calculated_motor_burn_time

        return None

    def run_flight_loop(self) -> None:
        """Main flight control loop that runs until shutdown is requested or interrupted."""

        worker = get_current_worker()
        while not self.airbrakes.shutdown_requested and not worker.is_cancelled:
            self.airbrakes.update()

            # Stop the simulation when the data is exhausted
            if not self.airbrakes.imu.is_running:
                break

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Used to shut down the airbrakes system when the data is exhausted."""
        if event.worker.name == "Flight Loop" and event.state == WorkerState.SUCCESS:
            self.airbrakes.stop()

    def compose(self) -> ComposeResult:
        """Create the layout of the app."""
        yield Header()
        yield Horizontal(
            Vertical(FlightDisplay(id="flight_data_panel", airbrakes=airbrakes)), id="main"
        )
        yield Footer()


class FlightDisplay(Static):
    """Panel displaying real-time flight information."""

    takeoff_time = 0
    airbrakes: reactive[AirbrakesContext | None] = reactive(None)
    t_zero_time = reactive(0)
    state = reactive("Standby")
    vertical_velocity = reactive(0.0)
    max_vertical_velocity = reactive(0.0)
    current_height = reactive(0.0)
    max_height = reactive(0.0)
    apogee_prediction = reactive(0.0)
    imu_queue_size = reactive(0)
    cpu_usage = reactive("")

    def __init__(self, airbrakes, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.airbrakes: AirbrakesContext = airbrakes

    def compose(self) -> ComposeResult:
        yield Label("SIMULATED TELEMETRY", id="title")
        yield TimeDisplay(f"T+{self.t_zero_time}", id="time_display")
        yield Label("State: ", id="state")
        yield Label("Current Velocity: ", id="vertical_velocity")
        yield Label("Max Velocity: ", id="max_vertical_velocity")
        yield Label("Current Height: ", id="current_height")
        yield Label("Max Height: ", id="max_height")
        yield Label("Predicted Apogee: ", id="apogee_prediction")
        yield Label("IMU Queue Size: ", id="imu_queue_size")
        yield Label("CPU Usage: ", id="cpu_usage")

    def watch_time_display(self) -> None:
        time_display = self.query_one("#time_display", TimeDisplay)
        after_launch = self.t_zero_time > 0
        launch_time = TimeDisplay.format_ns_to_min_s_ms(abs(self.t_zero_time))
        launch_time = f"T+{launch_time}" if after_launch else f"T-{launch_time}"
        time_display.update(launch_time)

    def watch_state(self) -> None:
        state_label = self.query_one("#state", Label)
        if not self.takeoff_time and self.state == "MotorBurnState":
            self.takeoff_time = self.airbrakes.state.start_time_ns
        state_label.update(f"{self.state}")

    def watch_vertical_velocity(self) -> None:
        vertical_velocity_label = self.query_one("#vertical_velocity", Label)
        vertical_velocity_label.update(f"Current Velocity: {self.vertical_velocity:.2f} m/s")

    def watch_max_vertical_velocity(self) -> None:
        max_vertical_velocity_label = self.query_one("#max_vertical_velocity", Label)
        max_vertical_velocity_label.update(f"Max Velocity: {self.max_vertical_velocity:.2f} m/s")

    def watch_current_height(self) -> None:
        current_height_label = self.query_one("#current_height", Label)
        current_height_label.update(f"Current Height: {self.current_height:.2f} m")

    def watch_max_height(self) -> None:
        max_height_label = self.query_one("#max_height", Label)
        max_height_label.update(f"Max Height: {self.max_height:.2f} m")

    def watch_apogee_prediction(self) -> None:
        apogee_prediction_label = self.query_one("#apogee_prediction", Label)
        apogee_prediction_label.update(f"Predicted Apogee: {self.apogee_prediction:.2f} m")

    def watch_imu_queue_size(self) -> None:
        imu_queue_size_label = self.query_one("#imu_queue_size", Label)
        imu_queue_size_label.update(f"IMU Queue Size: {self.imu_queue_size}")

    def watch_cpu_usage(self) -> None:
        cpu_usage_label = self.query_one("#cpu_usage", Label)
        cpu_usage_label.update(f"CPU Usage: {self.cpu_usage}")


if __name__ == "__main__":
    app = AirbrakesApplication()
    app.run()
