"""Module to show the terminal GUI for the airbrakes system."""

from typing import TYPE_CHECKING, ClassVar

import textual.renderables.digits
from gpiozero.pins.mock import MockFactory, MockPWMPin
from textual import on, work
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
        self.airbrakes: AirbrakesContext
        self.is_mock: bool = False
        self._pre_calculated_motor_burn_time: int = None

    @work
    async def on_mount(self) -> None:
        await self.push_screen("launch_selector", self.create_components, wait_for_dismiss=True)
        self.update_timer = self.set_interval(1 / 20, self.update_telemetry, pause=True)
        self.initialize_widgets()
        self.watch(self.query_one(SimulationSpeed), "sim_speed", self.change_sim_speed)
        self.start()

    @work
    async def on_unmount(self) -> None:
        if self.update_timer:
            self.update_timer.pause()
        if self.airbrakes:
            self.airbrakes.stop()

    def initialize_widgets(self) -> None:
        """Supplies the airbrakes context and related objects to the widgets for proper
        operation."""
        flight_header = self.query_one(FlightHeader)
        flight_information = self.query_one(FlightInformation)
        flight_header.initialize_widgets(self.airbrakes, self.is_mock)
        flight_information.initialize_widgets(self.airbrakes)

    def start(self) -> None:
        """Starts the flight display."""
        # Initialize the airbrakes context and display
        self.airbrakes.start()
        self.call_later(self.update_timer.resume)
        self.run_worker(self.run_flight_loop, name="Flight Loop", exclusive=True, thread=True)

    def change_sim_speed(self, sim_speed: float) -> None:
        self.airbrakes.imu._sim_speed_factor.value = sim_speed
        # TODO: Make the time blink if sim_speed == 0

    def create_components(self, launch_config: SelectedLaunchConfiguration) -> None:
        """Create the system components needed for the airbrakes system."""
        if launch_config.launch_options is not None:
            imu = MockIMU(
                simulation_speed=2.0 if launch_config.launch_options.fast_simulation else 1.0,
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
        flight_header.update_header()
        flight_information = self.query_one(FlightInformation)
        flight_information.update_flight_information()

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
    is_mock: bool = True
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

    def initialize_widgets(self, airbrakes: AirbrakesContext, is_mock: bool) -> None:
        self.airbrakes = airbrakes
        self.is_mock = is_mock
        self.query_one(SimulationSpeed).sim_speed = self.airbrakes.imu._sim_speed_factor.value

    def calculate_launch_time(self) -> int:
        """
        Calculates the launch time relative to the start of motor burn.
        :return: The launch time in nanoseconds relative to the start of motor burn.
        """
        # Just update our launch time, if it was set (see watch_state)
        if self.takeoff_time:
            current_timestamp = self.airbrakes.data_processor.current_timestamp
            return current_timestamp - self.takeoff_time

        # We are before launch (T-0). Only happens when running a mock:
        if self.is_mock:
            current_timestamp = self.airbrakes.data_processor.current_timestamp
            return current_timestamp - self._pre_calculated_motor_burn_time

        return 0

    def update_header(self) -> None:
        file_name = self.query_one("#launch-file-name", Label)
        if file_name.disabled:
            launch_file_name = self.airbrakes.imu._log_file_path.stem.replace("_", " ").title()
            file_name.update(launch_file_name)
            file_name.disabled = False

        if not self._pre_calculated_motor_burn_time:
            self._pre_calculated_motor_burn_time = self.airbrakes.imu.get_launch_time()

        self.state = self.airbrakes.state.name
        self.t_zero_time = self.calculate_launch_time()


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


class SimulationSpeed(Static, can_focus=True):
    """Panel displaying the current simulation speed, with buttons to change it."""

    BINDINGS: ClassVar[list] = [
        ("comma", "decrease_sim_speed", "Dec. speed"),
        ("full_stop", "increase_sim_speed", "Inc. speed"),
        ("space", "pause_sim", "Pause sim"),
        ("space", "play_sim", "Play sim"),
    ]

    sim_speed: reactive[float] = reactive(1.0, bindings=True)
    old_sim_speed: float = 1.0

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("<", id="speed_decrease_button")
            yield Label("1.0x", id="simulation_speed")
            yield Button(">", id="speed_increase_button")

    def validate_sim_speed(self, sim_speed: float) -> float:
        if sim_speed < 0.0:
            return 0
        if sim_speed > 2.0:
            return 2.0
        return sim_speed

    def watch_sim_speed(self, old_sim_speed: float, sim_speed: float) -> None:
        self.query_one("#simulation_speed", Label).update(f"{sim_speed:.1f}x")
        self.old_sim_speed = old_sim_speed

    def action_pause_sim(self) -> None:
        self.sim_speed = 0.0

    def action_play_sim(self) -> None:
        self.sim_speed = self.old_sim_speed

    @on(Button.Pressed, "#speed_decrease_button")
    def decrease_speed(self) -> None:
        self.sim_speed -= 0.1

    @on(Button.Pressed, "#speed_increase_button")
    def increase_speed(self) -> None:
        self.sim_speed += 0.1

    def check_action(self, action: str, _: tuple[object, ...]) -> bool | None:
        if action == "decrease_sim_speed" and self.sim_speed <= 0.0:
            return None
        if action == "increase_sim_speed" and self.sim_speed >= 2.0:
            return None
        if action == "pause_sim":
            return self.sim_speed != 0.0
        if action == "play_sim":
            return self.sim_speed == 0.0
        return True

    action_decrease_sim_speed = decrease_speed
    action_increase_sim_speed = increase_speed


class DebugTelemetry(Static):
    """Collapsible panel for displaying debug telemetry data."""

    airbrakes: AirbrakesContext
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
        yield Label("IMU Queue Size: ", id="imu_queue_size", expand=True)
        yield Label("Convergence Time: ", id="apogee_convergence_time")
        yield Label("Convergence Height: ", id="alt_at_convergence")
        yield Label("Pred. Apogee at Convergence: ", id="apogee_at_convergence")
        yield Label("Fetched packets: ", id="fetched_packets")
        yield Label("Log buffer size: ", id="log_buffer_size")
        yield Label("CPU Usage: ", id="cpu_usage")

    def initialize_widgets(self, airbrakes: AirbrakesContext) -> None:
        self.airbrakes = airbrakes

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

    def update_debug_telemetry(self) -> None:
        self.imu_queue_size = self.airbrakes.imu._data_queue.qsize()
        self.log_buffer_size = len(self.airbrakes.logger._log_buffer)
        self.apogee = self.airbrakes.apogee_predictor.apogee
        self.fetched_packets = len(self.airbrakes.imu_data_packets)
        self.state = self.airbrakes.state.name
        # self.cpu_usage = cpu_usage


class FlightTelemetry(Static):
    """Panel displaying real-time flight information."""

    airbrakes: AirbrakesContext
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

    def initialize_widgets(self, airbrakes: AirbrakesContext) -> None:
        self.airbrakes = airbrakes

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

    def update_flight_telemetry(self) -> None:
        self.vertical_velocity = self.airbrakes.data_processor.vertical_velocity
        self.max_vertical_velocity = self.airbrakes.data_processor.max_vertical_velocity
        self.current_height = self.airbrakes.data_processor.current_altitude
        self.max_height = self.airbrakes.data_processor.max_altitude
        self.apogee_prediction = self.airbrakes.apogee_predictor.apogee
        self.airbrakes_extension = self.airbrakes.current_extension.value
