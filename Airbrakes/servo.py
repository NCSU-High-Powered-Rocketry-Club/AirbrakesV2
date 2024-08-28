import RPi.GPIO as GPIO

class Servo:
    """
    Represents a servo that controls the extension of the airbrakes.
    """

    def __init__(self, servo_pin, closed_duty, open_duty):
        self.servo_pin = servo_pin
        GPIO.setwarnings(False)  # disable warnings
        GPIO.setmode(GPIO.BOARD)  # set pin numbering system

        # set the servo pin to output
        GPIO.setup(self.servo_pin, GPIO.OUT)

        # create PWM instance with frequency
        self.pi_pwm = GPIO.PWM(self.servo_pin, 50)

        # start PWM of required Duty Cycle
        self.pi_pwm.start(0)

        # minimum duty cycle for left stop (determined with trial and error)
        self.servo_closed_duty = closed_duty  # 3.5
        # maximum duty cycle for right stop (determined with trial and error)
        self.servo_open_duty = open_duty  # 11.5

        self.command = 0.0

    def set_extension(self, extension: float):
        """
        Sets the extension of the servo from 0.0 to 1.0 (0 being the airbrakes fully retracted, 1 the airbrakes fully
        extended).
        """
        command = extension
        if command > 1:
            command = 1.0
        if command < 0:
            command = 0.0

        self.command = command
        self.pi_pwm.ChangeDutyCycle(
            self.servo_closed_duty * (1.0 - command)
            + (self.servo_open_duty * command)
        )
