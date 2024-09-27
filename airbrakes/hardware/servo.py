"""Module which contains the Servo class, representing a servo motor that controls the extension of the airbrakes."""

import gpiozero

from constants import ServoExtension


class Servo:
    """
    A custom class that represents a servo motor, controlling the extension of the airbrakes.
    """

    __slots__ = ("current_extension", "max_extension", "max_no_buzz", "min_extension", "min_no_buzz", "servo")

    def __init__(self, gpio_pin_number: int, max_no_buzz: float, min_extension: float, max_extension: float,
                 min_no_buzz: float, pin_factory=None):
        self.min_extension = min_extension
        self.max_extension = max_extension
        self.min_no_buzz = min_no_buzz
        self.max_no_buzz = max_no_buzz
        self.current_extension = 0.0

        # Sets up the servo with the specified GPIO pin number
        # For this to work, you have to run the pigpio daemon on the Raspberry Pi (sudo pigpiod)
        if pin_factory is None:
            gpiozero.Device.pin_factory = gpiozero.pins.pigpio.PiGPIOFactory()
        else:
            gpiozero.Device.pin_factory = pin_factory

        self.servo = gpiozero.Servo(gpio_pin_number)

    def set_extension(self, extension: ServoExtension):
        """
        Sets the extension of the servo.
        :param extension: The extension of the servo, there are 4 possible values, see constants.
        """

        # Sets the servo extension
        self.servo.value = extension.value
