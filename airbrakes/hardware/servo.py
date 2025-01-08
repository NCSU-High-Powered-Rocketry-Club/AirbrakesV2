"""Module which contains the Servo class, representing a servo motor that controls the extension of
the airbrakes."""

import threading
import warnings

import gpiozero

from airbrakes.constants import SERVO_DELAY_SECONDS, ServoExtension


class Servo:
    """
    A custom class that represents a servo motor, controlling the extension of the airbrakes. The
    servo is controlled using the gpiozero library, which provides a simple interface for
    controlling GPIO pins on the Raspberry Pi.
    """

    __slots__ = ("_go_to_max_no_buzz", "_go_to_min_no_buzz", "current_extension", "servo")

    def __init__(self, gpio_pin_number: int, pin_factory=None) -> None:
        """
        Initializes the servo object with the specified GPIO pin.
        :param gpio_pin_number: The GPIO pin that the servo is connected to.
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
            warnings.filterwarnings(message="To reduce servo jitter", action="ignore")
            gpiozero.Device.pin_factory = pin_factory

        self.servo = gpiozero.Servo(gpio_pin_number,initial_value=ServoExtension.MIN_NO_BUZZ.value)

        # We have to use threading to avoid blocking the main thread because our extension methods
        # need to run at a specific time. Yes this is bad practice but we had a mechanical issue and
        # we had to fix it in code.
        self._go_to_max_no_buzz = threading.Timer(SERVO_DELAY_SECONDS, self._set_max_no_buzz)
        self._go_to_min_no_buzz = threading.Timer(SERVO_DELAY_SECONDS, self._set_min_no_buzz)

    def set_extended(self) -> None:
        """
        Extends the servo to the maximum extension. Starts a timer to stop the buzzing after the
        servo reaches the maximum extension.
        """
        # If we are already going to the minimum extension, we cancel that operation before
        # extending the servo.
        self._go_to_min_no_buzz.cancel()

        self._set_extension(ServoExtension.MAX_EXTENSION)

        # Creates a timer to stop the buzzing after the servo reaches the maximum extension
        self._go_to_max_no_buzz = threading.Timer(SERVO_DELAY_SECONDS, self._set_max_no_buzz)
        self._go_to_max_no_buzz.start()

    def set_retracted(self) -> None:
        """
        Retracts the servo to the minimum extension. Starts a timer to stop the buzzing after the
        servo reaches the minimum extension.
        """
        # If we are already going to the maximum extension, we cancel that operation before
        # retracting the servo.
        self._go_to_max_no_buzz.cancel()

        self._set_extension(ServoExtension.MIN_EXTENSION)

        # Creates a timer to stop the buzzing after the servo reaches the minimum extension
        self._go_to_min_no_buzz = threading.Timer(SERVO_DELAY_SECONDS, self._set_min_no_buzz)
        self._go_to_min_no_buzz.start()

    def _set_max_no_buzz(self) -> None:
        """
        Extends the servo to the stop buzz position. This extends the servo such that it reaches
        the physical end of the airbrakes, and then sets its extension to its actual extension.
        """
        self._set_extension(ServoExtension.MAX_NO_BUZZ)

    def _set_min_no_buzz(self) -> None:
        """
        Retracts the servo to the stop buzz position. This retracts the servo such that it reaches
        the physical start of the airbrakes, and then sets its extension to its actual extension.
        """
        self._set_extension(ServoExtension.MIN_NO_BUZZ)

    def _set_extension(self, extension: ServoExtension) -> None:
        """
        Sets the extension of the servo.
        :param extension: The extension of the servo, there are 4 possible values, see constants.
        """
        self.current_extension = extension
        self.servo.value = self.current_extension.value
