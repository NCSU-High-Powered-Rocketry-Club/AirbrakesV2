"""Module for processing IMU data on a higher level."""

from collections import deque
from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from constants import ACCELERATION_NOISE_THRESHOLD
from utils import deadband


class IMUDataProcessor:
    """
    Performs high level calculations on the data packets received from the IMU. Includes
    calculation the rolling averages of acceleration, maximum altitude so far, etc., from the set of
    data points.

    :param data_points: A sequence of EstimatedDataPacket objects to process.
    """

    __slots__ = (
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
        self._max_altitude: float = 0.0
        self._speeds: list[float] = [0.0]
        self._max_speed: float = 0.0
        self._previous_velocity: npt.NDArray[np.float64] = np.array([0.0, 0.0, 0.0])
        self._initial_altitude: np.float64 | None = None
        self._current_altitudes: npt.NDArray[np.float64] = np.array([0.0])
        self.upside_down = upside_down
        self._last_data_point: EstimatedDataPacket | None = None

        self._data_points: Sequence[EstimatedDataPacket]

        if data_points:  # actually update the data on init
            self.update_data(data_points)
        else:
            self._data_points: Sequence[EstimatedDataPacket] = data_points

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"max_altitude={self.max_altitude}, "
            f"current_altitude={self.current_altitude}, "
            f"speed={self.speed}, "
            f"max_speed={self.max_speed})"
        )

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
        # If the absolute value of acceleration is less than our threshold, set it to 0
        x_accel, y_accel, z_accel, pressure_altitudes = deque(), deque(), deque(), deque()
        for data_point in self._data_points:
            x_accel.append(deadband(data_point.estLinearAccelX, ACCELERATION_NOISE_THRESHOLD))
            y_accel.append(deadband(data_point.estLinearAccelY, ACCELERATION_NOISE_THRESHOLD))
            z_accel.append(deadband(data_point.estLinearAccelZ, ACCELERATION_NOISE_THRESHOLD))
            pressure_altitudes.append(data_point.estPressureAlt)

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
                current_altitude=current_alt,
                speed=speed,
            )
            for current_alt, speed in zip(self._current_altitudes, self._speeds, strict=False)
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

    def _calculate_speeds(self, a_x: list[float], a_y: list[float], a_z: list[float]) -> npt.NDArray[np.float64]:
        """
        Calculates the speed of the rocket based on the linear acceleration.
        Integrates the linear acceleration to get the speed.
        """
        # We need at least two data points to calculate the speed:
        if not self._data_points:  # We use the last_data_point, hence even a single data point works.
            return np.array([0.0])

        # Deliberately discard all our data packets for speed calc if we don't have a
        # last_data_point. This will only happen during startup. It does not make sense to
        # set last_data_point as the first element of data_points during initialization, as we will
        # then have one less data point to calculate the time difference between the last data point
        # leading to get_processed_data to have a different length than the data_points.
        if self._last_data_point is None:
            return np.array([0.0] * len(self._data_points))

        # At this point, our last_data_point is guaranteed to be an EstimatedDataPacket.
        self._last_data_point: EstimatedDataPacket

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
        return np.sqrt(velocities_x**2 + velocities_y**2 + velocities_z**2)
