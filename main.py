from Airbrakes.airbrakes import AirbrakesContext
from Airbrakes.imu import IMU
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
# The frequency in which the IMU polls data in Hz
FREQUENCY = 100


def main():
    servo = Servo(SERVO_PIN, CLOSED_DUTY_CYCLE, OPEN_DUTY_CYCLE)
    imu = IMU(PORT, FREQUENCY, UPSIDE_DOWN)

    # The context that will manage the airbrakes state machine
    airbrakes = AirbrakesContext(servo, imu)

    # This is the main loop that will run until the shutdown method on the airbrakes is called
    while not airbrakes.shutdown_requested:
        airbrakes.update()


if __name__ == '__main__':
    main()
