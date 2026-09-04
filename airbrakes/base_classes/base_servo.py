"""Define the interface shared by real and simulated airbrake servos."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket


class BaseServo(ABC):
    """
    A custom class that represents a servo interface.
    The servo controls the extension of airbrakes.
    """

    __slots__ = ()

    @abstractmethod
    def start(self) -> None:
        """
        Starts the servo.
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Stops the servo.
        """

    @abstractmethod
    def extend_airbrakes(self) -> None:
        """Command the servo to its maximum extension."""

    @abstractmethod
    def retract_airbrakes(self) -> None:
        """Command the servo to its minimum extension."""

    @abstractmethod
    def set_extension(self, angle: float) -> None:
        """
        Command a specific airbrake extension in servo-position degrees.

        :param angle: The desired servo position.
        """

    @property
    @abstractmethod
    def is_powered(self) -> bool:
        """Return whether the servo is currently powered."""

    @property
    @abstractmethod
    def servo_extension(self) -> float:
        """Return the servo's current or most recently reported position."""

    @property
    @abstractmethod
    def battery_volts(self) -> float:
        """Return the supply voltage in volts."""

    @property
    @abstractmethod
    def system_current_milliamps(self) -> float:
        """Return the system current draw in milliamps."""

    @property
    @abstractmethod
    def servo_voltage(self) -> float:
        """Return the servo motor voltage in volts."""

    @property
    @abstractmethod
    def servo_temp(self) -> float:
        """Return the servo motor temperature in degrees Celsius."""

    @abstractmethod
    def get_servo_data_packet(self) -> ServoDataPacket:
        """Create a data packet containing the current servo telemetry."""
