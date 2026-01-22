"""
Module which contains the MockServo class and doesn't use the adafruit circuitpython library.
"""

from gpiozero import RotaryEncoder
from gpiozero.pins.mock import MockFactory, MockPWMPin

from airbrakes.base_classes.base_servo import BaseServo
from airbrakes.constants import SERVO_OPERATING_FREQUENCY_HZ, ServoExtension


class MockServo(BaseServo):
    """
    A custom class that represents a servo motor and the accompanying rotary encoder. The servo
    controls the extension of the airbrakes while the encoder measures the servo's position. the
    encoder is controlled using the gpiozero library, which provides a simple interface for
    controlling GPIO pins on the Raspberry Pi.

    The servo we use is the DS3235, which is a coreless digital servo.
    """

    __slots__ = ()

    def __init__(
        self,
        servo_channel: int,
        encoder_pin_number_a: int,
        encoder_pin_number_b: int,
    ) -> None:
        """
        Initializes the servo object with the specified GPIO pin.

        :param encoder_pin_number_a: The GPIO pin that the signal wire A of the encoder is connected
            to.
        :param encoder_pin_number_b: The GPIO pin that the signal wire B of the encoder is connected
            to.
        """
        factory = MockFactory(pin_class=MockPWMPin)

        # max_steps=0 indicates that the encoder's `value` property will never change. We will
        # only use the integer value, which is the `steps` property.
        encoder = RotaryEncoder(
            encoder_pin_number_a,
            encoder_pin_number_b,
            max_steps=0,
            pin_factory=factory,
        )

        servo = MockHardwarePWM(servo_channel, hz=SERVO_OPERATING_FREQUENCY_HZ, chip=0)

        super().__init__(encoder=encoder, servo=servo)

    def _set_extension(self, extension: ServoExtension) -> None:
        """
        Sets the servo to the specified extension.

        :param extension: The extension to set the servo to.
        """
        super()._set_extension(extension)
        duty_cycle: float = self._angle_to_duty_cycle(extension.value)
        self.servo.change_duty_cycle(duty_cycle)


class MockHardwarePWM:
    """
    A mock class that simulates the rpi_hardware_pwm.HardwarePWM class.
    """

    __slots__ = ("chip", "duty_cycle", "hz", "pwm_channel")

    def __init__(self, pwm_channel: int, hz: int, chip: int) -> None:
        """
        Initializes the mock HardwarePWM object.

        :param pwm_channel: The PWM channel to use.
        :param hz: The frequency to use.
        :param chip: The chip to use.
        """
        self.pwm_channel: int = pwm_channel
        self.hz: int = hz
        self.chip: int = chip
        self.duty_cycle: float = 0.0

    def change_duty_cycle(self, duty_cycle: float) -> None:
        """
        Changes the duty cycle of the PWM signal.

        :param duty_cycle: The new duty cycle to use.
        """
        self.duty_cycle = duty_cycle
