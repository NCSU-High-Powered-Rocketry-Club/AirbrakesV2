import RPi.GPIO as GPIO

class Servo:
    """
    A class that represents a servo motor. It can be used to set the extension of the servo, which will change the
    extension of the airbrakes.
    """

    # The pin that the servo's data wire is plugged into, 32 is for the GPIO 12 pin which is used for PWM
    SERVO_PIN = 32

    # The duty cycle for the servo to be fully closed and fully open
    CLOSED_DUTY_CYCLE = 6.3
    OPEN_DUTY_CYCLE = 9.2

    def __init__(self):
        GPIO.setwarnings(False)  # Disable warnings
        GPIO.setmode(GPIO.BOARD)  # Set pin numbering system

        # Set the servo pin to output
        GPIO.setup(self.SERVO_PIN, GPIO.OUT)

        # Create PWM instance with frequency
        self.pi_pwm = GPIO.PWM(self.SERVO_PIN, 50)

        # Start PWM of required Duty Cycle
        self.pi_pwm.start(0)

        self.extension = 0.0

    def set_extension(self, extension: float):
        """
        Sets the extension of the servo, which will change the extension of the airbrakes.
        :param extension: the extension of the servo, between 0 and 1
        """
        # Makes sure the extension is between 0 and 1
        self.extension = max(0.0, min(extension, 1.0))

        # Sets the duty cycle of the servo to be a linear interpolation between the closed and open duty cycles
        self.pi_pwm.ChangeDutyCycle(
            self.CLOSED_DUTY_CYCLE * (1.0 - self.extension)
            + (self.OPEN_DUTY_CYCLE * self.extension)
        )
