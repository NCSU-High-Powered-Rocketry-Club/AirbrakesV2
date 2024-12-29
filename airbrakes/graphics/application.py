"""Module to show the terminal GUI for the airbrakes system."""

from typing import TYPE_CHECKING, ClassVar

from gpiozero.pins.mock import MockFactory, MockPWMPin
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import Footer
from textual.worker import Worker, WorkerState, get_current_worker

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.logger import Logger
from airbrakes.graphics.flight.header import FlightHeader
from airbrakes.graphics.flight.panel import FlightInformation
from airbrakes.graphics.launch_selector import LaunchSelector, SelectedLaunchConfiguration
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from airbrakes.mock.mock_imu import MockIMU
from airbrakes.mock.mock_logger import MockLogger
from constants import IMU_PORT, LOGS_PATH, SERVO_PIN

if TYPE_CHECKING:
    from textual.timer import Timer


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
        self.update_timer = self.set_interval(1 / 10, self.update_telemetry, pause=True)
        self.initialize_widgets()
        self.watch(self.query_one("#sim-speed-panel"), "sim_speed", self.change_sim_speed)
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
