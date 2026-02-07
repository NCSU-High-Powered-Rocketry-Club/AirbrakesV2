"""
Base class for the Servo.

This will serve as the base for real servo and the mock servo.
"""

import threading
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from airbrakes.constants import (
    SERVO_DELAY_SECONDS,
    SERVO_MAX_ANGLE_DEGREES,
    SERVO_MAX_PULSE_WIDTH_US,
    SERVO_MIN_ANGLE_DEGREES,
    SERVO_MIN_PULSE_WIDTH_US,
    SERVO_OPERATING_FREQUENCY_HZ,
    ServoExtension,
)

if TYPE_CHECKING:
    import gpiozero
    from rpi_hardware_pwm import HardwarePWM

    from airbrakes.mock.mock_servo import MockHardwarePWM


class BaseServo(ABC):
    """
    A custom class that represents a servo interface and the accompanying rotary encoder interface.
    The servo controls the extension of the airbrakes while the encoder measures the servo's
    position. The encoder is controlled using the gpiozero library, which provides a simple
    interface for controlling GPIO pins on the Raspberry Pi.

    The servo we use is the DS3235, which is a coreless digital servo. We use hardware PWM to
    control the servo on the Pi 5. We can't use the gpiozero Servo class because it uses software
    PWM, which causes too much jitter (more specifically, the PiGPIO library does not support the Pi
    5, which is why it falls back to software PWM).
    """

    __slots__ = (
        "_go_to_max_no_buzz",
        "_go_to_min_no_buzz",
        "current_extension",
        "encoder",
        "servo",
    )

    def __init__(
        self,
        encoder: gpiozero.RotaryEncoder,
        servo: HardwarePWM | MockHardwarePWM,
    ) -> None:
        """
        Initializes the servo and the encoder.

        :param servo: The servo object. Can be a real servo or a mock servo.
        :param encoder: The rotary encoder object.
        """
        self.current_extension: ServoExtension = ServoExtension.MIN_NO_BUZZ

        self.servo: HardwarePWM | MockHardwarePWM = servo

        self.encoder = encoder

        # We have to use threading to avoid blocking the main thread because our extension methods
        # need to run at a specific time. Yes this is bad practice but we had a mechanical issue and
        # we had to fix it in code.
        self._go_to_max_no_buzz = threading.Timer(SERVO_DELAY_SECONDS, self._set_max_no_buzz)
        self._go_to_min_no_buzz = threading.Timer(SERVO_DELAY_SECONDS, self._set_min_no_buzz)

    @abstractmethod
    def _set_extension(self, extension: ServoExtension) -> None:
        """
        Sets the extension of the servo.

        :param extension: The extension of the servo, there are 4 possible values, see constants.
        """
        self.current_extension = extension

    @staticmethod
    def _angle_to_pulse_width(angle: float) -> float:
        """
        Converts an angle in degrees to a pulse width in microseconds for a servo motor.

        :param angle: The angle in degrees (0 to 180).
        :return: The corresponding pulse width in microseconds.
        """
        # Clamp the angle to the valid range:
        angle = max(SERVO_MIN_ANGLE_DEGREES, min(SERVO_MAX_ANGLE_DEGREES, angle))

        # Servos are controlled by sending PWM signals, where the width of the "high" pulse
        # (in microseconds) tells the servo what angle to move to. Each servo has a minimum and
        # maximum pulse width - these values correspond to its minimum and maximum rotation angles.

        # So we use linear interpolation to convert the angle to a pulse width:

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
        pulse_us = BaseServo._angle_to_pulse_width(angle)

        # Duty cycle is simply the percentage of time that the signal is "high" in one period of
        # the PWM signal. We convert the servo operating frequency from Hz to period in
        # microseconds (1_000_000 / frequency) and then multiply by 100 to get a percentage.

        duty_cycle: float = (pulse_us / (1_000_000 / SERVO_OPERATING_FREQUENCY_HZ)) * 100
        return duty_cycle

    def set_extended(self) -> None:
        """
        Extends the servo to the maximum extension.

        Starts a timer to stop the buzzing after the servo reaches the maximum extension.
        """
        # If we are already going to the minimum extension, we cancel that operation before
        # extending the servo.
        self._go_to_min_no_buzz.cancel()

        self._set_extension(ServoExtension.MAX_EXTENSION)

        # Creates a timer to stop the buzzing after the servo reaches the maximum extension.
        self._go_to_max_no_buzz = threading.Timer(SERVO_DELAY_SECONDS, self._set_max_no_buzz)
        self._go_to_max_no_buzz.start()

    def set_retracted(self) -> None:
        """
        Retracts the servo to the minimum extension.

        Starts a timer to stop the buzzing after the servo reaches the minimum extension.
        """
        # If we are already going to the maximum extension, we cancel that operation before
        # retracting the servo.
        self._go_to_max_no_buzz.cancel()

        self._set_extension(ServoExtension.MIN_EXTENSION)

        # Creates a timer to stop the buzzing after the servo reaches the minimum extension
        self._go_to_min_no_buzz = threading.Timer(SERVO_DELAY_SECONDS, self._set_min_no_buzz)
        self._go_to_min_no_buzz.start()

    def get_encoder_reading(self) -> int:
        """
        Gets the current reading (in steps) of the rotary encoder.

        :return: The current reading of the rotary encoder
        """
        return self.encoder.steps

    def _set_max_no_buzz(self) -> None:
        """
        Extends the servo to the stop buzz position.

        After the servo is extended to its maximum extension, this sets its extension to its actual
        extension.
        """
        self._set_extension(ServoExtension.MAX_NO_BUZZ)

    def _set_min_no_buzz(self) -> None:
        """
        Retracts the servo to the stop buzz position.

        After the servo is retracted to its minimum extension, this sets its extension to its actual
        extension.
        """
        self._set_extension(ServoExtension.MIN_NO_BUZZ)
