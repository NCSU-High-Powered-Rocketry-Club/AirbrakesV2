"""
Module to show the terminal GUI for the airbrakes system.
"""

import time
from typing import TYPE_CHECKING, ClassVar

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
from airbrakes.graphics.launch_selector import LaunchSelector, SelectedLaunchConfiguration
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
from airbrakes.utils import arg_parser

if TYPE_CHECKING:
    from textual.timer import Timer


class AirbrakesApplication(App):
    """
    A terminal based GUI for displaying real-time flight data.
    """

    BINDINGS: ClassVar[list] = [("q", "quit", "Quit")]
    TITLE = "AirbrakesV2"
    SCREENS: ClassVar[dict] = {"launch_selector": LaunchSelector}
    CSS_PATH = "css/visual.tcss"

    def __init__(self) -> None:
        super().__init__()
        self.theme = "catppuccin-mocha"  # Set the default (dark mode) application theme
        self.context: Context = None
        self.is_mock: bool = False
        self._args = arg_parser()
        self._pre_calculated_motor_burn_time: int = None
        self.flight_information: FlightInformation = None
        self.flight_header: FlightHeader = None
        self.timer: Timer = None

    def on_mount(self) -> None:
        """
        Mount the launch selector screen to get the launch configuration.
        """
        self.push_screen("launch_selector", self.receive_launch_configuration)

    def on_unmount(self) -> None:
        """
        Stop the airbrakes system when the app is unmounted.
        """
        if self.context:
            self.context.stop()

    def receive_launch_configuration(self, launch_config: SelectedLaunchConfiguration) -> None:
        """
        Receives the launch configuration from the launch selector screen.
        """
        self.create_components(launch_config)
        self.assign_target_apogee(launch_config.desired_target_apogee)
        self.initialize_widgets()
        self.watch(self.query_one("#sim-speed-panel"), "sim_speed", self.change_sim_speed)
        self.watch(self.flight_header, "t_zero_time_ns", self.monitor_flight_time, init=False)
        self.start()

    def initialize_widgets(self) -> None:
        """
        Supplies the airbrakes context and related objects to the widgets for proper operation.
        """
        self.flight_header = self.query_one(FlightHeader)
        self.flight_information = self.query_one(FlightInformation)
        self.flight_header.initialize_widgets(self.context, self.is_mock)
        self.flight_information.initialize_widgets(self.context)

    def start(self) -> None:
        """
        Starts the flight display.
        """
        # Initialize the airbrakes context and display
        self.context.start()
        self.query_one(CPUUsage).start()
        self.run_worker(self.run_flight_loop, name="Flight Loop", exclusive=True, thread=True)

    def stop(self) -> None:
        """
        Stops the flight display.
        """
        self.context.stop()
        self.query_one(CPUUsage).stop()

    def change_sim_speed(self, sim_speed: float) -> None:
        self.context.imu._sim_speed_factor.value = sim_speed

    def create_components(self, launch_config: SelectedLaunchConfiguration) -> None:
        """
        Create the system components needed for the airbrakes system.
        """
        if launch_config.launch_options is not None:
            imu = MockIMU(
                real_time_replay=2.0 if launch_config.launch_options.fast_simulation else 1.0,
                log_file_path=launch_config.selected_button,
            )
            logger = MockLogger(
                LOGS_PATH, delete_log_file=not launch_config.launch_options.keep_log_file
            )

            servo = (
                Servo(SERVO_1_CHANNEL, SERVO_2_CHANNEL, ENCODER_PIN_A, ENCODER_PIN_B)
                if launch_config.launch_options.real_servo
                else MockServo(
                    ENCODER_PIN_A,
                    ENCODER_PIN_B,
                )
            )
            camera = MockCamera() if not launch_config.launch_options.real_camera else Camera()
            data_processor = ExtendedDataProcessor()
            self.is_mock = True
        else:
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

    def assign_target_apogee(self, target_apogee: float) -> None:
        """
        Assigns the target apogee to the airbrakes system.
        """
        airbrakes.constants.TARGET_APOGEE_METERS = target_apogee
        # This updates the target apogee in the state machine, so you don't have to use
        # constants.TARGET_APOGEE_METERS directly in state.py.
        state.__dict__["TARGET_APOGEE_METERS"] = target_apogee

    def monitor_flight_time(self, flight_time_ns: int) -> None:
        """
        Updates the graphs when the time changes.
        """
        # TODO: Refactor everything to update when the time changes.
        self.flight_information.flight_graph.update_data(flight_time_ns)

    def run_flight_loop(self) -> None:
        """
        Main flight control loop that runs until shutdown is requested or interrupted.
        """
        # TODO: Maybe make different loops for real, mock, and sim?
        # TODO: The below should be in the sim loop:
        # # This allows the simulation to know whether air brakes are deployed or not, and
        # # change the drag coefficient and reference area used
        # if is_sim:
        #     context.imu.set_airbrakes_status(context.servo.current_extension)

        start_time = time.monotonic()
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

        self.stop()

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
            yield FlightHeader(id="flight-header")
            yield FlightInformation(id="flight-information-panel")
        yield Footer()
