"""Base class for the Servo. This will serve as the base for real servo and the mock servo."""

import threading
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import gpiozero

from airbrakes.constants import ServoExtension

if TYPE_CHECKING:
    from adafruit_motor.servo import Servo as AdafruitServo
    from gpiozero import Servo as MockedGPIOServo


class BaseServo(ABC):
    """
    A custom class that represents a servo interface and the accompanying rotary encoder interface.
    The servo controls the extension of the airbrakes while the encoder measures the servo's
    position. The encoder is controlled using the gpiozero library, which provides a simple
    interface for controlling GPIO pins on the Raspberry Pi.

    The servo we use is the DS3235, which is a coreless digital servo. This is controlled with the
    Adafruit PCA9685 PWM circuit board.
    """

    __slots__ = (
        "_go_to_max_no_buzz",
        "_go_to_min_no_buzz",
        "current_extension",
        "encoder",
        "first_servo",
        "second_servo",
    )

    def __init__(
        self,
        first_servo: "AdafruitServo | MockedGPIOServo",
        second_servo: "AdafruitServo | MockedGPIOServo",
        encoder: gpiozero.RotaryEncoder,
    ) -> None:
        """
        :param first_servo: The first servo object. Can be a real servo or a mock servo.
        :param second_servo: The second servo object. Can be a real servo or a mock servo.
        :param encoder: The rotary encoder object.
        """
        self.current_extension: ServoExtension = ServoExtension.MIN_NO_BUZZ

        self.first_servo: AdafruitServo | MockedGPIOServo = first_servo
        self.second_servo: AdafruitServo | MockedGPIOServo = second_servo

        self.encoder = encoder

        # We have to use threading to avoid blocking the main thread because our extension methods
        # need to run at a specific time. Yes this is bad practice but we had a mechanical issue and
        # we had to fix it in code.
        # self._go_to_max_no_buzz = threading.Timer(SERVO_DELAY_SECONDS, self._set_max_no_buzz)
        # self._go_to_min_no_buzz = threading.Timer(SERVO_DELAY_SECONDS, self._set_min_no_buzz)

    @abstractmethod
    def _set_max_extension(self, extension: ServoExtension) -> None:
        """
        Sets the extension of the servo.
        :param extension: The extension of the servo, there are 4 possible values, see constants.
        """
        self.current_extension = extension

    @abstractmethod
    def _set_min_extension(self, extension: ServoExtension) -> None:
        """
        Sets the extension of the servo.
        :param extension: The extension of the servo, there are 4 possible values, see constants.
        """
        self.current_extension = extension

    def set_extended(self) -> None:
        """
        Extends the servo to the maximum extension. Starts a timer to stop the buzzing after the
        servo reaches the maximum extension.
        """
        # If we are already going to the minimum extension, we cancel that operation before
        # extending the servo.
        # self._go_to_min_no_buzz.cancel()

        start_extending = threading.Thread(
            target=self._set_max_extension(ServoExtension.MAX_EXTENSION)
        )
        start_extending.start()

        # Creates a timer to stop the buzzing after the servo reaches the maximum extension.
        # self._go_to_max_no_buzz = threading.Timer(SERVO_DELAY_SECONDS, self._set_max_no_buzz)
        # self._go_to_max_no_buzz.start()

    def set_retracted(self) -> None:
        """
        Retracts the servo to the minimum extension. Starts a timer to stop the buzzing after the
        servo reaches the minimum extension.
        """
        # If we are already going to the maximum extension, we cancel that operation before
        # retracting the servo.
        # self._go_to_max_no_buzz.cancel()

        start_retracting = threading.Thread(
            target=self._set_min_extension(ServoExtension.MIN_EXTENSION)
        )
        start_retracting.start()

        # Creates a timer to stop the buzzing after the servo reaches the minimum extension
        # self._go_to_min_no_buzz = threading.Timer(SERVO_DELAY_SECONDS, self._set_min_no_buzz)
        # self._go_to_min_no_buzz.start()

    def get_encoder_reading(self) -> int:
        """
        Gets the current reading (in steps) of the rotary encoder.
        :return: The current reading of the rotary encoder
        """
        return self.encoder.steps

    # def _set_max_no_buzz(self) -> None:
    #     """
    #     Extends the servo to the stop buzz position. After the servo is extended to its maximum
    #     extension, this sets its extension to its actual extension.
    #     """
    #     self._set_extension(ServoExtension.MAX_NO_BUZZ)

    # def _set_min_no_buzz(self) -> None:
    #     """
    #     Retracts the servo to the stop buzz position. After the servo is retracted to its minimum
    #     extension, this sets its extension to its actual extension.
    #     """
    #     self._set_extension(ServoExtension.MIN_NO_BUZZ)
