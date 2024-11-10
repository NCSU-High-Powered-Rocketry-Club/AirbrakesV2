"""Module which contains the Servo class, representing a servo motor that controls the extension of
the airbrakes."""

import gpiozero

from constants import ServoExtension


class Servo:
    """
    A custom class that represents a servo motor, controlling the extension of the airbrakes. The
    servo is controlled using the gpiozero library, which provides a simple interface for
    controlling GPIO pins on the Raspberry Pi.
    """

    __slots__ = ("current_extension", "servo")

    def __init__(self, gpio_pin_number: int, pin_factory=None) -> None:
        """
        Initializes the servo object with the specified GPIO pin number.
        :param gpio_pin_number: The GPIO pin number that the servo is connected to.
        :param pin_factory: The pin factory to use for controlling the GPIO pins. If None, the
            default PiGPIOFactory from the gpiozero library is used, which is commonly used on
            Raspberry Pi for more precise servo control. The pin factory provides an abstraction
            layer that allows the Servo class to work across different hardware platforms or with
            different GPIO libraries (e.g., RPi.GPIO or pigpio).
        """
        self.current_extension: ServoExtension = ServoExtension.MIN_NO_BUZZ

        # Sets up the servo with the specified GPIO pin number
        # For this to work, you have to run the pigpio daemon on the Raspberry Pi (sudo pigpiod)
        if pin_factory is None:
            gpiozero.Device.pin_factory = gpiozero.pins.pigpio.PiGPIOFactory()
        else:
            gpiozero.Device.pin_factory = pin_factory

        self.servo = gpiozero.Servo(gpio_pin_number)

    def set_extended(self) -> None:
        """
        Extends the servo to the maximum extension.
        """
        self._set_extension(ServoExtension.MAX_EXTENSION)

    def set_retracted(self) -> None:
        """
        Retracts the servo to the minimum extension.
        """
        self._set_extension(ServoExtension.MIN_EXTENSION)

    def _set_extension(self, extension: ServoExtension) -> None:
        """
        Sets the extension of the servo.
        :param extension: The extension of the servo, there are 4 possible values, see constants.
        """
        # Sets the servo extension
        self.current_extension = extension
        self.servo.value = self.current_extension.value
