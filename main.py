"""The main file which will be run on the Raspberry Pi. It will create the AirbrakesContext object and run the main
loop."""

import sys

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
    MAX_EXTENSION,
    MIN_EXTENSION,
    MOCK_ARGUMENT,
    PORT,
    SERVO_PIN,
    SIMULATION_LOG_PATH,
    UPSIDE_DOWN,
)

# ANSI escape code for cursor movement:
MOVE_CURSOR_UP = "\033[F"  # Move the cursor one line up


def update_display(airbrakes):
    """Prints the values from the simulation in a pretty way."""
    # Print values with multiple print statements
    print(f"State:                       {airbrakes.state.name:<10}")
    print(f"Current speed:               {airbrakes.data_processor.speed:<10.2f} m/s")
    print(f"Max speed so far:            {airbrakes.data_processor.max_speed:<10.2f} m/s")
    print(f"Current altitude:            {airbrakes.data_processor.current_altitude:<10.2f} m")
    print(f"Max altitude so far:         {airbrakes.data_processor.max_altitude:<10.2f} m")
    print(f"Current airbrakes extension: {airbrakes.current_extension:<10}")

    # Move the cursor up 6 lines to overwrite the previous output
    print(MOVE_CURSOR_UP * 6, end="", flush=True)


def main(is_simulation: bool) -> None:
    # Create the objects that will be used in the airbrakes context
    if is_simulation:
        imu = MockIMU(SIMULATION_LOG_PATH, FREQUENCY)
        servo = Servo(SERVO_PIN, MIN_EXTENSION, MAX_EXTENSION, pin_factory=MockFactory(pin_class=MockPWMPin))
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
                update_display(airbrakes)

    except KeyboardInterrupt:
        pass
    finally:
        airbrakes.stop()  # Stop the IMU and logger processes


if __name__ == "__main__":
    # If the mock argument is passed in, then run the simulation: python main.py mock
    main(len(sys.argv) > 1 and MOCK_ARGUMENT in sys.argv[1:])
