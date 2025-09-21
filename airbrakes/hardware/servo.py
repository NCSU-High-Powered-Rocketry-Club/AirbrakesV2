"""
Module which contains the Servo class, representing a servo motor that controls the extension of the
airbrakes, along with a rotary encoder to measure the servo's position.
"""

import gpiozero
from rpi_hardware_pwm import HardwarePWM

from airbrakes.constants import (
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
        servo_channel: int,
        encoder_pin_number_a: int,
        encoder_pin_number_b: int,
    ) -> None:
        """
        Initializes the Servo class.

        :param servo_channel: The PWM channel that the servo is connected to.
        :param encoder_pin_number_a: The GPIO pin that the signal wire A of the encoder is connected
            to.
        :param encoder_pin_number_b: The GPIO pin that the signal wire B of the encoder is connected
            to.
        """
        servo = HardwarePWM(pwm_channel=servo_channel, hz=SERVO_OPERATING_FREQUENCY_HZ, chip=0)
        servo.start(self._angle_to_duty_cycle(ServoExtension.MIN_NO_BUZZ.value))

        # This library can only be imported on the raspberry pi. It's why the import is here.
        from gpiozero.pins.lgpio import LGPIOFactory as Factory  # noqa: PLC0415

        # max_steps=0 indicates that the encoder's `value` property will never change. We will
        # only use the integer value, which is the `steps` property.
        encoder = gpiozero.RotaryEncoder(
            encoder_pin_number_a, encoder_pin_number_b, max_steps=0, pin_factory=Factory()
        )

        super().__init__(encoder=encoder, servo=servo)

    def _set_extension(self, extension: ServoExtension) -> None:
        """
        Sets the servo to the specified extension.

        :param extension: The extension to set the servo to.
        """
        super()._set_extension(extension)
        duty_cycle: float = self._angle_to_duty_cycle(extension.value)
        self.servo.change_duty_cycle(duty_cycle)
