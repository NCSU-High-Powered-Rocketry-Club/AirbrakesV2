"""The main file which will be run on the Raspberry Pi. It will create the AirbrakesContext object and run the main
loop."""

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.imu import IMU, IMUDataPacket
from airbrakes.logger import Logger
from airbrakes.servo import Servo

# The pin that the servo's data wire is plugged into, in this case the GPIO 12 pin which is used for PWM
SERVO_PIN = 12

# The minimum and maximum position of the servo, its range is -1 to 1
MIN_EXTENSION = -1
MAX_EXTENSION = 1

# Should be checked before launch
UPSIDE_DOWN = True
# The port that the IMU is connected to
PORT = "/dev/ttyACM0"
# The frequency in Hz that the IMU will be polled at
# TODO: need to do testing with imu to see how the different data packets affect logging frequency
# TODO: Potential idea is making a separate method to get raw vs est data, and then have both held in the context
FREQUENCY = 100

# The headers for the CSV file
CSV_HEADERS = ["State", "Extension", *list(IMUDataPacket(0.0).__slots__)]


def main():
    logger = Logger(CSV_HEADERS)
    servo = Servo(SERVO_PIN, MIN_EXTENSION, MAX_EXTENSION)
    imu = IMU(PORT, FREQUENCY, UPSIDE_DOWN)

    # The context that will manage the airbrakes state machine
    airbrakes = AirbrakesContext(logger, servo, imu)

    # This is the main loop that will run until the shutdown method on the airbrakes is called
    while not airbrakes.shutdown_requested:
        airbrakes.update()


if __name__ == "__main__":
    main()
