"""
Module which contains the Servo class, representing a servo motor that controls the extension of the
airbrakes, along with a rotary encoder to measure the servo's position.
"""
from typing import TYPE_CHECKING

from airbrakes.base_classes.base_servo import BaseServo

from airbrakes.constants import (
    ServoExtension,
    SERVO_EXTENSION_TIME,
    SERVO_PORT,
    SERVO_ID,
)

from lewanlib.bus import ServoBus
from lewanlib.servo import Servo

class LewanServo(BaseServo):
    """
    A custom class that represents a servo motor and the accompanying rotary encoder. The servo
    controls the extension of the airbrakes while the encoder measures the servo's position. the
    encoder is controlled using the gpiozero library, which provides a simple interface for
    controlling GPIO pins on the Raspberry Pi 5.

    The servo we use is the DS3235, which is a coreless digital servo. We only use one servo to
    control the airbrakes, using hardware PWM on the Pi 5.
    """

    __slots__ = (
        "_current_extension",
        "bus",
        "servo",
    )

    def __init__(self) -> None:
        """
        Initializes the Servo class.

        """
        super().__init__()
        self._current_extension: ServoExtension
        self.bus = ServoBus(port=SERVO_PORT)
        self.servo = Servo(SERVO_ID, self.bus)
        self.servo.move_time_write(ServoExtension.MIN_EXTENSION, SERVO_EXTENSION_TIME)


    def set_max_extension(self) -> None:
        """
        Sets the servo to the maximum extension.
        """
        self.servo.move_time_write(ServoExtension.MAX_EXTENSION, SERVO_EXTENSION_TIME)

    def set_min_extension(self) -> None:
        """
        Retracts the servo to the minimum extension.
        """
        self.servo.move_time_write(ServoExtension.MIN_EXTENSION, SERVO_EXTENSION_TIME)

    @property
    def current_extension(self) -> ServoExtension:
        """
        The servo's current extension.
        """
        return self._current_extension



