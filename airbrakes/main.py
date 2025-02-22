"""The main file which will be run on the Raspberry Pi. It will create the AirbrakesContext object
and run the main loop."""

import argparse
import sys
import time

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.constants import (
    ENCODER_PIN_A,
    ENCODER_PIN_B,
    IMU_PORT,
    LOGS_PATH,
    SERVO_1_CHANNEL,
    SERVO_2_CHANNEL,
)
from airbrakes.hardware.camera import Camera
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from airbrakes.interfaces.base_imu import BaseIMU
from airbrakes.interfaces.base_servo import BaseServo
from airbrakes.mock.display import FlightDisplay
from airbrakes.mock.mock_camera import MockCamera
from airbrakes.mock.mock_imu import MockIMU
from airbrakes.mock.mock_logger import MockLogger
from airbrakes.mock.mock_servo import MockServo
from airbrakes.simulation.sim_imu import SimIMU
from airbrakes.telemetry.apogee_predictor import ApogeePredictor
from airbrakes.telemetry.data_processor import IMUDataProcessor
from airbrakes.telemetry.logger import Logger
from airbrakes.utils import arg_parser


def run_real_flight() -> None:
    """Entry point for the application to run the real flight. Entered when run with
    `uv run real` or `uvx --from git+... real`."""
    # Modify sys.argv to include `real` as the first argument:
    sys.argv.insert(1, "real")
    args = arg_parser()
    run_flight(args)


def run_mock_flight() -> None:
    """Entry point for the application to run the mock flight. Entered when run with
    `uvx --from git+... mock` or `uv run mock`."""
    # Modify sys.argv to include `mock` as the first argument:
    sys.argv.insert(1, "mock")
    args = arg_parser()
    run_flight(args)


def run_sim_flight() -> None:
    """Entry point for the application to run the sim flight. Entered when run with
    `uvx --from git+... sim` or `uv run sim`."""
    # Modify sys.argv to include `sim` as the first argument:
    sys.argv.insert(1, "sim")
    args = arg_parser()
    run_flight(args)


def run_flight(args: argparse.Namespace) -> None:
    """
    Initializes the Airbrakes components and starts the main loop.
    :param args: Command line arguments determining the program configuration.
    """
    mock_time_start = time.time()

    servo, imu, camera, logger, data_processor, apogee_predictor = create_components(args)
    # Initialize the Airbrakes Context and display
    context = AirbrakesContext(servo, imu, camera, logger, data_processor, apogee_predictor)
    flight_display = FlightDisplay(context, mock_time_start, args)

    # Run the main flight loop
    run_flight_loop(context, flight_display, args.mode == "mock", args.mode == "sim")


def create_components(
    args: argparse.Namespace,
) -> tuple[BaseServo, BaseIMU, Camera, Logger, IMUDataProcessor, ApogeePredictor]:
    """
    Creates the system components needed for the air brakes system. Depending on its arguments, it
        will return either mock, sim, or real components.
    :param args: Command line arguments determining the program configuration.
    :return: A tuple containing the Servo, IMU, Camera, Logger, IMUDataProcessor, and
        ApogeePredictor objects.
    """
    if args.mode in ("mock", "sim"):
        if args.real_imu:
            # Use real IMU but with other mock components:
            imu = IMU(IMU_PORT)

        elif args.mode == "mock":
            # Replace hardware with mock objects for simulation
            imu = MockIMU(
                real_time_replay=not args.fast_replay,
                log_file_path=args.path,
            )
        else:
            # Use simulation IMU
            imu = SimIMU(sim_type=args.preset, real_time_replay=not args.fast_replay)

        # If using a real servo, use the real servo object, otherwise use a mock servo object
        servo = (
            Servo(SERVO_1_CHANNEL, SERVO_2_CHANNEL, ENCODER_PIN_A, ENCODER_PIN_B)
            if args.real_servo
            else MockServo(
                ENCODER_PIN_A,
                ENCODER_PIN_B,
            )
        )
        logger = MockLogger(LOGS_PATH, delete_log_file=not args.keep_log_file)
        camera = Camera() if args.real_camera else MockCamera()

    else:
        # Use real hardware components
        servo = Servo(SERVO_1_CHANNEL, SERVO_2_CHANNEL, ENCODER_PIN_A, ENCODER_PIN_B)
        imu = IMU(IMU_PORT)
        logger = Logger(LOGS_PATH)
        camera = Camera()

    # the mock replay, simulation, and real Airbrakes program configuration will all
    # use the IMUDataProcessor class and the ApogeePredictor class. There are no mock versions of
    # these classes.
    data_processor = IMUDataProcessor()
    apogee_predictor = ApogeePredictor()
    return servo, imu, camera, logger, data_processor, apogee_predictor


def run_flight_loop(
    context: AirbrakesContext,
    flight_display: FlightDisplay,
    is_mock: bool,
    is_sim: bool,
) -> None:
    """
    Main flight control loop that runs until shutdown is requested or interrupted.
    :param context: The AirbrakesContext managing the state machine.
    :param flight_display: Display interface for flight data.
    :param is_mock: Whether running in mock replay mode.
    :param is_sim: Whether running in simulation mode.
    """
    try:
        # Starts the air brakes system and display
        context.start()
        flight_display.start()

        while True:
            # Update the state machine
            context.update()

            # See https://github.com/python/cpython/issues/130279 for why this is here and not
            # in the loop condition.
            if context.shutdown_requested:
                break

            # Stop the replay when the data is exhausted
            if is_mock and not context.imu.is_running:
                break
            # This allows the simulation to know whether air brakes are deployed or not, and
            # change the drag coefficient and reference area used
            if is_sim:
                context.imu.set_airbrakes_status(context.servo.current_extension)

    # Handle user interrupt gracefully
    except KeyboardInterrupt:
        if is_mock:
            flight_display.end_mock_interrupted.set()
    else:
        # This is run if we have landed, the landed buffer is reached, and the program is not
        # interrupted (see state.py)
        if is_mock:
            flight_display.end_mock_natural.set()
    finally:
        # Stops the display and the Airbrakes program
        flight_display.stop()
        context.stop()


if __name__ == "__main__":
    # Legacy way to run the program:
    # python -m airbrakes.main [ARGS]

    # Command line args (after these are run, you can press Ctrl+C to exit the program):
    # python -m airbrakes.main real -v: Run a real flight with the display showing much more data
    # python -m airbrakes.main mock: Runs a mock replay on your computer
    # python -m airbrakes.main mock -r: Runs a mock replay on your computer with the real servo
    # python -m airbrakes.main mock -l: Runs a mock replay on your computer and keeps the log file
    #   after the mock replay stops
    # python -m airbrakes.main mock -f: Runs a mock replay on your computer at full speed
    # python -m airbrakes.main mock -d: Runs a mock replay on your computer in debug
    #   mode (w/o display)
    # python -m airbrakes.main mock -c: Runs a mock replay on your computer with the real camera
    # python -m airbrakes.main mock -p [path]: Runs a mock replay on your computer using the
    #   launch data at the path specified after -p
    args = arg_parser()
    run_flight(args)
