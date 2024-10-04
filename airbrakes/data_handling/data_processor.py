"""Module for processing IMU data on a higher level."""

from collections import deque
from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from airbrakes.utils import deadband
from constants import ACCELERATION_NOISE_THRESHOLD


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
        "_current_altitudes",
        "_data_points",
        "_initial_altitude",
        "_last_data_point",
        "_max_altitude",
        "_max_speed",
        "_previous_velocity",
        "_speeds",
        "upside_down",
    )

    def __init__(self, data_points: Sequence[EstimatedDataPacket], upside_down: bool = False):
        self._avg_accel: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._avg_accel_mag: float = 0.0
        self._max_altitude: float = 0.0
        self._speeds: list[float] = [0.0]
        self._max_speed: float = 0.0
        self._previous_velocity: tuple[np.float64, np.float64, np.float64] = (
            np.float64(0.0), np.float64(0.0), np.float64(0.0))
        self._initial_altitude: np.float64 | None = None
        self._current_altitudes: npt.NDArray[np.float64] = np.array([0.0])
        self.upside_down = upside_down
        self._last_data_point = EstimatedDataPacket(0.0)  # Placeholder for the last data point

        self._data_points: Sequence[EstimatedDataPacket]

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
        return tuple(self._avg_accel)

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
        """Returns the altitudes of the rocket (zeroed out) from the data points, in meters."""
        return self._current_altitudes[-1]

    @property
    def speed(self) -> float:
        """The current speed of the rocket in m/s. Calculated by integrating the linear acceleration."""
        return self._speeds[-1]

    @property
    def max_speed(self) -> float:
        """The maximum speed the rocket has attained during the flight, in m/s."""
        return self._max_speed

    def update_data(self, data_points: Sequence[EstimatedDataPacket]) -> None:
        """
        Updates the data points to process. This will recompute all the averages and other
        information such as altitude, speed, etc.
        :param data_points: A sequence of EstimatedDataPacket objects to process
        """

        # If the data points are empty, we don't want to try to process anything
        if not data_points:
            return

        self._data_points = data_points

        # We use linearAcceleration because we don't want gravity to affect our calculations for
        # speed.
        # Next, assign variables for linear acceleration, since we don't want to recalculate them
        # in the helper functions below:
        # List of the acceleration in the x, y, and z directions, useful for calculations below
        # If the absolute value of acceleration is less than 0.1, set it to 0
        x_accel, y_accel, z_accel, pressure_altitudes = deque(), deque(), deque(), deque()
        for data_point in self._data_points:
            x_accel.append(deadband(data_point.estLinearAccelX, ACCELERATION_NOISE_THRESHOLD))
            y_accel.append(deadband(data_point.estLinearAccelY, ACCELERATION_NOISE_THRESHOLD))
            z_accel.append(deadband(data_point.estLinearAccelZ, ACCELERATION_NOISE_THRESHOLD))
            pressure_altitudes.append(data_point.estPressureAlt)

        a_x, a_y, a_z = self._compute_averages(x_accel, y_accel, z_accel)
        self._avg_accel = (a_x, a_y, a_z)
        self._avg_accel_mag = (a_x ** 2 + a_y ** 2 + a_z ** 2) ** 0.5

        self._speeds: np.array[np.float64] = self._calculate_speeds(x_accel, y_accel, z_accel)
        self._max_speed = max(self._speeds.max(), self._max_speed)

        # Zero the altitude only once, during the first update:
        if self._initial_altitude is None:
            self._initial_altitude = np.mean(pressure_altitudes)

        self._current_altitudes = self._calculate_current_altitudes(pressure_altitudes)
        self._max_altitude = self._calculate_max_altitude(pressure_altitudes)

        # Store the last data point for the next update
        self._last_data_point = data_points[-1]

    def get_processed_data(self) -> list[ProcessedDataPacket]:
        """
        Processes the data points and returns a list of ProcessedDataPacket objects. The length
        of the list should be the same as the length of list of the estimated data packets most
        recently passed in by update_data()

        :return: A list of ProcessedDataPacket objects.
        """
        # The lengths of speeds, current altitudes, and data points should be the same, so it
        # makes a ProcessedDataPacket for EstimatedDataPacket
        return [
            ProcessedDataPacket(
                avg_acceleration=self.avg_acceleration,
                current_altitude=current_alt,
                speed=speed,
                estimated_data_packet=est_data_packet,
            )
            for current_alt, speed, est_data_packet in zip(
                self._current_altitudes, self._speeds, self._data_points, strict=False
            )
        ]

    def _calculate_max_altitude(self, pressure_alt: Sequence[float]) -> float:
        """
        Calculates the maximum altitude (zeroed out) of the rocket based on the pressure
        altitude during the flight.

        :return: The maximum altitude of the rocket in meters.
        """
        zeroed_alts = np.array(pressure_alt) - self._initial_altitude
        return max(zeroed_alts.max(), self._max_altitude)

    def _calculate_current_altitudes(self, alt_list: Sequence[float]) -> npt.NDArray[np.float64]:
        """
        Calculates the current altitudes, by zeroing out the initial altitude.

        :param alt_list: A list of the altitude data points.
        """
        # There is a decent chance that the zeroed out altitude is negative, e.g. if the rocket
        # landed at a height below from where it launched from, but that doesn't concern us.
        return np.array(alt_list) - self._initial_altitude

    def _compute_averages(self, a_x: list[float], a_y: list[float], a_z: list[float]) -> tuple[float, float, float]:
        """
        Calculates the average acceleration and acceleration magnitude of the data points.

        :param a_x: A list of the accelerations in the x direction.
        :param a_y: A list of the accelerations in the y direction.
        :param a_z: A list of the accelerations in the z direction.

        :return: A numpy array of the average acceleration in the x, y, and z directions.
        """
        # calculate the average acceleration in the x, y, and z directions
        return float(np.mean(a_x)), float(np.mean(a_y)), float(np.mean(a_z))

    def _calculate_speeds(self, a_x: list[float], a_y: list[float], a_z: list[float]) -> npt.NDArray[np.float64]:
        """
        Calculates the speed of the rocket based on the linear acceleration.
        Integrates the linear acceleration to get the speed.
        """
        # We need at least two data points to calculate the speed:
        if len(self._data_points) < 1:
            return np.array([0.0])

        # Prevent subtle bug in at init, when we only process one data packet, and the
        # last_data_point is a dummy set in __init__.
        if self._last_data_point.timestamp == 0.0:
            return np.array([0.0] * len(self._data_points))

        # Side note: We can't use the pressure altitude to calculate the speed, since the pressure
        # does not update fast enough to give us a good estimate of the speed.

        # calculate the time differences between each data point
        # We are converting from ns to s, since we don't want to have a speed in m/ns^2
        # We are using the last data point to calculate the time difference between the last data point from the
        # previous loop, and the first data point from the current loop
        time_diff = np.diff([data_point.timestamp for data_point in [self._last_data_point, *self._data_points]]) * 1e-9

        # We store the previous calculated velocity vectors, so that our speed
        # doesn't show a jump, e.g. after motor burn out.
        previous_vel_x, previous_vel_y, previous_vel_z = self._previous_velocity

        # We integrate each of the components of the acceleration to get the velocity
        # The [:-1] is used to remove the last element of the list, since we have one less time
        # difference than we have acceleration values.
        velocities_x: np.array = previous_vel_x + np.cumsum(np.array(a_x) * time_diff)
        velocities_y: np.array = previous_vel_y + np.cumsum(np.array(a_y) * time_diff)
        velocities_z: np.array = previous_vel_z + np.cumsum(np.array(a_z) * time_diff)

        # Store the last calculated velocity vectors
        self._previous_velocity = (velocities_x[-1], velocities_y[-1], velocities_z[-1])

        # All the speeds gotten as the magnitude of the velocity vector at each point
        return np.sqrt(velocities_x ** 2 + velocities_y ** 2 + velocities_z ** 2)
