"""Module to show the terminal GUI for the airbrakes system."""

from typing import TYPE_CHECKING, ClassVar

import textual.renderables.digits
from gpiozero.pins.mock import MockFactory, MockPWMPin
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Center, Grid, Horizontal
from textual.reactive import reactive, var
from textual.renderables.digits import DIGITS
from textual.widgets import Button, Digits, Footer, Label, Placeholder, Static
from textual.worker import Worker, WorkerState, get_current_worker

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
    CSS_PATH = "css/visual.tcss"

    def __init__(self) -> None:
        super().__init__()
        self.update_timer: Timer | None = None
        self.airbrakes: AirbrakesContext | None = None
        self.is_mock: bool = False
        self._pre_calculated_motor_burn_time: int = None

    @work
    async def on_mount(self) -> None:
        await self.push_screen("launch_selector", self.create_components, wait_for_dismiss=True)
        self.update_timer = self.set_interval(1 / 20, self.update_telemetry, pause=True)
        self.start()

    @work
    async def on_unmount(self) -> None:
        if self.update_timer:
            self.update_timer.pause()
        if self.airbrakes:
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

    def update_telemetry(self) -> None:
        """Updates all the reactive variables with the latest telemetry data."""
        flight_header = self.query_one(FlightHeader)
        flight_header.update_header(self.airbrakes, self.is_mock)
        flight_information = self.query_one(FlightInformation)
        flight_information.update_flight_information(self.airbrakes)

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
        with Grid(id="main-grid"):
            yield FlightHeader(id="flight-header")
            yield FlightInformation(id="flight-information-panel")
        yield Footer()


class FlightHeader(Static):
    """Panel displaying the launch file name, launch time, and simulation status."""

    state: reactive[str] = reactive("Standby")

    airbrakes: AirbrakesContext | None = None
    t_zero_time = reactive(0)
    takeoff_time = 0
    _pre_calculated_motor_burn_time: int | None = None

    def compose(self) -> ComposeResult:
        yield Label("", id="launch-file-name", disabled=True)
        yield Label("00:00.00", id="normal-sim-time")
        yield Static()
        yield Static()
        yield TimeDisplay("T+00:00", id="launch-clock")
        yield Static()
        yield Label("STATUS: ", id="state")
        with Center():
            yield SimulationSpeed(id="sim-speed-panel")

    def watch_t_zero_time(self) -> None:
        time_display = self.query_one("#launch-clock", TimeDisplay)
        after_launch = self.t_zero_time > 0
        launch_time = TimeDisplay.format_ns_to_min_s_ms(abs(self.t_zero_time))
        launch_time = f"T+{launch_time}" if after_launch else f"T-{launch_time}"
        time_display.update(launch_time)

    def watch_state(self) -> None:
        state_label = self.query_one("#state", Label)

        if not self.takeoff_time and self.state == "MotorBurnState":
            self.takeoff_time = self.airbrakes.state.start_time_ns

        label = self.state.removesuffix("State")
        state_label.update(f"STATUS: {label}")

    def calculate_launch_time(self, is_mock: bool) -> int:
        """
        Calculates the launch time relative to the start of motor burn.
        :return: The launch time in nanoseconds relative to the start of motor burn.
        """
        # Just update our launch time, if it was set (see watch_state)
        if self.takeoff_time:
            current_timestamp = self.airbrakes.data_processor.current_timestamp
            return current_timestamp - self.takeoff_time

        # We are before launch (T-0). Only happens when running a mock:
        if is_mock:
            current_timestamp = self.airbrakes.data_processor.current_timestamp
            return current_timestamp - self._pre_calculated_motor_burn_time

        return 0

    def update_header(self, airbrakes: AirbrakesContext, is_mock: bool) -> None:
        self.airbrakes = airbrakes

        file_name = self.query_one("#launch-file-name", Label)
        if file_name.disabled:
            launch_file_name = airbrakes.imu._log_file_path.stem.replace("_", " ").title()
            file_name.update(launch_file_name)
            file_name.disabled = False

        if not self._pre_calculated_motor_burn_time:
            self._pre_calculated_motor_burn_time = self.airbrakes.imu.get_launch_time()

        self.state = airbrakes.state.name
        self.t_zero_time = self.calculate_launch_time(is_mock)


