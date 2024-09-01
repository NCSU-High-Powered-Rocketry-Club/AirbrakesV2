import RPi.GPIO as GPIO


class Servo:
    """
    A class that represents a servo motor. It can be used to set the extension of the servo, which will change the
    extension of the airbrakes.
    """

    def __init__(self, servo_pin: int, closed_duty_cycle: float, open_duty_cycle: float):
        self.closed_duty_cycle = closed_duty_cycle
        self.open_duty_cycle = open_duty_cycle
        self.extension = 0.0

        # Disable warnings
        GPIO.setwarnings(False)
        # Set pin numbering system
        GPIO.setmode(GPIO.BOARD)
        # Set the servo pin to output
        GPIO.setup(servo_pin, GPIO.OUT)

        # Create PWM instance with frequency
        self.pi_pwm = GPIO.PWM(servo_pin, 50)
        # Start PWM of required Duty Cycle
        self.pi_pwm.start(0)

    def set_extension(self, extension: float):
        """
        Sets the extension of the servo, which will change the extension of the airbrakes.
        :param extension: the extension of the servo, between 0 and 1
        """
        # Makes sure the extension is between 0 and 1
        self.extension = max(0.0, min(extension, 1.0))

        # Sets the duty cycle of the servo to be a linear interpolation between the closed and open duty cycles
        self.pi_pwm.ChangeDutyCycle(
            self.closed_duty_cycle * (1.0 - self.extension)
            + (self.open_duty_cycle * self.extension)
        )
