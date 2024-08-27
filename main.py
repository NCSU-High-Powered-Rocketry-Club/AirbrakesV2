from Airbrakes.airbrakes import AirbrakesContext
from Airbrakes.imu import IMU
from Airbrakes.servo import Servo


def main():
    servo = Servo()
    imu = IMU()
    airbrakes = AirbrakesContext(servo, imu)

    # This is the main loop that will run until the shutdown method on the airbrakes is called
    while not airbrakes.shutdown_requested:
        airbrakes.update()


if __name__ == '__main__':
    main()

