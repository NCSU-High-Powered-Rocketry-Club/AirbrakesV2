"""Module which contains the Servo class, representing a servo motor that controls the extension of
the airbrakes, along with a rotary encoder to measure the servo's position."""

import contextlib

import gpiozero

# This import fails on non raspberry pi devices running arm architecture
with contextlib.suppress(AttributeError):
    from adafruit_servokit import ServoKit

from airbrakes.constants import (
    SERVO_MAX_ANGLE,
    SERVO_MAX_PULSE_WIDTH,
    SERVO_MIN_PULSE_WIDTH,
    ServoExtension,
)
from airbrakes.interfaces.base_servo import BaseServo


class Servo(BaseServo):
    """
    A custom class that represents a servo motor and the accompanying rotary encoder. The servo
    controls the extension of the airbrakes while the encoder measures the servo's position.
    the encoder is controlled using the gpiozero library, which provides a simple
    interface for controlling GPIO pins on the Raspberry Pi 5.

    The servo we use is the DS3235, which is a coreless digital servo. There are two of these on
    the Servo Bonnet (https://www.adafruit.com/product/3416), which is connected to the Pi 5.
    """

    __slots__ = ()

    def __init__(
        self,
        first_servo_channel: int,
        second_servo_channel: int,
        encoder_pin_number_a: int,
        encoder_pin_number_b: int,
    ) -> None:
        """
        :param first_servo_channel: The channel where the first servo is connected to on the board
        :param second_servo_channel: The channel where the second servo is connected to on the board
        :param encoder_pin_number_a: The GPIO pin that the signal wire A of the encoder is
        connected to.
        :param encoder_pin_number_b: The GPIO pin that the signal wire B of the encoder is
        connected to.
        """

        # Set up the Bonnet servo kit. This contains the servos that control the airbrakes.
        pca_9685 = ServoKit(channels=16)
        # The servo controlling the airbrakes is connected to channel 0 and 3 of the PCA9685.
        servo_1 = pca_9685.servo[first_servo_channel]
        servo_2 = pca_9685.servo[second_servo_channel]

        servo_1.set_pulse_width_range(SERVO_MIN_PULSE_WIDTH, SERVO_MAX_PULSE_WIDTH)
        servo_2.set_pulse_width_range(SERVO_MIN_PULSE_WIDTH, SERVO_MAX_PULSE_WIDTH)
        servo_1.actuation_range = SERVO_MAX_ANGLE
        servo_2.actuation_range = SERVO_MAX_ANGLE

        # This library can only be imported on the raspberry pi. It's why the import is here.
        from gpiozero.pins.lgpio import LGPIOFactory as Factory

        # max_steps=0 indicates that the encoder's `value` property will never change. We will
        # only use the integer value, which is the `steps` property.
        encoder = gpiozero.RotaryEncoder(
            encoder_pin_number_a, encoder_pin_number_b, max_steps=0, pin_factory=Factory()
        )

        super().__init__(servo_1, servo_2, encoder)

    def _set_extension(self, extension: ServoExtension) -> None:
        """
        Sets the servo to the specified extension.
        :param extension: The extension to set the servo to.
        """
        super()._set_extension(extension)
        self.first_servo.angle = extension.value
        self.second_servo.angle = extension.value