class FlightInformation(Static):
    """Panel displaying the real-time flight information."""

    airbrakes: AirbrakesContext | None = None

    def compose(self) -> ComposeResult:
        ft = FlightTelemetry(id="flight_data_panel")
        ft.border_title = "SIMULATED TELEMETRY"
        yield ft
        yield Placeholder("tabbed graphs")
        yield Placeholder("2d rocket vis")
        yield DebugTelemetry(id="debug-flight-data-panel")
        yield Placeholder("downrange map")
        yield Placeholder("2d rocket vis")

    def update_flight_information(self, airbrakes: AirbrakesContext) -> None:
        self.airbrakes = airbrakes
        flight_telemetry = self.query_one("#flight_data_panel", FlightTelemetry)
        debug_telemetry = self.query_one("#debug-flight-data-panel", DebugTelemetry)
        flight_telemetry.update_flight_telemetry(airbrakes)
        debug_telemetry.update_debug_telemetry(airbrakes)


class SimulationSpeed(Static):
    """Panel displaying the current simulation speed, with buttons to change it."""

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("<", id="speed_decrease_button")
            yield Label("1x", id="simulation_speed")
            yield Button(">", id="speed_increase_button")


class DebugTelemetry(Static):
    """Collapsible panel for displaying debug telemetry data."""

    airbrakes: AirbrakesContext | None = None
    imu_queue_size = reactive(0)
    cpu_usage = reactive("")
    state = var("Standby")
    apogee = var(0.0)
    apogee_convergence_time = reactive(0.0)
    alt_at_convergence = reactive(0.0)
    apogee_at_convergence = reactive(0.0)
    log_buffer_size = reactive(0)
    fetched_packets = reactive(0)
    coast_start_time = 0

    def compose(self) -> ComposeResult:
        yield Label("IMU Queue Size: ", id="imu_queue_size")
        yield Label("Convergence Time: ", id="apogee_convergence_time")
        yield Label("Convergence Height: ", id="alt_at_convergence")
        yield Label("Pred. Apogee at Convergence: ", id="apogee_at_convergence")
        yield Label("Fetched packets: ", id="fetched_packets")
        yield Label("Log buffer size: ", id="log_buffer_size")
        yield Label("CPU Usage: ", id="cpu_usage")

    def watch_imu_queue_size(self) -> None:
        imu_queue_size_label = self.query_one("#imu_queue_size", Label)
        imu_queue_size_label.update(f"IMU Queue Size: {self.imu_queue_size}")

    def watch_state(self) -> None:
        if self.state == "CoastState":
            self.coast_start_time = self.airbrakes.state.start_time_ns

    def watch_apogee(self) -> None:
        if self.coast_start_time and not self.apogee_convergence_time:
            self.apogee_convergence_time = (
                self.airbrakes.data_processor.current_timestamp - self.coast_start_time
            ) * 1e-9
            self.alt_at_convergence = self.airbrakes.data_processor.current_altitude
            self.apogee_at_convergence = self.apogee

    def watch_apogee_convergence_time(self) -> None:
        apogee_convergence_time_label = self.query_one("#apogee_convergence_time", Label)
        apogee_convergence_time_label.update(
            f"Convergence Time: {self.apogee_convergence_time:.2f} s"
        )

    def watch_alt_at_convergence(self) -> None:
        alt_at_convergence_label = self.query_one("#alt_at_convergence", Label)
        alt_at_convergence_label.update(f"Convergence Height: {self.alt_at_convergence:.2f} m")

    def watch_apogee_at_convergence(self) -> None:
        apogee_at_convergence_label = self.query_one("#apogee_at_convergence", Label)
        apogee_at_convergence_label.update(
            f"Pred. Apogee at Convergence: {self.apogee_at_convergence:.2f} m"
        )

    def watch_log_buffer_size(self) -> None:
        log_buffer_size_label = self.query_one("#log_buffer_size", Label)
        log_buffer_size_label.update(f"Log buffer size: {self.log_buffer_size} packets")

    def watch_fetched_packets(self) -> None:
        fetched_packets_label = self.query_one("#fetched_packets", Label)
        fetched_packets_label.update(f"Fetched packets: {self.fetched_packets}")

    def watch_cpu_usage(self) -> None:
        cpu_usage_label = self.query_one("#cpu_usage", Label)
        cpu_usage_label.update(f"CPU Usage: {self.cpu_usage}")

    def update_debug_telemetry(self, airbrakes: AirbrakesContext) -> None:
        self.airbrakes = airbrakes
        self.imu_queue_size = airbrakes.imu._data_queue.qsize()
        self.log_buffer_size = len(self.airbrakes.logger._log_buffer)
        self.apogee = self.airbrakes.apogee_predictor.apogee
        self.fetched_packets = len(self.airbrakes.imu_data_packets)
        self.state = airbrakes.state.name
        # self.cpu_usage = cpu_usage


