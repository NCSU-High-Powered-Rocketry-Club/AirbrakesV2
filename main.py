"""The main file which will be run on the Raspberry Pi. It will create the AirbrakesContext object and run the main
loop."""

import sys
import time

from gpiozero.pins.mock import MockFactory, MockPWMPin

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.logger import Logger
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from airbrakes.mock.mock_imu import MockIMU
from constants import (
    FREQUENCY,
    LOGS_PATH,
    MOCK_ARGUMENT,
    PORT,
    REAL_SERVO_ARGUMENT,
    SERVO_PIN,
    SIMULATION_LOG_PATH,
    UPSIDE_DOWN,
)
from utils import prepare_process_dict, update_display


def main(is_simulation: bool, real_servo: bool) -> None:
    """
    The main function that will be run when the program is started. It will create the objects that will be used in the
    airbrakes context and run the main loop. The main loop will run until the user presses Ctrl+C.

    This function handles is what handles if the program is running in simulation mode or not.

    :param is_simulation: Whether to run the program in simulation mode or not
    :param real_servo: Whether to use the real servo or a mock servo
    """
    # Create the objects that will be used in the airbrakes context
    sim_time_start = time.time()
    if is_simulation:
        # If we are running a simulation, then we will replace our hardware objects with mock objects that just pretend
        # to be the real hardware. This is useful for testing the software without having to fly the rocket.
        # MockIMU pretends to be the imu by reading previous flight data from a log file
        imu = MockIMU(SIMULATION_LOG_PATH, real_time_simulation=True)
        # MockFactory is used to create a mock servo object that pretends to be the real servo
        servo = Servo(SERVO_PIN) if real_servo else Servo(SERVO_PIN, pin_factory=MockFactory(pin_class=MockPWMPin))
    else:
        # If we are not running a simulation, then we will use the real hardware objects
        servo = Servo(SERVO_PIN)
        imu = IMU(PORT, FREQUENCY)

    # Our logger and data processor stay the same regardless of whether we are running a simulation or not
    logger = Logger(LOGS_PATH)
    data_processor = IMUDataProcessor(UPSIDE_DOWN)

    # The context that will manage the airbrakes state machine
    airbrakes = AirbrakesContext(servo, imu, logger, data_processor)

    # Prepare the processes for monitoring in the simulation:
    if is_simulation:
        sim_time_start = time.time()
        all_processes = prepare_process_dict(airbrakes)

    try:
        airbrakes.start()  # Start the IMU and logger processes
        # This is the main loop that will run until we press Ctrl+C
        while not airbrakes.shutdown_requested:
            # Update the airbrakes finite state machine
            airbrakes.update()

            if is_simulation:
                # This is what prints the flight data to the console in real time, we only do it when running the sim
                # because printing a lot of things can significantly slow down the program
                update_display(airbrakes, sim_time_start, all_processes)
    except KeyboardInterrupt:
        pass
    finally:
        airbrakes.stop()


if __name__ == "__main__":
    # We check if the user has passed the MOCK_ARGUMENT (m) or REAL_SERVO_ARGUMENT (r) to the program
    # If you want to run a simulation on your computer (or Pi) run: python main.py m
    # If you want to run a simulation on the Pi with the servo connected run: python main.py m rs
    main(len(sys.argv) > 1 and MOCK_ARGUMENT in sys.argv[1:], len(sys.argv) > 1 and REAL_SERVO_ARGUMENT in sys.argv[1:])
