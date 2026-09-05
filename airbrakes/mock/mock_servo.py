"""
Module which contains the MockServo class and doesn't use the adafruit
circuitpython library.
"""

import threading

from airbrakes.base_classes.base_servo import BaseServo
from airbrakes.constants import (
    SERVO_DELAY_SECONDS,
    SERVO_MAX_ANGLE_DEGREES,
    SERVO_MAX_PULSE_WIDTH_US,
    SERVO_MIN_ANGLE_DEGREES,
    SERVO_MIN_PULSE_WIDTH_US,
    SERVO_OPERATING_FREQUENCY_HZ,
    ServoExtension,
)


class MockServo(BaseServo):
    """
    A custom class that represents a mock servo motor.
    """

    __slots__ = (
        "_current_angle",
        "_go_to_max_no_buzz",
        "_go_to_min_no_buzz",
        "_servo_extension",
        "duty_cycle",
    )

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
        self._servo_extension = ServoExtension.MIN_NO_BUZZ
        self.duty_cycle = 0.0
        self._go_to_max_no_buzz: threading.Timer | None = None
        self._go_to_min_no_buzz: threading.Timer | None = None
        self._current_angle = float(ServoExtension.MIN_NO_BUZZ.value)

    def start(self) -> None:
        """
        Starts the servo.
        """
        self.duty_cycle = float(ServoExtension.MIN_NO_BUZZ.value)

    def stop(self) -> None:
        """
        Stops the servo.
        """
        self._cancel_timer("_go_to_max_no_buzz")
        self._cancel_timer("_go_to_min_no_buzz")
        self.duty_cycle = 0.0

    def extend_airbrakes(self, velocity: float = 0.0) -> None:
        """
        Extends the servo to deploy the airbrakes (Mock).
        """
        _ = velocity
        self._cancel_timer("_go_to_min_no_buzz")
        self._set_extension(ServoExtension.MAX_EXTENSION)
        self._go_to_max_no_buzz = threading.Timer(
            SERVO_DELAY_SECONDS, self._set_extension, args=(ServoExtension.MAX_NO_BUZZ,)
        )
        self._go_to_max_no_buzz.start()

    def retract_airbrakes(self) -> None:
        """
        Retracts the servo to close the airbrakes (Mock).
        """
        self._cancel_timer("_go_to_max_no_buzz")
        self._set_extension(ServoExtension.MIN_EXTENSION)
        self._go_to_min_no_buzz = threading.Timer(
            SERVO_DELAY_SECONDS, self._set_extension, args=(ServoExtension.MIN_NO_BUZZ,)
        )
        self._go_to_min_no_buzz.start()

    def _set_extension(self, extension: ServoExtension) -> None:
        """Sets the simulated servo extension."""
        self._servo_extension = extension
        self._current_angle = float(extension.value)
        self.duty_cycle = self._angle_to_duty_cycle(extension.value)

    def _cancel_timer(self, timer_name: str) -> None:
        """Cancels the pending transition stored in the named timer slot."""
        timer = getattr(self, timer_name)
        if timer is not None:
            timer.cancel()

    @staticmethod
    def _angle_to_duty_cycle(angle: float) -> float:
        """Converts a servo angle to a PWM duty cycle percentage."""
        angle = max(SERVO_MIN_ANGLE_DEGREES, min(SERVO_MAX_ANGLE_DEGREES, angle))
        pulse_us = SERVO_MIN_PULSE_WIDTH_US + (
            (SERVO_MAX_PULSE_WIDTH_US - SERVO_MIN_PULSE_WIDTH_US)
            * (angle - SERVO_MIN_ANGLE_DEGREES)
            / (SERVO_MAX_ANGLE_DEGREES - SERVO_MIN_ANGLE_DEGREES)
        )
        return (pulse_us / (1_000_000 / SERVO_OPERATING_FREQUENCY_HZ)) * 100

    @property
    def servo_extension(self) -> ServoExtension:
        """
        Gets the extension most recently commanded to the mock servo.

        :return: The commanded servo extension.
        """
        return self._servo_extension

    @property
    def servo_angle(self) -> float:
        return self._current_angle

    @property
    def current_extension(self) -> ServoExtension:
        """Gets the extension most recently commanded to the mock servo."""
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
