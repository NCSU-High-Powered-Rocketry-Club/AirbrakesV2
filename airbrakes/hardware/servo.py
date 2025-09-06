"""
Module which contains the Servo class, representing a servo motor that controls the extension of the
airbrakes, along with a rotary encoder to measure the servo's position.
"""

import gpiozero
from rpi_hardware_pwm import HardwarePWM

from airbrakes.constants import (
    SERVO_MAX_ANGLE_DEGREES,
    SERVO_MAX_PULSE_WIDTH_US,
    SERVO_MIN_ANGLE_DEGREES,
    SERVO_MIN_PULSE_WIDTH_US,
    SERVO_OPERATING_FREQUENCY_HZ,
    ServoExtension,
)
from airbrakes.interfaces.base_servo import BaseServo


class Servo(BaseServo):
    """
    A custom class that represents a servo motor and the accompanying rotary encoder. The servo
    controls the extension of the airbrakes while the encoder measures the servo's position. the
    encoder is controlled using the gpiozero library, which provides a simple interface for
    controlling GPIO pins on the Raspberry Pi 5.

    The servo we use is the DS3235, which is a coreless digital servo. We only use one servo to
    control the airbrakes, using hardware PWM on the Pi 5.
    """

    __slots__ = ()

    def __init__(
        self,
        first_servo_channel: int,
        second_servo_channel: int | None,
        encoder_pin_number_a: int,
        encoder_pin_number_b: int,
    ) -> None:
        """
        Initializes the Servo class.

        :param encoder_pin_number_a: The GPIO pin that the signal wire A of the encoder is connected
            to.
        :param encoder_pin_number_b: The GPIO pin that the signal wire B of the encoder is connected
            to.
        """
        first_servo = HardwarePWM(
            pwm_channel=first_servo_channel, hz=SERVO_OPERATING_FREQUENCY_HZ, chip=0
        )
        first_servo.start(self._angle_to_duty_cycle(ServoExtension.MIN_NO_BUZZ.value))

        second_servo = None
        if second_servo_channel is not None:
            # Did not test with two servos, but I think we need to keep them both at same Hz.
            second_servo = HardwarePWM(
                pwm_channel=second_servo_channel, hz=SERVO_OPERATING_FREQUENCY_HZ, chip=0
            )
            second_servo.start(self._angle_to_duty_cycle(ServoExtension.MIN_NO_BUZZ.value))

        # This library can only be imported on the raspberry pi. It's why the import is here.
        from gpiozero.pins.lgpio import LGPIOFactory as Factory  # noqa: PLC0415

        # max_steps=0 indicates that the encoder's `value` property will never change. We will
        # only use the integer value, which is the `steps` property.
        encoder = gpiozero.RotaryEncoder(
            encoder_pin_number_a, encoder_pin_number_b, max_steps=0, pin_factory=Factory()
        )

        super().__init__(encoder=encoder, first_servo=first_servo, second_servo=second_servo)

    @staticmethod
    def _angle_to_pulse_width(angle: float) -> float:
        """
        Converts an angle in degrees to a pulse width in microseconds for a servo motor.

        :param angle: The angle in degrees (0 to 180).
        :return: The corresponding pulse width in microseconds.
        """
        # Clamp the angle to the valid range:
        angle = max(SERVO_MIN_ANGLE_DEGREES, min(SERVO_MAX_ANGLE_DEGREES, angle))

        return SERVO_MIN_PULSE_WIDTH_US + (
            (SERVO_MAX_PULSE_WIDTH_US - SERVO_MIN_PULSE_WIDTH_US)
            * (angle - SERVO_MIN_ANGLE_DEGREES)
            / (SERVO_MAX_ANGLE_DEGREES - SERVO_MIN_ANGLE_DEGREES)
        )

    @staticmethod
    def _angle_to_duty_cycle(angle: float) -> float:
        """
        Converts an angle in degrees to a duty cycle percentage for a servo motor.

        :param angle: The angle in degrees.
        :return: The corresponding duty cycle percentage.
        """
        pulse_us = Servo._angle_to_pulse_width(angle)
        duty_cycle: float = (pulse_us / (1_000_000 / SERVO_OPERATING_FREQUENCY_HZ)) * 100
        return duty_cycle

    def _set_extension(self, extension: ServoExtension) -> None:
        """
        Sets the servo to the specified extension.

        :param extension: The extension to set the servo to.
        """
        super()._set_extension(extension)
        duty_cycle: float = self._angle_to_duty_cycle(extension.value)
        self.first_servo.change_duty_cycle(duty_cycle)
        if self.second_servo is not None:
            self.second_servo.change_duty_cycle(duty_cycle)
