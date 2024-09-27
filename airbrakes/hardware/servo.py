"""Module which contains the Servo class, representing a servo motor that controls the extension of the airbrakes."""
import threading
import time

import gpiozero

from constants import SERVO_DELAY, ServoExtension


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

    def set_extended(self) -> None:
        """
        Extends the servo to the maximum extension.
        """
        thread = threading.Thread(target=self._extend_then_no_buzz)
        thread.start()

    def set_retracted(self) -> None:
        """
        Retracts the servo to the minimum extension.
        """
        thread = threading.Thread(target=self._retract_then_no_buzz)
        thread.start()

    def _extend_then_no_buzz(self) -> None:
        """
        Extends the servo then stops buzzing. This extends the servo to the maximum extension, waits for the servo to
        reach the physical end of the air brakes, and then sets its extension to its actual extension.
        """
        self._set_extension(ServoExtension.MAX_EXTENSION)
        time.sleep(SERVO_DELAY)
        self._set_extension(ServoExtension.MAX_NO_BUZZ)

    def _retract_then_no_buzz(self) -> None:
        """
        Retracts the servo then stops buzzing. This retracts the servo to the minimum extension, waits for the servo to
        reach the physical end of the air brakes, and then sets its extension to its actual extension.
        """
        self._set_extension(ServoExtension.MIN_EXTENSION)
        time.sleep(SERVO_DELAY)
        self._set_extension(ServoExtension.MIN_NO_BUZZ)

    def _set_extension(self, extension: ServoExtension) -> None:
        """
        Sets the extension of the servo.
        :param extension: The extension of the servo, there are 4 possible values, see constants.
        """
        # Sets the servo extension
        self.servo.value = extension.value
