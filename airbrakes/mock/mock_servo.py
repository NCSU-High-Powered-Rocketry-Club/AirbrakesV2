"""
Module which contains the MockServo class and doesn't use the adafruit
circuitpython library.
"""

from airbrakes.base_classes.base_servo import BaseServo
from airbrakes.constants import ServoExtension


class MockServo(BaseServo):
    """
    A custom class that represents a mock servo motor.
    """

    __slots__ = ("_servo_extension",)

    def __init__(
        self,
        servo_channel: int | None = None,
        encoder_pin_a: int | None = None,
        encoder_pin_b: int | None = None,
    ) -> None:
        """
        Initializes the mock servo object.

        :param servo_channel: The PWM channel for the servo
        :param encoder_pin_a: GPIO pin A for the encoder
        :param encoder_pin_b: GPIO pin B for the encoder.
        """
        _ = servo_channel, encoder_pin_a, encoder_pin_b
        self._servo_extension = ServoExtension.MIN_EXTENSION

    def start(self) -> None:
        """
        Starts the servo.
        """

    def stop(self) -> None:
        """
        Stops the servo.
        """

    def extend_airbrakes(self) -> None:
        """
        Extends the servo to deploy the airbrakes (Mock).
        """
        self._servo_extension = ServoExtension.MAX_EXTENSION

    def retract_airbrakes(self) -> None:
        """
        Retracts the servo to close the airbrakes (Mock).
        """
        self._servo_extension = ServoExtension.MIN_EXTENSION

    @property
    def servo_extension(self) -> ServoExtension:
        """
        Gets the extension most recently commanded to the mock servo.

        :return: The commanded servo extension.
        """
        return self._servo_extension

    @property
    def battery_volts(self) -> float:
        """
        Gets the current system voltage in volts. Since this is a mock servo,
        it always returns 0.

        :return: The current system voltage in volts.
        """
        return 0.0

    @property
    def system_current_milliamps(self) -> float:
        """
        Gets the current system current in milliamps. Since this is a mock
        servo, it always returns 0.

        :return: The current system current in milliamps.
        """
        return 0.0
