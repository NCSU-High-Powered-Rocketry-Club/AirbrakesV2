"""Module which contains the Servo class, representing a servo motor that controls the extension of the airbrakes."""

import gpiozero


class Servo:
    """
    A custom class that represents a servo motor, controlling the extension of the airbrakes.
    """

    __slots__ = ("current_extension", "max_extension", "min_extension", "servo")

    def __init__(self, gpio_pin_number: int, min_extension: float, max_extension: float, pin_factory=None):
        self.min_extension = min_extension
        self.max_extension = max_extension
        self.current_extension = 0.0

        # Sets up the servo with the specified GPIO pin number
        # For this to work, you have to run the pigpio daemon on the Raspberry Pi (sudo pigpiod)
        if pin_factory is None:
            gpiozero.Device.pin_factory = gpiozero.pins.pigpio.PiGPIOFactory()
        else:
            gpiozero.Device.pin_factory = pin_factory
        self.servo = gpiozero.Servo(gpio_pin_number)

    def set_extension(self, extension: float):
        """
        Sets the extension of the servo.
        :param extension: The extension of the servo, between 0 and 1.
        """

        # Clamps the extension value to be within the specified range
        extension = min(1.0, max(0.0, extension))

        # Converts the extension from 0 to 1 to the actual extension range
        self.current_extension = extension * (self.max_extension - self.min_extension) + self.min_extension

        # Sets the servo extension
        self.servo.value = self.current_extension
