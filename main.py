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
from airbrakes.utils import update_display
from constants import (
    FREQUENCY,
    LOGS_PATH,
    MAX_EXTENSION,
    MIN_EXTENSION,
    MOCK_ARGUMENT,
    PORT,
    SERVO_PIN,
    SIMULATION_LOG_PATH,
    UPSIDE_DOWN,
)


def main(is_simulation: bool) -> None:
    # Create the objects that will be used in the airbrakes context
    if is_simulation:
        imu = MockIMU(SIMULATION_LOG_PATH, FREQUENCY)
        servo = Servo(SERVO_PIN, MIN_EXTENSION, MAX_EXTENSION, pin_factory=MockFactory(pin_class=MockPWMPin))
        sim_time_start = time.time()
        print(f"\n{'='*10} REAL TIME FLIGHT DATA {'='*10}\n")
    else:
        servo = Servo(SERVO_PIN, MIN_EXTENSION, MAX_EXTENSION)
        imu = IMU(PORT, FREQUENCY)

    logger = Logger(LOGS_PATH)
    data_processor = IMUDataProcessor([], UPSIDE_DOWN)

    # The context that will manage the airbrakes state machine
    airbrakes = AirbrakesContext(servo, imu, logger, data_processor)

    try:
        airbrakes.start()  # Start the IMU and logger processes
        # This is the main loop that will run until we press Ctrl+C
        while not airbrakes.shutdown_requested:
            airbrakes.update()

            if is_simulation:
                update_display(airbrakes, sim_time_start)

    except KeyboardInterrupt:
        pass
    finally:
        airbrakes.stop()  # Stop the IMU and logger processes


if __name__ == "__main__":
    # If the mock argument is passed in, then run the simulation: python main.py mock
    main(len(sys.argv) > 1 and MOCK_ARGUMENT in sys.argv[1:])
