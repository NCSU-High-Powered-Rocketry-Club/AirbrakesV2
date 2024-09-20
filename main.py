"""The main file which will be run on the Raspberry Pi. It will create the AirbrakesContext object and run the main
loop."""

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.data_handling.logger import Logger
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from constants import FREQUENCY, LOGS_PATH, MAX_EXTENSION, MIN_EXTENSION, PORT, SERVO_PIN, UPSIDE_DOWN


def main():
    logger = Logger(LOGS_PATH)
    servo = Servo(SERVO_PIN, MIN_EXTENSION, MAX_EXTENSION)
    imu = IMU(PORT, FREQUENCY, UPSIDE_DOWN)

    # The context that will manage the airbrakes state machine
    airbrakes = AirbrakesContext(logger, servo, imu)
    try:
        airbrakes.start()  # Start the IMU and logger processes
        # This is the main loop that will run until we press Ctrl+C
        while not airbrakes.shutdown_requested:
            airbrakes.update()
    except KeyboardInterrupt:
        pass
    finally:
        airbrakes.stop()  # Stop the IMU and logger processes


if __name__ == "__main__":
    main()
