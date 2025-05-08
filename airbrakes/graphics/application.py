"""
Module to show the terminal GUI for the airbrakes system.
"""

import time
from argparse import Namespace
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import Footer
from textual.worker import Worker, WorkerState

import airbrakes.constants
from airbrakes import state
from airbrakes.constants import (
    ENCODER_PIN_A,
    ENCODER_PIN_B,
    IMU_PORT,
    LOGS_PATH,
    MOCK_DISPLAY_UPDATE_RATE,
    SERVO_1_CHANNEL,
    SERVO_2_CHANNEL,
)
from airbrakes.context import Context
from airbrakes.graphics.flight.header import FlightHeader
from airbrakes.graphics.flight.panel import FlightInformation
from airbrakes.graphics.flight.telemetry import CPUUsage
from airbrakes.graphics.screens.benchmark import BenchmarkScreen
from airbrakes.graphics.screens.launch_selector import (
    LaunchOptions,
    LaunchSelector,
    SelectedLaunchConfiguration,
)
from airbrakes.hardware.camera import Camera
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from airbrakes.mock.extended_data_processor import ExtendedDataProcessor
from airbrakes.mock.mock_camera import MockCamera
from airbrakes.mock.mock_imu import MockIMU
from airbrakes.mock.mock_logger import MockLogger
from airbrakes.mock.mock_servo import MockServo
from airbrakes.telemetry.apogee_predictor import ApogeePredictor
from airbrakes.telemetry.data_processor import DataProcessor
from airbrakes.telemetry.logger import Logger


