"""The main file which will be run on the Raspberry Pi. It will create the AirbrakesContext object
and run the main loop."""

import argparse
import time

from gpiozero.pins.mock import MockFactory, MockPWMPin

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.constants import IMU_PORT, LOGS_PATH, SERVO_PIN
from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.logger import Logger
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from airbrakes.mock.display import FlightDisplay
from airbrakes.mock.mock_imu import MockIMU
from airbrakes.mock.mock_logger import MockLogger
from airbrakes.simulation.sim_imu import SimIMU
from airbrakes.utils import arg_parser


def run_real_flight() -> None:
    """Entry point for the application to run the real flight. Entered when run with
    `uv run real` or `uvx --from git+... real`."""
    args = arg_parser()
    run_flight(args)


def run_mock_flight() -> None:
    """Entry point for the application to run the mock flight. Entered when run with
    `uvx --from git+... mock` or `uv run mock`."""
    args = arg_parser(mock_invocation=True)
    run_flight(args)


def run_flight(args: argparse.Namespace) -> None:
    sim_time_start = time.time()

    servo, imu, logger, data_processor, apogee_predictor = create_components(args)
    # Initialize the airbrakes context and display
    airbrakes = AirbrakesContext(servo, imu, logger, data_processor, apogee_predictor)
    flight_display = FlightDisplay(airbrakes, sim_time_start, args)

    # Run the main flight loop
    run_flight_loop(airbrakes, flight_display, args.mock)


def create_components(
    args: argparse.Namespace,
) -> tuple[Servo, IMU, Logger, IMUDataProcessor, ApogeePredictor]:
    """
    Creates the system components needed for the airbrakes system. Depending on its arguments, it
    will return either mock or real components.
    :param args: Command line arguments determining the configuration.
    :return: A tuple containing the servo, IMU, Logger, data processor, and apogee predictor objects
    """
    if args.mock:
        # Replace hardware with mock objects for simulation
        if args.sim:
            imu = SimIMU(sim_type=args.sim, real_time_simulation=not args.fast_simulation)
        else:
            imu = MockIMU(
                real_time_simulation=not args.fast_simulation,
                log_file_path=args.path,
            )
        # If using a real servo, use the real servo object, otherwise use a mock servo object
        servo = (
            Servo(SERVO_PIN)
            if args.real_servo
            else Servo(SERVO_PIN, pin_factory=MockFactory(pin_class=MockPWMPin))
        )
        logger = MockLogger(LOGS_PATH, delete_log_file=not args.keep_log_file)
    else:
        # Use real hardware components
        servo = Servo(SERVO_PIN)
        imu = IMU(IMU_PORT)
        logger = Logger(LOGS_PATH)

    # Initialize data processing and prediction
    data_processor = IMUDataProcessor()
    apogee_predictor = ApogeePredictor()
    return servo, imu, logger, data_processor, apogee_predictor


def run_flight_loop(
    airbrakes: AirbrakesContext, flight_display: FlightDisplay, is_mock: bool
) -> None:
    """
    Main flight control loop that runs until shutdown is requested or interrupted.
    :param airbrakes: The airbrakes context managing the state machine.
    :param flight_display: Display interface for flight data.
    :param is_mock: Whether running in simulation mode.
    """
    try:
        # Starts the airbrakes system and display
        airbrakes.start()
        flight_display.start()

        while not airbrakes.shutdown_requested:
            # Update the state machine
            airbrakes.update()

            # Stop the simulation when the data is exhausted
            if is_mock and not airbrakes.imu.is_running:
                break

    # Handle user interrupt gracefully
    except KeyboardInterrupt:
        if is_mock:
            flight_display.end_sim_interrupted.set()
    else:  # This is run if we have landed and the program is not interrupted (see state.py)
        if is_mock:
            # Stop the mock simulation naturally if not interrupted
            flight_display.end_sim_natural.set()
    finally:
        # Stop the display and airbrakes
        flight_display.stop()
        airbrakes.stop()


if __name__ == "__main__":
    # Legacy way to run the program:
    # python -m airbrakes.main [ARGS]

    # Command line args (after these are run, you can press Ctrl+C to exit the program):
    # python -m airbrakes.main -v: Shows the display with much more data
    # python -m airbrakes.main -m: Runs a simulation on your computer
    # python -m airbrakes.main -m -r: Runs a simulation on your computer with the real servo
    # python -m airbrakes.main -m -l: Runs a simulation on your computer and keeps the log file
    # after the simulation stops
    # python -m airbrakes.main -m -f: Runs a simulation on your computer at full speed
    # python -m airbrakes.main -m -d: Runs a simulation on your computer in debug mode (w/o display)
    args = arg_parser()
    run_flight(args)
