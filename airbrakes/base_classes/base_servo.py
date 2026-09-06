"""Define the interface shared by real and simulated airbrake servos."""

from __future__ import annotations

from abc import ABC, abstractmethod
from math import isfinite
from typing import TYPE_CHECKING

import numpy as np

from airbrakes.constants import (
    AIR_DENSITY_KG_PER_M3,
    AIRBRAKE_DRAG_COEFFICIENT,
    AIRBRAKE_EXTENSIONS,
    AIRBRAKE_SURFACE_AREAS_IN2,
    MAX_AIRBRAKE_FORCE_LBS,
    SERVO_MAX_EXTENSION,
    SERVO_MIN_EXTENSION,
)
from airbrakes.utils import convert_lbf_to_newtons, convert_square_meters_to_square_inches

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
    def extend_airbrakes(self, velocity: float) -> None:
        """Command the servo to the maximum safe extension for ``velocity``."""

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
        """Return whether the servo is currently powered and attempting to hold its position."""

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

    def _calculate_deployment_extension(self, velocity_meters_per_s: float) -> float:
        """
        Return the largest safe extension fraction for a rocket speed.

        :param velocity_meters_per_s: The rocket's current speed in meters per second.
        :return: The largest safe extension fraction, between 0.0 and 1.
        """
        speed = abs(velocity_meters_per_s)
        if not isfinite(speed):
            return 0.0
        if speed == 0:
            return 1.0

        max_force_newtons = convert_lbf_to_newtons(MAX_AIRBRAKE_FORCE_LBS)
        max_area_m2 = (
            2 * max_force_newtons / (AIR_DENSITY_KG_PER_M3 * speed**2 * AIRBRAKE_DRAG_COEFFICIENT)
        )
        max_area_in2 = convert_square_meters_to_square_inches(max_area_m2)
        return float(
            np.interp(
                max_area_in2,
                AIRBRAKE_SURFACE_AREAS_IN2,
                AIRBRAKE_EXTENSIONS,
            )
        )

    def _deployment_extension_to_angle(self, extension: float) -> float:
        """Convert a normalized airbrake extension into a servo angle in degrees."""
        if not isfinite(extension):
            return float(SERVO_MIN_EXTENSION)
        bounded_extension = min(max(extension, 0.0), 1.0)
        return SERVO_MIN_EXTENSION + bounded_extension * (SERVO_MAX_EXTENSION - SERVO_MIN_EXTENSION)
