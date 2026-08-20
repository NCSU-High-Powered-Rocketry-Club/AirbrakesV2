"""
Base class for the Servo.

This will serve as the base for real servo and the mock servo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from airbrakes.constants import ServoExtension


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
        """
        Extends the servo to deploy the airbrakes.
        """

    @abstractmethod
    def retract_airbrakes(self) -> None:
        """
        Retracts the servo to close the airbrakes.
        """

    @property
    @abstractmethod
    def servo_extension(self) -> ServoExtension:
        """
        Gets the extension most recently commanded to the servo.

        :return: The commanded servo extension.
        """

    @property
    @abstractmethod
    def battery_volts(self) -> float:
        """
        Gets the current battery voltage.

        :return: The current battery voltage in volts.
        """

    @property
    @abstractmethod
    def system_current_milliamps(self) -> float:
        """
        Gets the current system current draw.

        :return: The current system current draw in milliamps.
        """
