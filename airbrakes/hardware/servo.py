"""Module which contains the Servo class, representing a servo motor that controls the extension of the airbrakes."""

import gpiozero

from constants import ServoExtension


class Servo:
    """
    A custom class that represents a servo motor, controlling the extension of the airbrakes.
    """

    __slots__ = ("current_extension", "servo")

    def __init__(self, gpio_pin_number: int, pin_factory=None):
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
