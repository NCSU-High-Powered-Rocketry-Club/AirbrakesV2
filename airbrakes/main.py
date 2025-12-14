"""
The main file which will be run on the Raspberry Pi.

It will create the Context object and run the main loop.
"""

import sys
import sysconfig
from typing import TYPE_CHECKING, cast

from airbrakes.constants import (
    ENCODER_PIN_A,
    ENCODER_PIN_B,
    IMU_PORT,
    LOGS_PATH,
    SERVO_CHANNEL,
)
from airbrakes.context import Context
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from airbrakes.mock.display import FlightDisplay
from airbrakes.mock.mock_imu import MockIMU
from airbrakes.mock.mock_logger import MockLogger
from airbrakes.mock.mock_servo import MockServo
from airbrakes.telemetry.apogee_predictor import ApogeePredictor
from airbrakes.telemetry.data_processor import DataProcessor
from airbrakes.telemetry.logger import Logger
from airbrakes.utils import arg_parser

if TYPE_CHECKING:
    import argparse

    from airbrakes.interfaces.base_imu import BaseIMU
    from airbrakes.interfaces.base_servo import BaseServo


def run_real_flight() -> None:
    """
    Entry point for the application to run the real flight.

    Entered when run with
    `uv run real` or `uvx --from git+... real`.
    """
    # Modify sys.argv to include real as the first argument:
    sys.argv.insert(1, "real")
    args = arg_parser()
    run_flight(args)


def run_mock_flight() -> None:
    """
    Entry point for the application to run the mock flight.

    Entered when run with
    `uvx --from git+... mock` or `uv run mock`.
    """
    # Modify sys.argv to include mock as the first argument:
    sys.argv.insert(1, "mock")
    args = arg_parser()
    run_flight(args)


def run_flight(args: argparse.Namespace) -> None:
    """
    Initializes the Airbrakes components and starts the main loop.

    :param args: Command line arguments determining the program configuration.
    """
    servo, imu, logger, data_processor, apogee_predictor = create_components(args)

    # Assert that we are running in the free-threaded build, and the GIL is disabled:
    if not bool(sysconfig.get_config_var("Py_GIL_DISABLED")) or sys._is_gil_enabled():
        raise RuntimeError(
            "The Airbrakes program must be run with the GIL disabled for performance reasons. "
            "Make sure you are using Python 3.14t, and set the environment variable `PYTHON_GIL=0`"
            " before running the program."
        )

    # Initialize the Airbrakes Context and display
    context = Context(servo, imu, logger, data_processor, apogee_predictor)
    flight_display = FlightDisplay(context, args)

    # Run the main flight loop
    run_flight_loop(context, flight_display, args.mode == "mock")


def create_components(
    args: argparse.Namespace,
) -> tuple[BaseServo, BaseIMU, Logger, DataProcessor, ApogeePredictor]:
    """
    Creates the system components needed for the air brakes system.

    Depending on its arguments, it will return either mock, or real components.
    :param args: Command line arguments determining the program configuration.
    :return: A tuple containing the Servo, IMU, Logger, IMUDataProcessor, and ApogeePredictor
        objects.
    """
    # TODO: this looks ugly but eventually we will use HPRM to run sims
    if args.mode in ("mock"):
        if args.mode == "mock":
            # Replace hardware with mock objects for simulation
            imu = MockIMU(
                real_time_replay=not args.fast_replay,
                log_file_path=args.path,
            )

        # If using a real servo, use the real servo object, otherwise use a mock servo object
        servo = (
            Servo(SERVO_CHANNEL, ENCODER_PIN_A, ENCODER_PIN_B)
            if args.real_servo
            else MockServo(
                SERVO_CHANNEL,
                ENCODER_PIN_A,
                ENCODER_PIN_B,
            )
        )
        logger = MockLogger(LOGS_PATH, delete_log_file=not args.keep_log_file)

    else:
        # Use real hardware components
        imu = IMU(IMU_PORT)
        logger = Logger(LOGS_PATH)

        # Maybe use mock components as specified by the command line arguments:
        if args.mock_servo:
            servo = MockServo(
                SERVO_CHANNEL,
                ENCODER_PIN_A,
                ENCODER_PIN_B,
            )
        else:
            servo = Servo(SERVO_CHANNEL, ENCODER_PIN_A, ENCODER_PIN_B)

    # the mock replay, simulation, and real Airbrakes program configuration will all
    # use the DataProcessor class and the ApogeePredictor class. There are no mock versions of
    # these classes.
    data_processor = DataProcessor()
    apogee_predictor = ApogeePredictor()
    return servo, imu, logger, data_processor, apogee_predictor


def run_flight_loop(
    context: Context,
    flight_display: FlightDisplay,
    is_mock: bool,
) -> None:
    """
    Main flight control loop that runs until shutdown is requested or interrupted.

    :param context: The AirbrakesContext managing the state machine.
    :param flight_display: Display interface for flight data.
    :param is_mock: Whether running in mock replay mode.
    """
    try:
        # Starts the air brakes system and display
        context.start(wait_for_start=True)
        flight_display.start()

        # Run the main loop until shutdown is requested:
        while not context.shutdown_requested:
            # Update the state machine
            context.update()

            # Stop the replay when the data is exhausted
            if is_mock and not context.imu.is_running:
                break

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
    # This code isn't actually used when running `uv run ...` but is kept for
    # backwards compatibility. In the `pyproject.toml` file, the entry points for
    # `uvx` are set to the functions above: `run_real_flight` or `run_mock_flight`

    # Deprecated way to run the program:
    # python -m airbrakes.main [ARGS]

    # The main Airbrakes program can be run in different modes:

    # `uv run real [ARGS]`: Runs the flight with real hardware. Optional arguments:
    #     -s, --mock-servo   : Uses a mock servo instead of the real one.

    # `uv run mock [ARGS]`: Runs the program in mock replay mode, using pre-recorded flight data.
    #   Optional arguments include:
    #     -s, --real-servo   : Uses the real servo instead of a mock one.
    #     -f, --fast-replay  : Runs the replay at full speed instead of real-time.
    #     -p, --path <file>  : Specifies a flight data file to use (default is the first file).

    # Global options for all modes:
    #     -d, --debug   : Runs without a display, allowing inspection of print statements.
    #     -v, --verbose : Enables a detailed display with more flight data.

    args = arg_parser()
    run_flight(args)
