"""Module for processing IMU data on a higher level."""

from collections.abc import Sequence

import numpy as np

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket
from airbrakes.utils import deadband
from constants import ACCLERATION_NOISE_THRESHOLD


class IMUDataProcessor:
    """
    Performs high level calculations on the data packets received from the IMU. Includes
    calculation the rolling averages of acceleration, maximum altitude so far, etc., from the set of
    data points.

    :param data_points: A sequence of EstimatedDataPacket objects to process.
    """

    __slots__ = (
        "_avg_accel",
        "_avg_accel_mag",
        "_current_altitude",
        "_data_points",
        "_initial_altitude",
        "_max_altitude",
        "_max_speed",
        "_old_data_points",
        "_previous_velocity",
        "_speed",
        "upside_down",
    )

    def __init__(self, data_points: Sequence[EstimatedDataPacket], upside_down: bool = False):
        self._avg_accel: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._avg_accel_mag: float = 0.0
        self._max_altitude: float = 0.0
        self._speed: float = 0.0
        self._max_speed: float = 0.0
        self._previous_velocity: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._initial_altitude: float | None = None
        self._current_altitude: float = 0.0
        self.upside_down = upside_down

        self._data_points: Sequence[EstimatedDataPacket]
        self._old_data_points = []

        if data_points:  # actually update the data on init
            self.update_data(data_points)
        else:
            self._data_points: Sequence[EstimatedDataPacket] = data_points

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"avg_acceleration={self.avg_acceleration}, "
            f"avg_acceleration_mag={self.avg_acceleration_mag}, "
            f"max_altitude={self.max_altitude}, "
            f"current_altitude={self.current_altitude}, "
            f"speed={self.speed}, "
            f"max_speed={self.max_speed})"
        )

    @property
    def avg_acceleration_z(self) -> float:
        """
        Returns the average acceleration in the z direction of the data points, in m/s^2.
        """
        return self._avg_accel[-1]

    @property
    def avg_acceleration(self) -> tuple[float, float, float]:
        """
        Returns the averaged acceleration as a vector of the data points, in m/s^2.
        """
        return self._avg_accel

    @property
    def avg_acceleration_mag(self) -> float:
        """
        Returns the magnitude of the acceleration vector of the data points, in m/s^2.
        """
        return self._avg_accel_mag

    @property
    def max_altitude(self) -> float:
        """
        Returns the highest altitude (zeroed out) attained by the rocket for the entire flight
        so far, in meters.
        """
        return self._max_altitude

    @property
    def current_altitude(self) -> float:
        """Returns the altitude of the rocket (zeroed out) from the data points, in meters."""
        return self._current_altitude

    @property
    def speed(self) -> float:
        """The current speed of the rocket in m/s. Calculated by integrating the linear acceleration."""
        return self._speed

    @property
    def max_speed(self) -> float:
        """The maximum speed the rocket has attained during the flight, in m/s."""
        return self._max_speed

    def update_data(self, data_points: Sequence[EstimatedDataPacket]) -> None:
        """
        Updates the data points to process. This will recompute all the averages and other
        information such as altitude, speed, etc.
        :param data_points: A sequence of EstimatedDataPacket objects to process.
        """

        if len(data_points) + len(self._old_data_points) < 2:
            self._old_data_points.extend(data_points)
            return

        # First assign the data points
        self._data_points = self._old_data_points + list(data_points)
        self._old_data_points = []  # Clear old data points after updating

        # We use linearAcceleration because we don't want gravity to affect our calculations for
        # speed.
        # Next, assign variables for linear acceleration, since we don't want to recalculate them
        # in the helper functions below:
        # List of the acceleration in the x, y, and z directions, useful for calculations below
        # If the absolute value of acceleration is less than 0.1, set it to 0
        x_accel = [
            deadband(data_point.estLinearAccelX, ACCLERATION_NOISE_THRESHOLD) for data_point in self._data_points
        ]
        y_accel = [
            deadband(data_point.estLinearAccelY, ACCLERATION_NOISE_THRESHOLD) for data_point in self._data_points
        ]
        z_accel = [
            deadband(data_point.estLinearAccelZ, ACCLERATION_NOISE_THRESHOLD) for data_point in self._data_points
        ]

        pressure_altitude = [data_point.estPressureAlt for data_point in self._data_points]

        a_x, a_y, a_z = self._compute_averages(x_accel, y_accel, z_accel)
        self._avg_accel = (a_x, a_y, a_z)
        self._avg_accel_mag = (self._avg_accel[0] ** 2 + self._avg_accel[1] ** 2 + self._avg_accel[2] ** 2) ** 0.5

        self._speed = self._calculate_speed(x_accel, y_accel, z_accel)

        if self._speed != 0.0:
            print(self._speed)

        self._max_speed = max(self._speed, self._max_speed)

        # Zero the altitude only once, during the first update:
        if self._initial_altitude is None:
            self._initial_altitude = np.mean(pressure_altitude)

        self._current_altitude = self._calculate_current_altitude(pressure_altitude)
        self._max_altitude = self._calculate_max_altitude(pressure_altitude)

    def _calculate_max_altitude(self, pressure_alt: list[float]) -> float:
        """
        Calculates the maximum altitude (zeroed out) of the rocket based on the pressure
        altitude during the flight.

        :return: The maximum altitude of the rocket in meters.
        """
        zeroed_alts = np.array(pressure_alt) - self._initial_altitude
        return max(*zeroed_alts, self._max_altitude)

    def _calculate_current_altitude(self, alt_list: list[float]) -> float:
        """
        Calculates the current altitude, by zeroing out the latest altitude data point.

        :param alt_list: A list of the altitude data points.
        """
        # There is a decent chance that the zeroed out altitude is negative, e.g. if the rocket
        # landed at a height below from where it launched from, but that doesn't concern us.
        return alt_list[-1] - self._initial_altitude

    def _compute_averages(self, a_x: list[float], a_y: list[float], a_z: list[float]) -> tuple[float, float, float]:
        """
        Calculates the average acceleration and acceleration magnitude of the data points.

        :param a_x: A list of the accelerations in the x direction.
        :param a_y: A list of the accelerations in the y direction.
        :param a_z: A list of the accelerations in the z direction.

        :return: A tuple of the average acceleration in the x, y, and z directions.
        """
        # calculate the average acceleration in the x, y, and z directions
        avg_x_accel = np.mean(a_x)
        avg_y_accel = np.mean(a_y)
        avg_z_accel = np.mean(a_z)
        return avg_x_accel, avg_y_accel, avg_z_accel

    def _calculate_speed(self, a_x: list[float], a_y: list[float], a_z: list[float]) -> float:
        """
        Calculates the speed of the rocket based on the linear acceleration.
        Integrates the linear acceleration to get the speed.
        """
        previous_vel_x, previous_vel_y, previous_vel_z = self._previous_velocity
        # We need at least two data points to calculate the speed:
        if len(self._data_points) < 2:
            return np.sqrt(previous_vel_x**2 + previous_vel_y**2 + previous_vel_z**2)

        # Side note: We can't use the pressure altitude to calculate the speed, since the pressure
        # does not update fast enough to give us a good estimate of the speed.

        # calculate the time differences between each data point
        # We are converting from ns to s, since we don't want to have a speed in m/ns^2
        time_diff = np.diff([data_point.timestamp for data_point in self._data_points]) * 1e-9

        # We store the previous calculated velocity vectors, so that our speed
        # doesn't show a jump, e.g. after motor burn out.
        previous_vel_x, previous_vel_y, previous_vel_z = self._previous_velocity

        # We integrate each of the components of the acceleration to get the velocity
        # The [:-1] is used to remove the last element of the list, since we have one less time
        # difference than we have acceleration values.
        velocity_x: np.array = previous_vel_x + np.cumsum(np.array(a_x) * time_diff[0])
        velocity_y: np.array = previous_vel_y + np.cumsum(np.array(a_y) * time_diff[0])
        velocity_z: np.array = previous_vel_z + np.cumsum(np.array(a_z) * time_diff[0])

        # Store the last calculated velocity vectors
        self._previous_velocity = (velocity_x[-1], velocity_y[-1], velocity_z[-1])

        # The speed is the magnitude of the velocity vector
        # [-1] to get the last element of the array (latest speed)
        return np.sqrt(velocity_x**2 + velocity_y**2 + velocity_z**2)[-1]
