"""The main file which will be run on the Raspberry Pi. It will create the AirbrakesContext object
and run the main loop."""

import argparse
import time

from gpiozero.pins.mock import MockFactory, MockPWMPin

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.logger import Logger
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from airbrakes.mock.display import FlightDisplay
from airbrakes.mock.mock_imu import MockIMU
from airbrakes.mock.mock_logger import MockLogger
from airbrakes.simulation.sim_imu import SimIMU
from constants import IMU_PORT, LOGS_PATH, SERVO_PIN
from utils import arg_parser


def create_components(args: argparse.Namespace) -> tuple[Servo, IMU, Logger]:
    """
    Creates the system components needed for the airbrakes system. Depending on its arguments, it
    will return either mock or real components.
    :param args: Command line arguments determining the configuration.
    :return: A tuple containing the servo, IMU, and logger objects.
    """
    if args.mock:
        # If we are running a mock simulation, then we will replace our hardware objects with mock
        # objects that just pretend to be the real hardware. This is useful for testing the
        # software without having to fly the rocket. MockIMU pretends to be the imu by reading
        # previous flight data from a log file
        if not args.sim:
            imu = MockIMU(
                real_time_simulation=not args.fast_simulation,
                log_file_path=args.path,
            )
        # If we are running the simulation for generating datasets, we will replace our IMU object
        # with a sim variant, similar to running a mock simulation.
        else:
            imu = SimIMU(sim_type=args.sim)
        # MockFactory is used to create a mock servo object that pretends to be the real servo
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

    return servo, imu, logger


def run_flight_loop(
    airbrakes: AirbrakesContext, flight_display: FlightDisplay, is_mock: bool, is_sim: bool
) -> None:
    """
    Main flight control loop that runs until shutdown is requested or interrupted.
    :param airbrakes: The airbrakes context managing the state machine.
    :param flight_display: Display interface for flight data.
    :param is_mock: Whether running in mock simulation mode.
    :param is_sim: Whether running in flight simulation mode.
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

            # If we are running a simulation we need to tell the data generator/sim imu what
            # the current airbrakes extension is so that it can change the Cd based on that
            # It is a bit of a hack, but it is better we do it this way rather than changing
            # the entire structure of the program
            if is_sim:
                airbrakes.imu.set_airbrakes_status(airbrakes.current_extension)

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


def main(args: argparse.Namespace) -> None:
    """
    Sets up and runs the airbrakes system.
    :param args: Command line arguments for configuration.
    """
    sim_time_start = time.time()

    # Creates the components for the airbrakes system
    servo, imu, logger = create_components(args)

    # Initialize data processing and prediction
    data_processor = IMUDataProcessor()
    apogee_predictor = ApogeePredictor()

    # Initialize the airbrakes context and display
    airbrakes = AirbrakesContext(servo, imu, logger, data_processor, apogee_predictor)
    flight_display = FlightDisplay(airbrakes, sim_time_start, args)

    # Run the main flight loop
    run_flight_loop(airbrakes, flight_display, args.mock, args.sim)


if __name__ == "__main__":
    # Command line args (after these are run, you can press Ctrl+C to exit the program):
    # python main.py -v: Shows the display with much more data
    # python main.py -m: Runs a simulation on your computer
    # python main.py -m -r: Runs a simulation on your computer with the real servo
    # python main.py -m -l: Runs a simulation on your computer and keeps the log file after the
    # simulation stops
    # python main.py -m -f: Runs a simulation on your computer at full speed
    # python main.py -m -d: Runs a simulation on your computer in debug mode (doesn't show display)
    args = arg_parser()
    main(args)
