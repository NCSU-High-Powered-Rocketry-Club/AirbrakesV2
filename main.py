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
    # Create the objects that will be used in the airbrakes context
    if is_simulation:
        imu = MockIMU(SIMULATION_LOG_PATH, real_time_simulation=True)
        servo = Servo(SERVO_PIN) if real_servo else Servo(SERVO_PIN, pin_factory=MockFactory(pin_class=MockPWMPin))
    else:
        servo = Servo(SERVO_PIN)
        imu = IMU(PORT, FREQUENCY)

    logger = Logger(LOGS_PATH)
    data_processor = IMUDataProcessor([], UPSIDE_DOWN)

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
            airbrakes.update()

            if is_simulation:
                #update_display(airbrakes, sim_time_start, all_processes)
                pass
    except KeyboardInterrupt:
        pass
    finally:
        airbrakes.stop()  # Stop the IMU and logger processes


if __name__ == "__main__":
    # If the mock argument is passed in, then run the simulation: python main.py mock
    main(len(sys.argv) > 1 and MOCK_ARGUMENT in sys.argv[1:], len(sys.argv) > 1 and REAL_SERVO_ARGUMENT in sys.argv[1:])