class AirbrakesApplication(App):
    """
    A terminal based GUI for displaying real-time flight data.
    """

    BINDINGS: ClassVar[list] = [("q", "quit", "Quit"), ("m", "main_menu", "Main Menu")]
    TITLE = "AirbrakesV2"
    SCREENS: ClassVar[dict] = {"launch_selector": LaunchSelector}
    CSS_PATH = "css/visual.tcss"

    def __init__(self, is_mock: bool, cmd_args: Namespace) -> None:
        super().__init__()
        self.theme = "catppuccin-mocha"  # Set the default (dark mode) application theme
        self.context: Context = None
        self.is_mock: bool = is_mock
        self._args = cmd_args
        self._profiled_time: float = 0.0  # Time taken to run the flight loop in benchmark mode
        self.launch_config: SelectedLaunchConfiguration = self._construct_launch_config_from_args()
        self.flight_information: FlightInformation = None
        self.flight_header: FlightHeader = None

    def on_mount(self) -> None:
        """
        Mount the launch selector screen to get the launch configuration, if the path is not
        specified.
        """
        # If the path isn't specified, don't skip the launch selector screen.
        if not self._args.path:
            self.push_screen("launch_selector", self._receive_launch_configuration)
        else:
            # If the path is specified, skip the launch selector screen.
            self._setup_application()

    def on_unmount(self) -> None:
        """
        Stop the airbrakes system when the app is unmounted.
        """
        if self.context:
            self.context.stop()

    def start(self) -> None:
        """
        Starts the flight display.

        Starts a different kind of flight loop depending on the launch configuration.
        """
        # Initialize the airbrakes context and display
        self.context.start()

        # Run normally, updating the display:
        if not self.launch_config.benchmark_mode:
            self.query_one(CPUUsage).start()
            self.run_worker(
                self.run_replay_flight_loop, name="Flight Loop", exclusive=True, thread=True
            )
        elif self.launch_config.benchmark_mode:
            # In benchmark mode, enforce blocking the entire display and run the flight only.
            # The 0.1 second delay is to allow the button to update its text:
            self.set_timer(0.1, self.run_benchmark_flight_loop)
        else:
            ...  # implement uv run real flight loop

    def stop(self) -> None:
        """
        Stops the flight display.
        """
        if not self.context:
            return

        self.context.stop()
        if not self.launch_config.benchmark_mode:
            self.query_one(CPUUsage).stop()

    def show_benchmark_results(self) -> None:
        """
        Shows the benchmark results after the flight is finished.
        """
        self.push_screen(
            BenchmarkScreen(self.context, self._profiled_time, self.launch_config.selected_launch)
        )

    def action_main_menu(self) -> None:
        """
        Returns to the main menu.
        """
        self.stop()
        # Reset the widgets to their initial state.
        self.reset_widgets()
        self.push_screen("launch_selector", self._receive_launch_configuration)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """
        Currently used to check if the main menu button should be shown on the launch selector
        screen.
        """
        if action == "main_menu" and type(self.screen) is LaunchSelector:
            return False
        return super().check_action(action, parameters)

    def create_components(self) -> None:
        """
        Create the system components needed for the airbrakes system. There are 4 possible paths.

        1. Mock replay mode with launch selector screen - used when the path isn't specified.
        2. Mock replay mode without launch selector screen - used when the path is
            specified. Purely uses command line arguments.
        3. Real flight mode - There is no launch selector screen.
        4. Sim mode - WIP, will take a long time to implement, since it is barely used.
        """
        if self.is_mock:
            imu = MockIMU(
                real_time_replay=2.0 if self.launch_config.launch_options.fast_replay else 1.0,
                log_file_path=self.launch_config.selected_launch,
            )
            logger = MockLogger(
                LOGS_PATH, delete_log_file=not self.launch_config.launch_options.keep_log_file
            )

            servo = (
                Servo(SERVO_1_CHANNEL, SERVO_2_CHANNEL, ENCODER_PIN_A, ENCODER_PIN_B)
                if self.launch_config.launch_options.real_servo
                else MockServo(
                    ENCODER_PIN_A,
                    ENCODER_PIN_B,
                )
            )
            camera = MockCamera() if not self.launch_config.launch_options.real_camera else Camera()
            data_processor = (
                ExtendedDataProcessor()
                if not self.launch_config.benchmark_mode
                else DataProcessor()
            )

        else:  # uv run real interface
            # Maybe use mock components as specified by the command line arguments:
            if self._args.mock_servo:
                servo = MockServo(
                    ENCODER_PIN_A,
                    ENCODER_PIN_B,
                )
            else:
                servo = Servo(SERVO_1_CHANNEL, SERVO_2_CHANNEL, ENCODER_PIN_A, ENCODER_PIN_B)

            camera = MockCamera() if self._args.mock_camera else Camera()
            imu = IMU(IMU_PORT)
            logger = Logger(LOGS_PATH)
            data_processor = DataProcessor()

        apogee_predictor = ApogeePredictor()

        self.context = Context(servo, imu, camera, logger, data_processor, apogee_predictor)

    def update_telemetry(self) -> None:
        """
        Updates all the reactive variables with the latest telemetry data.
        """
        self.flight_header.update_header()
        self.flight_information.update_flight_information()

    def run_replay_flight_loop(self) -> None:
        """
        Main flight control loop that runs until shutdown is requested or interrupted.

        This is used for the mock replay and sim modes.
        """
        # TODO: The below should be in the sim loop:
        # # This allows the simulation to know whether air brakes are deployed or not, and
        # # change the drag coefficient and reference area used
        # if is_sim:
        #     context.imu.set_airbrakes_status(context.servo.current_extension)

        start_time = time.monotonic()
        if not self.launch_config.benchmark_mode:
            while True:
                self.context.update()

                # See https://github.com/python/cpython/issues/130279 for why this is here and not
                # in the loop condition.
                # Stop the simulation when the data is exhausted or when shutdown is requested:
                if self.context.shutdown_requested or not self.context.imu.is_running:
                    break

                # Update the telemetry display at a fixed frequency:
                if time.monotonic() - start_time >= MOCK_DISPLAY_UPDATE_RATE:
                    self.call_from_thread(self.update_telemetry)
                    start_time = time.monotonic()

    def run_benchmark_flight_loop(self) -> None:
        """
        Flight loop which runs in benchmark mode.

        This ensures that no control is given to Textual, and not a single display element is
        updated, even in the background, only the flight loop is run.
        """
        start_profile_time = time.perf_counter()
        # In benchmark mode, we don't need to update the display, so just run the loop
        # until the data is exhausted:
        while True:
            self.context.update()

            # Stop the simulation when the data is exhausted or when shutdown is requested:
            if self.context.shutdown_requested or not self.context.imu.is_running:
                break
        self._profiled_time = time.perf_counter() - start_profile_time

        self.stop()
        self.show_benchmark_results()

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """
        Used to shut down the airbrakes system when the data is exhausted.
        """
        if event.worker.name == "Flight Loop" and event.state == WorkerState.SUCCESS:
            self.stop()

    def compose(self) -> ComposeResult:
        """
        Create the layout of the app.
        """
        with Grid(id="main-grid"):
            self.flight_header = FlightHeader(id="flight-header")
            self.flight_information = FlightInformation(id="flight-information-panel")
            yield self.flight_header
            yield self.flight_information
        yield Footer()

    def _change_sim_speed(self, sim_speed: float) -> None:
        self.context.imu._sim_speed_factor.value = sim_speed

    def _monitor_flight_time(self, flight_time_ns: int) -> None:
        """
        Updates the graphs when the time changes.
        """
        self.flight_information.flight_graph.update_data(flight_time_ns)

    def _assign_target_apogee(self) -> None:
        """
        Assigns the target apogee to the airbrakes system.
        """
        if self.launch_config.launch_options.target_apogee is None:
            # If no target apogee is specified, e.g. when bypassing the launch selector screen,
            # get the target apogee from the metadata:
            self.launch_config.launch_options.target_apogee = self.context.imu.file_metadata[
                "flight_data"
            ]["target_apogee_meters"]

        airbrakes.constants.TARGET_APOGEE_METERS = self.launch_config.launch_options.target_apogee
        # This updates the target apogee in the state machine, so you don't have to use
        # constants.TARGET_APOGEE_METERS directly in state.py.
        state.__dict__["TARGET_APOGEE_METERS"] = self.launch_config.launch_options.target_apogee

    def _receive_launch_configuration(self, launch_config: SelectedLaunchConfiguration) -> None:
        """
        Receives the launch configuration from the launch selector screen.
        """
        self.launch_config = launch_config
        self._setup_application()

    def on_launch_selector_send_config(self, event: LaunchSelector.SendConfig) -> None:
        """
        Used when the benchmark mode button is pressed.
        """
        self.launch_config = event.launch_config
        self._setup_application()

    def _construct_launch_config_from_args(self) -> SelectedLaunchConfiguration:
        """
        Constructs the launch configuration from the command line arguments.
        """
        return SelectedLaunchConfiguration(
            selected_launch=self._args.path,
            launch_options=LaunchOptions(
                real_servo=self._args.real_servo,
                real_camera=self._args.real_camera,
                fast_replay=self._args.fast_replay,
                keep_log_file=self._args.keep_log_file,
                target_apogee=self._args.target_apogee,
            ),
            benchmark_mode=self._args.bench,
        )

    def _setup_application(self) -> None:
        """
        Common setup code for initializing widgets and starting the application.
        """
        self.create_components()
        self._assign_target_apogee()

        if not self.launch_config.benchmark_mode:
            self.initialize_widgets()
            self.watch(self.query_one("#sim-speed-panel"), "sim_speed", self._change_sim_speed)
            self.watch(self.flight_header, "t_zero_time_ns", self._monitor_flight_time, init=False)

        self.start()

    def initialize_widgets(self) -> None:
        """
        Supplies the airbrakes context and related objects to the widgets for proper operation.
        """
        self.flight_header.initialize_widgets(self.context, self.is_mock)
        self.flight_information.initialize_widgets(self.context)

    def reset_widgets(self) -> None:
        """
        Resets the widgets to their initial state.
        """
        self.flight_header.reset_widgets()
        self.flight_information.reset_widgets()
