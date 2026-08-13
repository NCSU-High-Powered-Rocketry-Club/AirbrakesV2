"""
Base class for the Servo.

This will serve as the base for real servo and the mock servo.
"""

from abc import ABC, abstractmethod


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

    @abstractmethod
    def get_battery_volts(self) -> float:
        """
        Gets the current battery voltage.

        :return: The current battery voltage in volts.
        """

    @abstractmethod
    def get_system_current_milliamps(self) -> float:
        """
        Gets the current system current draw.

        :return: The current system current draw in milliamps.
        """
