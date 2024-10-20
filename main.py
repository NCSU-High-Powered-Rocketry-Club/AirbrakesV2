"""The main file which will be run on the Raspberry Pi. It will create the AirbrakesContext object and run the main
loop."""

import argparse
import time

from gpiozero.pins.mock import MockFactory, MockPWMPin

from airbrakes.airbrakes import AirbrakesContext
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
    SIMULATION_LOG_PATH,
    UPSIDE_DOWN,
)
from utils import arg_parser


def main(args: argparse.Namespace) -> None:
    # Create the objects that will be used in the airbrakes context
    sim_time_start = time.time()

    if args.mock:
        imu = MockIMU(SIMULATION_LOG_PATH, real_time_simulation=not args.fast_simulation, start_after_log_buffer=True)
        servo = Servo(SERVO_PIN) if args.real_servo else Servo(SERVO_PIN, pin_factory=MockFactory(pin_class=MockPWMPin))
        logger = MockLogger(LOGS_PATH, delete_log_file=not args.keep_log_file)
    else:
        servo = Servo(SERVO_PIN)
        imu = IMU(PORT, FREQUENCY)
        logger = Logger(LOGS_PATH)

    data_processor = IMUDataProcessor(UPSIDE_DOWN)

    # The context that will manage the airbrakes state machine
    airbrakes = AirbrakesContext(servo, imu, logger, data_processor)

    flight_display = FlightDisplay(airbrakes=airbrakes, start_time=sim_time_start)

    try:
        airbrakes.start()  # Start the IMU and logger processes
        # This is the main loop that will run until we press Ctrl+C
        while not airbrakes.shutdown_requested:
            airbrakes.update()

            if args.mock:
                if not args.debug:
                    flight_display.update_display()
                # Stop the sim when the data is exhausted:
                if not airbrakes.imu._data_fetch_process.is_alive():
                    flight_display.update_display(end_sim=FlightDisplay.NATURAL_END)
                    break
    except KeyboardInterrupt:
        if args.mock:
            flight_display.update_display(end_sim=FlightDisplay.INTERRUPTED_END)
    finally:
        airbrakes.stop()  # Stop the IMU and logger processes


if __name__ == "__main__":
    args = arg_parser()  # Load all command line options
    main(args)
