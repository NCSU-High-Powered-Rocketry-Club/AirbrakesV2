"""The main file which will be run on the Raspberry Pi. It will create the AirbrakesContext object and run the main
loop."""

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.data_handling.logger import Logger
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from constants import FREQUENCY, LOGS_PATH, MAX_EXTENSION, MIN_EXTENSION, PORT, SERVO_PIN


def main():
    logger = Logger(LOGS_PATH)
    servo = Servo(SERVO_PIN, MIN_EXTENSION, MAX_EXTENSION)
    imu = IMU(PORT, FREQUENCY)

    # The context that will manage the airbrakes state machine
    airbrakes = AirbrakesContext(logger, servo, imu)

    # Start the IMU and logger processes:
    airbrakes.start()

    # This is the main loop that will run until the stop method on the airbrakes is called
    while not airbrakes.shutdown_requested:
        airbrakes.update()

    # Shutdown the IMU and logger processes:
    airbrakes.stop()


if __name__ == "__main__":
    main()
