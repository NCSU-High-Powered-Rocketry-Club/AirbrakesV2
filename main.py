from Airbrakes.airbrakes import AirbrakesContext
from Airbrakes.imu import IMU, IMUDataPacket
from Airbrakes.logger import Logger
from Airbrakes.servo import Servo


# The pin that the servo's data wire is plugged into, 32 is for the GPIO 12 pin which is used for PWM
SERVO_PIN = 32

# The duty cycle for the servo to be fully closed and fully open
CLOSED_DUTY_CYCLE = 6.3
OPEN_DUTY_CYCLE = 9.2

# Should be checked before launch
UPSIDE_DOWN = True
# The port that the IMU is connected to
PORT = "/dev/ttyACM0"
# The frequency in Hz that the IMU will be polled at
# TODO: need to do testing with imu to see how the different data packets affect logging frequency
# TODO: Potential idea is making a separate method to get raw vs est data, and then have both held in the context
FREQUENCY = 100

# The headers for the CSV file
CSV_HEADERS = ["State", "Extension"] + list(IMUDataPacket(0.0).__slots__)


def main():
    logger = Logger(CSV_HEADERS)
    servo = Servo(SERVO_PIN, CLOSED_DUTY_CYCLE, OPEN_DUTY_CYCLE)
    imu = IMU(PORT, FREQUENCY, UPSIDE_DOWN)

    # The context that will manage the airbrakes state machine
    airbrakes = AirbrakesContext(logger, servo, imu)

    # This is the main loop that will run until the shutdown method on the airbrakes is called
    while not airbrakes.shutdown_requested:
        airbrakes.update()


if __name__ == "__main__":
    main()