class FlightTelemetry(Static):
    """Panel displaying real-time flight information."""

    vertical_velocity = reactive(0.0)
    max_vertical_velocity = reactive(0.0)
    current_height = reactive(0.0)
    max_height = reactive(0.0)
    apogee_prediction = reactive(0.0)
    airbrakes_extension = reactive(0.0)

    def compose(self) -> ComposeResult:
        yield Label("Velocity: ", id="vertical_velocity")
        yield Label("Max Velocity: ", id="max_vertical_velocity")
        yield Label("Altitude: ", id="current_height")
        yield Label("Max altitude: ", id="max_height")
        yield Label("Predicted Apogee: ", id="apogee_prediction")
        yield Label("Airbrakes Extension: ", id="airbrakes_extension")

    def watch_vertical_velocity(self) -> None:
        vertical_velocity_label = self.query_one("#vertical_velocity", Label)
        vertical_velocity_label.update(f"Velocity: {self.vertical_velocity:.2f} m/s")

    def watch_max_vertical_velocity(self) -> None:
        max_vertical_velocity_label = self.query_one("#max_vertical_velocity", Label)
        max_vertical_velocity_label.update(f"Max Velocity: {self.max_vertical_velocity:.2f} m/s")

    def watch_current_height(self) -> None:
        current_height_label = self.query_one("#current_height", Label)
        current_height_label.update(f"Altitude: {self.current_height:.2f} m")

    def watch_max_height(self) -> None:
        max_height_label = self.query_one("#max_height", Label)
        max_height_label.update(f"Max altitude: {self.max_height:.2f} m")

    def watch_apogee_prediction(self) -> None:
        apogee_prediction_label = self.query_one("#apogee_prediction", Label)
        apogee_prediction_label.update(f"Predicted Apogee: {self.apogee_prediction:.2f} m")

    def watch_airbrakes_extension(self) -> None:
        airbrakes_extension_label = self.query_one("#airbrakes_extension", Label)
        airbrakes_extension_label.update(f"Airbrakes Extension: {self.airbrakes_extension:.2f}")

    def update_flight_telemetry(self, airbrakes: AirbrakesContext) -> None:
        self.vertical_velocity = airbrakes.data_processor.vertical_velocity
        self.max_vertical_velocity = airbrakes.data_processor.max_vertical_velocity
        self.current_height = airbrakes.data_processor.current_altitude
        self.max_height = airbrakes.data_processor.max_altitude
        self.apogee_prediction = airbrakes.apogee_predictor.apogee
        self.airbrakes_extension = airbrakes.current_extension.value
