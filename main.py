"""The main file which will be run on the Raspberry Pi. It will create the AirbrakesContext object and run the main
loop."""

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
from constants import (
    FREQUENCY,
    LOGS_PATH,
    PORT,
    SERVO_PIN,
)
from utils import arg_parser


def main(args: argparse.Namespace) -> None:
    """
    The main function that will be run when the program is started. It will create the objects that will be used in the
    airbrakes context and run the main loop. The main loop will run until the user presses Ctrl+C.

    Depending on its arguments, it will run the program in simulation mode or not. If it is running in simulation mode,
    it will replace the hardware objects with mock objects that pretend to be the real hardware.

    :param args: Contains the command line arguments that the user passed to the program. See
        :func:`utils.arg_parser` in utils.py to know what arguments are available.
    """
    # Create the objects that will be used in the airbrakes context
    sim_time_start = time.time()

    if args.mock:
        # If we are running a simulation, then we will replace our hardware objects with mock objects that just pretend
        # to be the real hardware. This is useful for testing the software without having to fly the rocket.
        # MockIMU pretends to be the imu by reading previous flight data from a log file
        imu = MockIMU(args.path, real_time_simulation=not args.fast_simulation, start_after_log_buffer=True)
        # MockFactory is used to create a mock servo object that pretends to be the real servo
        servo = Servo(SERVO_PIN) if args.real_servo else Servo(SERVO_PIN, pin_factory=MockFactory(pin_class=MockPWMPin))
        logger = MockLogger(LOGS_PATH, delete_log_file=not args.keep_log_file)
    else:
        # If we are not running a simulation, then we will use the real hardware objects
        servo = Servo(SERVO_PIN)
        imu = IMU(PORT, FREQUENCY)
        logger = Logger(LOGS_PATH)

    # Our data processing and apogee prediction stay the same regardless of whether we are running a simulation or not
    data_processor = IMUDataProcessor()
    apogee_predictor = ApogeePredictor()

    # The context that will manage the airbrakes state machine
    airbrakes = AirbrakesContext(servo, imu, logger, data_processor, apogee_predictor)

    flight_display = FlightDisplay(airbrakes=airbrakes, start_time=sim_time_start)

    try:
        airbrakes.start()  # Start the IMU and logger processes

        # Setup our flight display, only for mock sims:
        # Don't print the flight data if we are in debug mode
        if args.mock and not args.debug:
            # This is what prints the flight data to the console in real time, we only do
            # it when running the sim because printing a lot of things can significantly slow down the program
            flight_display.start()

        # This is the main loop that will run until we press Ctrl+C
        while not airbrakes.shutdown_requested:
            # Update the airbrakes finite state machine
            airbrakes.update()

            # Stop the sim when the data is exhausted:
            if args.mock and not airbrakes.imu._data_fetch_process.is_alive():
                break
    except KeyboardInterrupt:
        if args.mock:
            flight_display.end_sim_interrupted.set()
    else:  # This is run if we have landed and the program is not interrupted (see state.py)
        if args.mock:
            # Usually the mock sim will stop itself due to data exhaustion, so we will actually
            # hit the condition above, but if the data isn't exhausted, we will stop it here.
            flight_display.end_sim_natural.set()
    finally:
        if args.mock and not args.debug:
            flight_display.stop()
        airbrakes.stop()


if __name__ == "__main__":
    # Command line args:
    # python main.py -m: Runs a simulation on your computer.
    # python main.py -m -r: Runs a simulation on your computer with the real servo.
    # python main.py -m -l: Runs a simulation on your computer and keeps the log file after the simulation stops.
    # python main.py -m -f: Runs a simulation on your computer at full speed.
    # python main.py -m -d: Runs a simulation on your computer in debug mode.
    args = arg_parser()  # Load all command line options
    main(args)
