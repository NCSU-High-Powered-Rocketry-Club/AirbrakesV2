"""Module which contains the MockServo class and doesn't use the adafruit circuitpython library."""

from gpiozero import RotaryEncoder, Servo
from gpiozero.pins.mock import MockFactory, MockPWMPin

from airbrakes.constants import SERVO_MAX_ANGLE, ServoExtension
from airbrakes.interfaces.base_servo import BaseServo


class MockServo(BaseServo):
    """
    A custom class that represents a servo motor and the accompanying rotary encoder. The servo
    controls the extension of the airbrakes while the encoder measures the servo's position.
    the encoder is controlled using the gpiozero library, which provides a simple
    interface for controlling GPIO pins on the Raspberry Pi.

    The servo we use is the DS3235, which is a coreless digital servo.
    """

    __slots__ = ()

    def __init__(
        self,
        encoder_pin_number_a: int,
        encoder_pin_number_b: int,
    ) -> None:
        """
        Initializes the servo object with the specified GPIO pin.
        :param encoder_pin_number_a: The GPIO pin that the signal wire A of the encoder is
            connected to.
        :param encoder_pin_number_b: The GPIO pin that the signal wire B of the encoder is
            connected to.
        """
        # Setup the PCA9685 PWM servo driver. This contains the servos that control the airbrakes.

        # The servo controlling the airbrakes is connected to channel 0 and 3 of the PCA9685.
        # max_steps=0 indicates that the encoder's `value` property will never change. We will
        # only use the integer value, which is the `steps` property.
        encoder = RotaryEncoder(
            encoder_pin_number_a,
            encoder_pin_number_b,
            max_steps=0,
            pin_factory=MockFactory(pin_class=MockPWMPin),
        )
        first_servo = Servo(0, pin_factory=MockFactory(pin_class=MockPWMPin))
        second_servo = Servo(1, pin_factory=MockFactory(pin_class=MockPWMPin))

        super().__init__(first_servo, second_servo, encoder)

    @staticmethod
    def _scale_min_max(extension: float) -> float:
        """
        Scales the extension value to the range [0, 1] to set the servo value.
        :param extension: The extension to set the servo to.
        :return: The scaled extension value.
        """
        return extension / SERVO_MAX_ANGLE

    def _set_extension(self, extension: ServoExtension) -> None:
        """
        Sets the servo to the specified extension.
        :param extension: The extension to set the servo to.
        """
        super()._set_extension(extension)
        self.first_servo.value = MockServo._scale_min_max(extension.value)
        self.second_servo.value = MockServo._scale_min_max(extension.value)
