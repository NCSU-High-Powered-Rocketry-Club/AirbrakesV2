"""The mocked main file which can be run locally. To run this, make sure you're not inside scripts,
and run the following command: `python -m scripts.run_main_local`"""

from airbrakes.airbrakes import AirbrakesContext
from constants import FREQUENCY, LOGS_PATH, MAX_EXTENSION, MIN_EXTENSION, PORT, SERVO_PIN, UPSIDE_DOWN
from airbrakes.hardware.imu import IMU
from airbrakes.data_handling.logger import Logger
from airbrakes.hardware.servo import Servo

from gpiozero.pins.mock import MockFactory, MockPWMPin


def main():
    logger = Logger(LOGS_PATH)
    servo = Servo(SERVO_PIN, MIN_EXTENSION, MAX_EXTENSION, pin_factory=MockFactory(pin_class=MockPWMPin))
    imu = IMU(PORT, FREQUENCY, UPSIDE_DOWN)

    # The context that will manage the airbrakes state machine
    airbrakes = AirbrakesContext(logger, servo, imu)
    try:
        airbrakes.start()  # Start the IMU and logger processes
        # This is the main loop that will run until we press Ctrl+C
        while not airbrakes.shutdown_requested:
            airbrakes.update()
    except KeyboardInterrupt:  # Stop running IMU and logger if the user presses Ctrl+C
        pass
    finally:
        airbrakes.stop()  # Stop the IMU and logger processes


if __name__ == "__main__":
    main()
